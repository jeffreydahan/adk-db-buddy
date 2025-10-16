# Custom tools defintions

import os
from google.adk.tools import FunctionTool
import psycopg2
import subprocess 
from google.adk.tools.application_integration_tool.application_integration_toolset import ApplicationIntegrationToolset
from google.adk.agents.callback_context import CallbackContext

project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
region = os.getenv("GOOGLE_CLOUD_LOCATION")


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
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise Exception("Could not get gcloud user. Please ensure you are logged in to gcloud.") from e

def get_access_token():
    """Gets the access token for the currently logged in gcloud user."""
    try:
        command = ["gcloud", "auth", "print-access-token"]
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise Exception("Could not get access token. Please ensure you are logged in to gcloud.") from e

def get_postgres_connection(dbname=None):
    """Establishes a connection to the PostgreSQL database using IAM authentication."""
    try:
        iam_user = get_gcloud_user()
        access_token = get_access_token()

        conn = psycopg2.connect(
            host='127.0.0.1',
            port=5432,
            user=iam_user,
            password=access_token,
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


def execute_postgres_query(query: str) -> str:
    """
    Executes a SQL query against a PostgreSQL database and returns the result.
    The postgres connector and corresponding instance/databse/table contains
    information on nyc taxi rides.
    """
    conn = get_postgres_connection()
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

def setup_before_agent_call(callback_context: CallbackContext):
    """Setup the agent and ensure that the Cloud SQL Proxy is running"""
    
    proxy_path = os.getenv("GOOGLE_CLOUD_POSTGRES_PATH")
    proxy_script = os.getenv("GOOGLE_CLOUD_POSTGRES_PROXY_SCRIPT")

    print("Setting up Cloud SQL Auth Proxy...")
    try:
        # Kill any existing cloud_sql_proxy processes
        subprocess.run(["pkill", "-f", "cloud_sql_proxy"])
        print("Stopped existing Cloud SQL Auth Proxy processes.")
    except FileNotFoundError:
        # pkill is not installed, which is unlikely in a linux env
        print("Warning: pkill command not found. Could not stop existing proxy processes.")

    # Start a new proxy process
    print("Starting a new Cloud SQL Auth Proxy process...")
    
    # Get the project root directory (assuming agent.py is in a subdirectory)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    proxy_script_path = os.path.join(project_root, proxy_path, proxy_script)

    if not os.path.exists(proxy_script_path):
        print(f"Error: Cloud SQL Auth Proxy script not found at {proxy_script_path}")
        return

    try:
        # Make sure the script is executable
        subprocess.run(["chmod", "+x", proxy_script_path], check=True)
        
        # Start the proxy in the background
        subprocess.Popen([proxy_script_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("New Cloud SQL Auth Proxy process started in the background.")
    except Exception as e:
        print(f"Error: Failed to start Cloud SQL Auth Proxy: {e}")

