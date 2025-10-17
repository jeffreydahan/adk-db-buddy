"""Database Buddy Root Agent: Take the natural language inputs from 
the end user, execute database queries and return outputs."""

import os
from google.genai import types
from google.adk.agents import Agent
from .tools_custom import execute_postgres_query, setup_before_agent_call
from .tools_native import app_int_cloud_sql_sqlsvr_connector, rag_engine_connector
from .prompts import root_agent_instructions
import vertexai

# Load env variables
root_agent_model = os.getenv("ROOT_AGENT_MODEL")
project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
region = os.getenv("GOOGLE_CLOUD_LOCATION")

# Initialize Vertex AI
vertexai.init(project=project_id, location=region)

# Define the root agent with tools and instructions
root_agent = Agent(
    model=root_agent_model,
    name="Database_Buddy_Root_Agent",
    instruction=root_agent_instructions,
    tools=[execute_postgres_query, app_int_cloud_sql_sqlsvr_connector, rag_engine_connector],
    before_agent_callback=setup_before_agent_call,
    generate_content_config=types.GenerateContentConfig(temperature=0.01),
)