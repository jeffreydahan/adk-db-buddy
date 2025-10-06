import os
import logging
import pandas as pd
import psycopg2
import subprocess
import time
from io import StringIO
from psycopg2 import Error as Psycopg2Error
from psycopg2.extras import execute_values
from dotenv import load_dotenv
import pymssql
import argparse
import os
import signal # Needed for os.killpg

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Helper for memory-safe data loading ---
def get_csv_dtypes(csv_file_path, sample_rows=1000):
    """Reads a small sample of the CSV to infer optimal, memory-efficient dtypes."""
    try:
        temp_df = pd.read_csv(csv_file_path, nrows=sample_rows)
        dtype_map = {}
        for col in temp_df.columns:
            if temp_df[col].dtype == 'object':
                 dtype_map[col] = pd.StringDtype()
            
        return dtype_map
    except Exception as e:
        logger.warning(f"Warning: Error inferring dtypes: {e}. Proceeding with default.")
        return None
# -------------------------------------------


def get_gcloud_user():
    """Gets the currently logged in gcloud user using shell=True for stability."""
    try:
        command = "gcloud auth list --filter=status:ACTIVE --format=value(account)"
        # Use shell=True for stability with external binaries
        result = subprocess.run(
            command, 
            check=True, 
            capture_output=True, 
            text=True,
            shell=True 
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing gcloud (check PATH and login status): {e.stderr}")
        time.sleep(1)
        raise
    except FileNotFoundError:
        logger.error("Error: 'gcloud' command not found. Ensure Google Cloud CLI is installed and in your PATH.")
        raise

def get_access_token():
    """Gets the access token for the currently logged in gcloud user using shell=True for stability."""
    try:
        command = "gcloud auth print-access-token"
        # Use shell=True for stability with external binaries
        result = subprocess.run(
            command, 
            check=True, 
            capture_output=True, 
            text=True,
            shell=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing gcloud access token command: {e.stderr}")
        time.sleep(1)
        raise
    except FileNotFoundError:
        logger.error("Error: 'gcloud' command not found. Ensure Google Cloud CLI is installed and in your PATH.")
        raise
        
def check_database_exists(db_name, db_type, user, password):
    """Checks if the specified database exists and is accessible."""
    try:
        if db_type == "postgres":
            with psycopg2.connect(
                host="localhost",
                port=5432,
                dbname=db_name,
                user=user,
                password=password
            ) as conn:
                logger.info(f"Successfully connected to PostgreSQL database '{db_name}'.")
            return True
        elif db_type == "sqlsvr":
            server = "localhost"
            conn = pymssql.connect(
                server=server,
                user=user,
                password=password,
                database='master',
                port=1433
            )
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT name FROM sys.databases WHERE name = %s", (db_name,))
                    if cursor.fetchone():
                        logger.info(f"SQL Server database '{db_name}' exists.")
                        return True
                    else:
                        logger.warning(f"SQL Server database '{db_name}' does not exist.")
                        return False
    except Psycopg2Error as e:
        logger.error(f"PostgreSQL connection error: {e}")
    except pymssql.Error as e:
        logger.error(f"SQL Server connection error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during database check: {e}")
    return False

def populate_sqlsvr_database_with_csv(db_name, table_name, csv_file_path, user, password, chunk_size=10000):
    """Populates the SQL Server database with data from a CSV file in chunks."""
    logger.info(f"Attempting to populate SQL Server database {db_name} with data from {csv_file_path}")
    
    inferred_dtypes = get_csv_dtypes(csv_file_path)

    try:
        server = "localhost"
        
        with pymssql.connect(
            server=server,
            user=user,
            password=password,
            database=db_name,
            port=1433
        ) as conn:
            with conn.cursor() as cursor:
                is_first_chunk = True
                total_rows_inserted = 0
                
                for chunk_df in pd.read_csv(csv_file_path, chunksize=chunk_size, dtype=inferred_dtypes):
                    logger.info(f"Processing chunk of {len(chunk_df)} rows.")
                    
                    chunk_df.columns = [col.replace(' ', '_').lower() for col in chunk_df.columns]

                    if is_first_chunk:
                        columns_with_types = []
                        for col, dtype in chunk_df.dtypes.items():
                            if 'int' in str(dtype):
                                columns_with_types.append(f"[{col}] BIGINT")
                            elif 'float' in str(dtype):
                                columns_with_types.append(f"[{col}] FLOAT")
                            elif 'datetime' in str(dtype):
                                columns_with_types.append(f"[{col}] DATETIME2")
                            else:
                                columns_with_types.append(f"[{col}] NVARCHAR(MAX)")
                        
                        cursor.execute(f"IF OBJECT_ID('{table_name}', 'U') IS NULL CREATE TABLE {table_name} ({(', '.join(columns_with_types))});")
                        logger.info(f"Table {table_name} created or already exists.")
                        is_first_chunk = False

                    values = [tuple(x) for x in chunk_df.to_numpy()]
                    columns = ', '.join([f'[{col}]' for col in chunk_df.columns])
                    placeholders = ', '.join(['%s' for _ in chunk_df.columns])
                    insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                    
                    cursor.executemany(insert_query, values)
                    conn.commit()
                    
                    total_rows_inserted += len(chunk_df)
                    logger.info(f"Successfully inserted chunk. Total rows inserted so far: {total_rows_inserted}")

                logger.info(f"Finished inserting all data. Total rows inserted: {total_rows_inserted} into {table_name}.")

    except FileNotFoundError:
        logger.error(f"CSV file not found at {csv_file_path}.")
    except pymssql.Error as e:
        logger.error(f"SQL Server database error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

def populate_postgres_database_with_csv(db_name, table_name, csv_file_path, user, password, chunk_size=10000):
    """Populates the PostgreSQL database with data from a CSV file using chunking."""
    logger.info(f"Attempting to populate PostgreSQL database {db_name} with data from {csv_file_path}")
    
    inferred_dtypes = get_csv_dtypes(csv_file_path)

    try:
        # Establish database connection
        with psycopg2.connect(
            host="localhost",
            port=5432,
            dbname=db_name,
            user=user,
            password=password
        ) as conn:
            with conn.cursor() as cur:
                is_first_chunk = True
                total_rows_inserted = 0

                for chunk_df in pd.read_csv(csv_file_path, chunksize=chunk_size, dtype=inferred_dtypes):
                    logger.info(f"Processing chunk of {len(chunk_df)} rows.")

                    chunk_df.columns = [col.replace(' ', '_').lower() for col in chunk_df.columns]

                    if is_first_chunk:
                        columns_with_types = []
                        for col, dtype in chunk_df.dtypes.items():
                            if 'int' in str(dtype):
                                columns_with_types.append(f"{col} INTEGER")
                            elif 'float' in str(dtype):
                                columns_with_types.append(f"{col} NUMERIC")
                            elif 'datetime' in str(dtype):
                                columns_with_types.append(f"{col} TIMESTAMP")
                            else:
                                columns_with_types.append(f"{col} TEXT")
                        
                        create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns_with_types)});"
                        cur.execute(create_table_query)
                        logger.info(f"Table {table_name} created or already exists.")
                        is_first_chunk = False
                        
                    values = [tuple(x) for x in chunk_df.to_numpy()]
                    columns = ', '.join(chunk_df.columns)
                    insert_query = f"INSERT INTO {table_name} ({columns}) VALUES %s"
                    
                    execute_values(cur, insert_query, values)
                    conn.commit()

                    total_rows_inserted += len(chunk_df)
                    logger.info(f"Successfully inserted chunk. Total rows inserted so far: {total_rows_inserted}")

                logger.info(f"Finished inserting all data. Total rows inserted: {total_rows_inserted} into {table_name}.")

    except FileNotFoundError:
        logger.error(f"CSV file not found at {csv_file_path}. Please ensure it exists.")
    except Psycopg2Error as e:
        logger.error(f"Database error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")


