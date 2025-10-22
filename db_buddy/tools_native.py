# Native Tools defintion

import os
from google.adk.tools.application_integration_tool.application_integration_toolset import ApplicationIntegrationToolset
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai.preview import rag
import vertexai

# Helper function to get environment variables
def get_env_var(key):
    value = os.getenv(key)
    if value is None or not value.strip():
        raise ValueError(f"Environment variable '{key}' not found or is empty.")
    return value

project_id = get_env_var("GOOGLE_CLOUD_PROJECT_ID")

# Set variables for Integration Connector - Cloud SQL SQL Server
cloud_sql_sqlsvr_app_int_region = get_env_var("CLOUD_SQL_SQLSVR_APP_INT_REGION")
cloud_sql_sqlsvr_app_int_connection = get_env_var("CLOUD_SQL_SQLSVR_APP_INT_CONNECTION")
cloud_sql_sqlsvr_app_int_tool_name_prefix = os.getenv("CLOUD_SQL_SQLSVR_APP_INT_TOOL_NAME_PREFIX") # Optional, can be None
cloud_sql_sqlsvr_app_int_tool_instructions = os.getenv("CLOUD_SQL_SQLSVR_APP_INT_TOOL_INSTRUCTIONS") # Optional, can be None
google_cloud_sqlsvr_table = get_env_var("GOOGLE_CLOUD_SQLSVR_TABLE")

# Build Integration Connector object - Cloud SQL SQL Server
app_int_cloud_sql_sqlsvr_connector = ApplicationIntegrationToolset(
    project=project_id,
    location=cloud_sql_sqlsvr_app_int_region, 
    connection=cloud_sql_sqlsvr_app_int_connection, 
    entity_operations={google_cloud_sqlsvr_table: ["LIST", "GET", "CREATE", "UPDATE", "DELETE"]},
    tool_name_prefix=cloud_sql_sqlsvr_app_int_tool_name_prefix,
    tool_instructions=cloud_sql_sqlsvr_app_int_tool_instructions
)

# Set variables for Integration Connector - Cloud SQL Postgres
cloud_sql_postgres_app_int_region = get_env_var("CLOUD_SQL_POSTGRES_APP_INT_REGION")
cloud_sql_postgres_app_int_connection = get_env_var("CLOUD_SQL_POSTGRES_APP_INT_CONNECTION")
cloud_sql_postgres_app_int_tool_name_prefix = os.getenv("CLOUD_SQL_POSTGRES_APP_INT_TOOL_NAME_PREFIX") # Optional, can be None
cloud_sql_postgres_app_int_tool_instructions = os.getenv("CLOUD_SQL_POSTGRES_APP_INT_TOOL_INSTRUCTIONS") # Optional, can be None
google_cloud_postgres_table = os.getenv("GOOGLE_CLOUD_POSTGRES_TABLE") # This variable is not directly used in the constructor for Postgres, so it's less critical for this specific error.

# Build Integration Connector object - Cloud SQL Postgres
app_int_cloud_sql_postgres_connector = ApplicationIntegrationToolset(
    project=project_id, 
    location=cloud_sql_postgres_app_int_region, 
    connection=cloud_sql_postgres_app_int_connection, 
    actions=["ExecuteCustomQuery"],
    tool_name_prefix=cloud_sql_postgres_app_int_tool_name_prefix,
    tool_instructions=cloud_sql_postgres_app_int_tool_instructions
)

# Set variables for RAG Engine Connector
rag_engine_region = get_env_var("RAG_ENGINE_REGION")
rag_engine_name = get_env_var("RAG_ENGINE_NAME")

# Dynamically find the rag_corpus name
vertexai.init(project=project_id, location=rag_engine_region)
rag_corpora = rag.list_corpora()
rag_corpus_name = ""
for corpus in rag_corpora:
    if corpus.display_name == rag_engine_name:
        rag_corpus_name = corpus.name
        print(f"Found RAG Corpus: {rag_corpus_name}")
        print(f"Corpus Name: {corpus.name}")
        break

if not rag_corpus_name:
    raise ValueError(f"RAG Corpus with display name '{rag_engine_name}' not found.")

# Build RAG Engine Connector object
rag_engine_connector = VertexAiRagRetrieval(
    name=rag_engine_name,
    description="RAG Engine Connector which provides access to car recommendations for weather conditions.",
    rag_resources=[
        rag.RagResource(rag_corpus_name)
    ],
)