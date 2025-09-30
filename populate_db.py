import os
import logging
import pandas as pd
import psycopg2
import subprocess
from io import StringIO
from psycopg2 import Error as Psycopg2Error
from psycopg2.extras import execute_values
from dotenv import load_dotenv

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
    load_dotenv()

    postgres_db_name = os.getenv("GOOGLE_CLOUD_POSTGRES_DB")
    postgres_db_seed_data = os.getenv("GOOGLE_CLOUD_POSTGRES_DB_SEED_DATA")

    if not all([postgres_db_name, postgres_db_seed_data]):
        logger.error("Missing required environment variables for database population. Please check your .env file.")
        return

    # Construct absolute path for the CSV file
    project_root = os.path.dirname(os.path.abspath(__file__))
    absolute_csv_path = os.path.join(project_root, postgres_db_seed_data)

    populate_database_with_csv(postgres_db_name, absolute_csv_path)


if __name__ == "__main__":
    main()
