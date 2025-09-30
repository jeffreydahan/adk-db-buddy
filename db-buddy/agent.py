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

def setup_before_agent_call(callback_context: CallbackContext):
    """Setup the agent and ensure that the Cloud SQL Proxy is running"""
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
    proxy_script_path = os.path.join(project_root, "cloud_sql_auth_proxy.sh")

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
    ],
    before_agent_callback=setup_before_agent_call,
    generate_content_config=types.GenerateContentConfig(temperature=0.01),

)