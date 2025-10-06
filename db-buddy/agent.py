"""Database Buddy Root Agent: Take the natural language inputs from 
the end user and execute SQL commands and return outputs."""

import os
import subprocess

from typing import Any, Dict, Optional

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import BaseTool, ToolContext
from google.adk.tools.bigquery import BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode
from google.genai import types

from .tools import rag_response
from .postgres_tools import (
    execute_postgres_query,
    list_postgres_databases,
    list_postgres_tables,
    list_postgres_instances,
)
from .prompts import AGENT_INSTRUCTIONS

import vertexai

from dotenv import load_dotenv
load_dotenv()

# Load env variables
root_agent_model = os.getenv("ROOT_AGENT_MODEL")
project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
region = os.getenv("GOOGLE_CLOUD_LOCATION")

# Initialize Vertex AI
vertexai.init(project=project_id, location=region)

# Setup Application Integration
from google.adk.tools.application_integration_tool.application_integration_toolset import ApplicationIntegrationToolset

app_int_region=os.getenv("APP_INT_REGION")
app_int_connection=os.getenv("APP_INT_CONNECTION")
app_int_tool_name_prefix=os.getenv("APP_INT_TOOL_NAME_PREFIX")
app_int_tool_instructions=os.getenv("APP_INT_TOOL_INSTRUCTIONS")
# google_cloud_sqlsvr_db=os.getenv("GOOGLE_CLOUD_SQLSVR_DB")
google_cloud_sqlsvr_table=os.getenv("GOOGLE_CLOUD_SQLSVR_TABLE")

app_int_cloud_sql_sqlsvr_connector_tool = ApplicationIntegrationToolset(
    project=project_id, # TODO: replace with GCP project of the connection
    location=app_int_region, #TODO: replace with location of the connection
    connection=app_int_connection, #TODO: replace with connection name "projects/genai-app-builder/locations/europe-central2/connections/gdrive-connection", ##
    entity_operations={
        google_cloud_sqlsvr_table:
            [
            "LIST",    # Used for querying/retrieving multiple records
            "GET",     # Used for retrieving a single record by its key
            "CREATE",  # Used for inserting new records
            "UPDATE",  # Used for modifying existing records
            "DELETE",  # Used for removing records
            ]
    },##{"Entity_One": ["LIST","CREATE"], "Entity_Two": []},#empty list for actions means all operations on the entity are supported.
    # actions=["GET_files"], #TODO: replace with actions
    ##service_account_credentials='{...}', # optional
    tool_name_prefix=app_int_tool_name_prefix,
    tool_instructions=app_int_tool_instructions
)

def setup_before_agent_call(callback_context: CallbackContext):
    """Setup the agent and ensure that the Cloud SQL Proxy is running"""
    
    proxy_path = os.getenv("GOOGLE_CLOUD_SQLSVR_AUTH_PROXY_PATH")
    sqlsvr_proxy_script = os.getenv("GOOGLE_CLOUD_SQLSVR_AUTH_PROXY_SCRIPT")

    if not proxy_path or not sqlsvr_proxy_script:
        print("Skipping Cloud SQL Auth Proxy setup because environment variables are not set.")
        return

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
    
    sqlsvr_proxy_script_path = os.path.join(project_root, proxy_path, sqlsvr_proxy_script)

    if not os.path.exists(sqlsvr_proxy_script_path):
        print(f"Error: Cloud SQL Auth Proxy script not found at {sqlsvr_proxy_script_path}")
        return

    try:
        # Make sure the script is executable
        subprocess.run(["chmod", "+x", sqlsvr_proxy_script_path], check=True)
        
        # Start the proxy in the background
        subprocess.Popen([sqlsvr_proxy_script_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("New Cloud SQL Auth Proxy process started in the background.")
    except Exception as e:
        print(f"Error: Failed to start Cloud SQL Auth Proxy: {e}")

root_agent = Agent(
    model=root_agent_model,
    name="Database_Buddy_Root_Agent",
    instruction=AGENT_INSTRUCTIONS,
    tools=[
        rag_response,
        execute_postgres_query,
        list_postgres_databases,
        list_postgres_tables,
        list_postgres_instances,
        app_int_cloud_sql_sqlsvr_connector_tool,
    ],
    before_agent_callback=setup_before_agent_call,
    generate_content_config=types.GenerateContentConfig(temperature=0.01),

)