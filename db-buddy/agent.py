"""Database Buddy Root Agent: Take the natural language inputs from 
the end user and execute SQL commands and return outputs."""

import os

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

root_agent_model = os.getenv("ROOT_AGENT_MODEL")
project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
region = os.getenv("GOOGLE_CLOUD_LOCATION")

vertexai.init(project=project_id, location=region)

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
    ]

)