import os
import psycopg2
from google.adk.tools import FunctionTool
from dotenv import load_dotenv

load_dotenv()

def get_postgres_connection(dbname=None):
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host='127.0.0.1',
            port=5432,
            user='postgres',
            password=os.getenv("GOOGLE_CLOUD_POSTGRES_PASSWORD"),
            dbname=dbname if dbname else os.getenv("GOOGLE_CLOUD_POSTGRES_DB")
        )
        return conn
    except psycopg2.OperationalError as e:
        # This could be due to the proxy not running.
        # Provide a helpful error message.
        raise Exception(
            "Could not connect to PostgreSQL. "
            "Please ensure the Cloud SQL Auth Proxy is running in a separate terminal. "
            "You can start it by running the `cloud_sql_auth_proxy.sh` script."
        ) from e


def _execute_postgres_query_func(database_name: str, query: str) -> str:
    """Executes a SQL query against a PostgreSQL database and returns the result."""
    conn = get_postgres_connection(database_name)
    cur = conn.cursor()
    try:
        cur.execute(query)
        if cur.description:
            # Fetch all rows for queries that return results (e.g., SELECT)
            results = cur.fetchall()
            # Get column names from the cursor description
            colnames = [desc[0] for desc in cur.description]
            # Format the output as a string with a header
            formatted_results = ", ".join(colnames) + "\n"
            for row in results:
                formatted_results += ", ".join(map(str, row)) + "\n"
            return formatted_results
        else:
            # For queries that don't return rows (e.g., INSERT, UPDATE, DELETE)
            # return the number of rows affected.
            return f"Query executed successfully. {cur.rowcount} rows affected."
    except Exception as e:
        return f"An error occurred: {e}"
    finally:
        cur.close()
        conn.close()

execute_postgres_query = FunctionTool(_execute_postgres_query_func)

def _list_postgres_databases_func() -> list[str]:
    """Lists all databases in the PostgreSQL instance."""
    conn = get_postgres_connection('postgres') # Connect to the default 'postgres' db to query for other dbs
    cur = conn.cursor()
    cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
    databases = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return databases

list_postgres_databases = FunctionTool(_list_postgres_databases_func)

def _list_postgres_tables_func(database_name: str) -> list[str]:
    """Lists all tables in a specific PostgreSQL database."""
    conn = get_postgres_connection(database_name)
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return tables

list_postgres_tables = FunctionTool(_list_postgres_tables_func)

import googleapiclient.discovery

def _list_postgres_instances_func() -> list[str]:
    """Lists all PostgreSQL instances in a given Google Cloud project."""
    service = googleapiclient.discovery.build('sqladmin', 'v1beta4')
    request = service.instances().list(project=os.getenv("GOOGLE_CLOUD_PROJECT_ID"))
    response = request.execute()

    instances = []
    if 'items' in response:
        for item in response['items']:
            if item['databaseVersion'].startswith('POSTGRES'):
                instances.append(item['name'])
    return instances

list_postgres_instances = FunctionTool(_list_postgres_instances_func)
