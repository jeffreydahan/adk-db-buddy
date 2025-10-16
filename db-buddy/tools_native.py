# Native Tools defintion

import os
from google.adk.tools.application_integration_tool.application_integration_toolset import ApplicationIntegrationToolset

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

