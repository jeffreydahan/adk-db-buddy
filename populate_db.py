import os
import logging
import pandas as pd
import psycopg2
from psycopg2 import Error as Psycopg2Error
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def populate_database_with_csv(project_id, instance_name, db_name, password, csv_file_path, num_rows=20000):
    """Populates the PostgreSQL database with data from a CSV file."""
    logger.info(f"Attempting to populate database {db_name} in instance {instance_name} with data from {csv_file_path}")

    # Cloud SQL Auth Proxy connection string
    conn_string = f"postgresql://postgres:{password}@localhost:5432/{db_name}"

    try:
        df = pd.read_csv(csv_file_path, nrows=num_rows)
        logger.info(f"Successfully read {len(df)} rows from {csv_file_path}.")

        # Clean column names for SQL
        df.columns = [col.replace(' ', '_').lower() for col in df.columns]

        # Establish database connection
        with psycopg2.connect(conn_string) as conn:
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

                # Insert data
                for index, row in df.iterrows():
                    columns = ', '.join(row.index)
                    values = ', '.join(['%s'] * len(row))
                    insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({values})"
                    cur.execute(insert_query, tuple(row))
                
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

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
    postgres_instance_name = os.getenv("GOOGLE_CLOUD_POSTGRES_INSTANCE")
    postgres_db_name = os.getenv("GOOGLE_CLOUD_POSTGRES_DB")
    postgres_password = os.getenv("GOOGLE_CLOUD_POSTGRES_PASSWORD")

    if not all([project_id, postgres_instance_name, postgres_db_name, postgres_password]):
        logger.error("Missing required environment variables for database population. Please check your .env file.")
        return

    csv_file_path = "source-data/revenue-for-cab-drivers-20000-rows.csv"
    populate_database_with_csv(project_id, postgres_instance_name, postgres_db_name, postgres_password, csv_file_path)


if __name__ == "__main__":
    main()
