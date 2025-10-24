"""Database Buddy Root Agent: Take the natural language inputs from 
the end user, execute database queries and return outputs."""

import os
from google.genai import types
from google.adk.tools.agent_tool import AgentTool
from google.adk.agents import Agent
from tools.tools_native import app_int_cloud_sql_sqlsvr_connector, app_int_cloud_sql_postgres_connector, rag_engine_connector
from .prompts import root_agent_instructions, cloud_sql_postgres_agent_instructions, cloud_sql_sqlsvr_agent_instructions, rag_engine_agent_instructions
import vertexai
import os

# Helper function to get environment variables
def get_env_var(key):
    value = os.getenv(key)
    if value is None or not value.strip():
        raise ValueError(f"Environment variable '{key}' not found or is empty.")
    return value

# Load required env variables
root_agent_model = get_env_var("ROOT_AGENT_MODEL")
cloud_sql_postgres_agent_model = get_env_var("POSTGRES_AGENT_MODEL")
cloud_sql_sqlsvr_agent_model = get_env_var("SQLSVR_AGENT_MODEL")
rag_agent_model = get_env_var("RAG_AGENT_MODEL")
project_id = get_env_var("GOOGLE_CLOUD_PROJECT_ID")
region = get_env_var("GOOGLE_CLOUD_LOCATION")

# Initialize Vertex AI
vertexai.init(project=project_id, location=region)

# Define Cloud SQL Posgres Server Agent
cloud_sql_postgres_agent = Agent(
    model=cloud_sql_postgres_agent_model,
    name="Cloud_SQL_Postgres_Agent",
    instruction=cloud_sql_postgres_agent_instructions,
    tools=[app_int_cloud_sql_postgres_connector],
    generate_content_config=types.GenerateContentConfig(temperature=0.01),
)

# Define Cloud SQL SQL Server Agent
cloud_sql_sqlsvr_agent = Agent(
    model=cloud_sql_sqlsvr_agent_model,
    name="Cloud_SQL_SQLServer_Agent",
    instruction=cloud_sql_sqlsvr_agent_instructions,
    tools=[app_int_cloud_sql_sqlsvr_connector],
    generate_content_config=types.GenerateContentConfig(temperature=0.01),
)

# Define RAG Engine Agent
rag_engine_agent = Agent(
    model=rag_agent_model,
    name="RAG_Engine_Agent",
    instruction=rag_engine_agent_instructions,
    tools=[rag_engine_connector],
    generate_content_config=types.GenerateContentConfig(temperature=0.01),
)

# Define the root agent with tools and instructions
root_agent = Agent(
    model=root_agent_model,
    name="RootAgent",
    instruction=root_agent_instructions,
    tools=[AgentTool(agent=cloud_sql_postgres_agent), AgentTool(agent=cloud_sql_sqlsvr_agent), AgentTool(agent=rag_engine_agent)],
    generate_content_config=types.GenerateContentConfig(temperature=0.01),
)