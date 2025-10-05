import os
import logging
import pandas as pd
import psycopg2
import subprocess
from io import StringIO
from psycopg2 import Error as Psycopg2Error
from psycopg2.extras import execute_values
from dotenv import load_dotenv
import pymssql
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_gcloud_user():
    """Gets the currently logged in gcloud user."""
    try:
        command = [
            "gcloud",
            "auth",
            "list",
            "--filter=status:ACTIVE",
            "--format=value(account)",
        ]
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting gcloud user: {e.stderr}")
        raise

def get_access_token():
    """Gets the access token for the currently logged in gcloud user."""
    try:
        command = ["gcloud", "auth", "print-access-token"]
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting access token: {e.stderr}")
        raise

def check_database_exists(db_name, db_type, user, password):
    """Checks if the specified database exists and is accessible."""
    try:
        if db_type == "postgres":
            with psycopg2.connect(
                host="localhost",
                port=5432,
                dbname=db_name, # Connect directly to the target DB
                user=user,
                password=password
            ) as conn:
                logger.info(f"Successfully connected to PostgreSQL database '{db_name}'.")
            return True
        elif db_type == "sqlsvr":
            # For SQL Server, the pyodbc connection string needs to be precise.
            # You connect to the server first, then check for the database's existence.
            # The driver name might need to be adjusted based on what's installed.
            server = "localhost"
            conn = pymssql.connect(
                server=server,
                user=user,
                password=password,
                database='master',
                port=1433
            )
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
        return False
    except pymssql.Error as e:
        logger.error(f"SQL Server connection error: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during database check: {e}")
        return False
    return False

def populate_sqlsvr_database_with_csv(db_name, csv_file_path, user, password, num_rows=100000):
    """Populates the SQL Server database with data from a CSV file."""
    logger.info(f"Attempting to populate SQL Server database {db_name} with data from {csv_file_path}")
    try:
        df = pd.read_csv(csv_file_path, nrows=num_rows)
        logger.info(f"Successfully read {len(df)} rows from {csv_file_path}.")

        df.columns = [col.replace(' ', '_').lower() for col in df.columns]

        server = "localhost"
        
        with pymssql.connect(
            server=server,
            user=user,
            password=password,
            database=db_name,
            port=1433
        ) as conn:
            with conn.cursor() as cursor:
                table_name = "nyc_taxi_data"
                
                columns_with_types = []
                for col, dtype in df.dtypes.items():
                    if 'int' in str(dtype):
                        columns_with_types.append(f"[{col}] BIGINT")
                    elif 'float' in str(dtype):
                        columns_with_types.append(f"[{col}] FLOAT")
                    elif 'datetime' in str(dtype):
                        columns_with_types.append(f"[{col}] DATETIME2")
                    else:
                        columns_with_types.append(f"[{col}] NVARCHAR(MAX)")
                
                # Check if table exists before creating
                cursor.execute(f"IF OBJECT_ID('{table_name}', 'U') IS NULL CREATE TABLE {table_name} ({(', '.join(columns_with_types))});")
                logger.info(f"Table {table_name} created or already exists.")

                # Efficient bulk insert for SQL Server
                values = [tuple(x) for x in df.to_numpy()]
                columns = ', '.join([f'[{col}]' for col in df.columns])
                placeholders = ', '.join(['%s' for _ in df.columns])
                insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                
                cursor.executemany(insert_query, values)
                conn.commit()
                logger.info(f"Successfully inserted {len(df)} rows into {table_name}.")

    except FileNotFoundError:
        logger.error(f"CSV file not found at {csv_file_path}.")
    except pymssql.Error as e:
        logger.error(f"SQL Server database error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

def populate_database_with_csv(db_name, csv_file_path, num_rows=100000):
    """Populates the PostgreSQL database with data from a CSV file."""
    logger.info(f"Attempting to populate database {db_name} with data from {csv_file_path}")
    logger.info(f"This can take over an hour if you have 100,000 rows of data.")
    try:
        iam_user = get_gcloud_user()
        access_token = get_access_token()

        df = pd.read_csv(csv_file_path, nrows=num_rows)
        logger.info(f"Successfully read {len(df)} rows from {csv_file_path}.")

        # Clean column names for SQL
        df.columns = [col.replace(' ', '_').lower() for col in df.columns]

        # Establish database connection
        with psycopg2.connect(
            host="localhost",
            port=5432,
            dbname=db_name,
            user=iam_user,
            password=access_token
        ) as conn:
            with conn.cursor() as cur:
                # Create table schema dynamically from DataFrame columns
                table_name = "nyc_taxi_data"
                columns_with_types = []
                for col, dtype in df.dtypes.items():
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

                # Use execute_values for efficient bulk insert
                values = [tuple(x) for x in df.to_numpy()]
                columns = ', '.join(df.columns)
                insert_query = f"INSERT INTO {table_name} ({columns}) VALUES %s"
                
                execute_values(cur, insert_query, values)
                conn.commit()
                logger.info(f"Successfully inserted {len(df)} rows into {table_name}.")

    except FileNotFoundError:
        logger.error(f"CSV file not found at {csv_file_path}. Please ensure it exists.")
    except Psycopg2Error as e:
        logger.error(f"Database error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

def main():
    """Main function to populate the database."""
    parser = argparse.ArgumentParser(description="Populate a database from a CSV file.")
    parser.add_argument(
        "db_type",
        choices=["postgres", "sqlsvr"],
        help="The type of database to populate."
    )
    args = parser.parse_args()
    db_type = args.db_type

    load_dotenv()

    db_name_env_var = f"GOOGLE_CLOUD_{db_type.upper()}_DB"
    db_seed_data_env_var = f"GOOGLE_CLOUD_{db_type.upper()}_DB_SEED_DATA"

    db_name = os.getenv(db_name_env_var)
    db_seed_data = os.getenv(db_seed_data_env_var)

    if not all([db_name, db_seed_data]):
        logger.error(f"Missing environment variables: {db_name_env_var} or {db_seed_data_env_var}")
        return

    if db_type == "sqlsvr":
        user = os.getenv("GOOGLE_CLOUD_SQLSVR_USER")
        password = os.getenv("GOOGLE_CLOUD_SQLSVR_PASSWORD")
        if not all([user, password]):
            logger.error("Missing GOOGLE_CLOUD_SQLSVR_USER or GOOGLE_CLOUD_SQLSVR_PASSWORD environment variables.")
            return
    else:
        try:
            user = get_gcloud_user()
            password = get_access_token()
        except Exception as e:
            logger.error(f"Failed to get gcloud credentials: {e}")
            return

    logger.info(f"Checking if {db_type} database '{db_name}' exists...")
    if not check_database_exists(db_name, db_type, user, password):
        logger.error(f"Database '{db_name}' does not exist or is not accessible. Please create it first.")
        return

    # Construct absolute path for the CSV file
    # Assumes the script is run from the deployment directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    absolute_csv_path = os.path.join(project_root, "source-data", db_type, db_seed_data)

    if db_type == "postgres":
        populate_database_with_csv(db_name, absolute_csv_path)
    elif db_type == "sqlsvr":
        populate_sqlsvr_database_with_csv(db_name, absolute_csv_path, user, password)


if __name__ == "__main__":
    main()