def start_sqlsvr_proxy():
    """Starts the Cloud SQL Auth Proxy for SQL Server, isolating it into a new process group."""
    try:
        # Check if the proxy is already running
        subprocess.run(["pgrep", "-f", "cloud_sql_proxy"], check=True, capture_output=True)
        logger.info("Cloud SQL Auth Proxy is already running.")
        return None
    except subprocess.CalledProcessError:
        logger.info("Cloud SQL Auth Proxy not running. Starting it now...")

    proxy_path = os.getenv("GOOGLE_CLOUD_SQLSVR_AUTH_PROXY_PATH")
    sqlsvr_proxy_script = os.getenv("GOOGLE_CLOUD_SQLSVR_AUTH_PROXY_SCRIPT")

    if not proxy_path or not sqlsvr_proxy_script:
        logger.error("Cannot start proxy: env variables not set.")
        return None

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    sqlsvr_proxy_script_path = os.path.join(project_root, proxy_path, sqlsvr_proxy_script)

    if not os.path.exists(sqlsvr_proxy_script_path):
        logger.error(f"Cloud SQL Auth Proxy script not found at {sqlsvr_proxy_script_path}")
        return None

    try:
        subprocess.run(["chmod", "+x", sqlsvr_proxy_script_path], check=True)
        
        # CRITICAL FIX: Explicitly launch with /bin/sh and start_new_session=True for isolation
        proxy_process = subprocess.Popen(
            ["/bin/sh", sqlsvr_proxy_script_path], 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL,
            start_new_session=True 
        )
        logger.info(f"Cloud SQL Auth Proxy started in the background with PID: {proxy_process.pid}")
        time.sleep(5)
        return proxy_process