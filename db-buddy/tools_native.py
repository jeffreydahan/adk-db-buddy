# Native Tools defintion

import os
from google.adk.tools.application_integration_tool.application_integration_toolset import ApplicationIntegrationToolset
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai.preview import rag
import vertexai

# Set variables for Integration Connector
project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
app_int_region=os.getenv("APP_INT_REGION")
app_int_connection=os.getenv("APP_INT_CONNECTION")
app_int_tool_name_prefix=os.getenv("APP_INT_TOOL_NAME_PREFIX")
app_int_tool_instructions=os.getenv("APP_INT_TOOL_INSTRUCTIONS")
google_cloud_sqlsvr_table=os.getenv("GOOGLE_CLOUD_SQLSVR_TABLE")

# Build Integration Connector object
app_int_cloud_sql_sqlsvr_connector = ApplicationIntegrationToolset(
    project=project_id, # TODO: replace with GCP project of the connection
    location=app_int_region, #TODO: replace with location of the connection
    connection=app_int_connection, #TODO: replace with connection name "projects/genai-app-builder/locations/europe-central2/connections/gdrive-connection", ##
    entity_operations={google_cloud_sqlsvr_table:["LIST", "GET", "CREATE", "UPDATE", "DELETE"]},
    tool_name_prefix=app_int_tool_name_prefix,
    tool_instructions=app_int_tool_instructions
)

# Set variables for RAG Engine Connector
rag_engine_region = os.getenv("RAG_ENGINE_REGION")
rag_engine_name = os.getenv("RAG_ENGINE_NAME")

# Dynamically find the rag_corpus name
vertexai.init(project=project_id, location=rag_engine_region)
rag_corpora = rag.list_corpora()
rag_corpus_name = ""
for corpus in rag_corpora:
    if corpus.display_name == rag_engine_name:
        rag_corpus_name = corpus.name
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