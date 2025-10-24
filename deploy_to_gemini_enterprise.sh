#!/bin/bash

set -x
source .env

# Get GCP Access Token
ACCESS_TOKEN=$(gcloud auth print-access-token)

# Use the following from the .env file, or a default if not set
PROJECT_ID="${GOOGLE_CLOUD_PROJECT_ID}"
COLLECTION_ID="default_collection"
ENGINE_ID="${AGENTSPACE_ENGINE_ID}"
ASSISTANT_ID="default_assistant"
REASONING_ENGINE_ID="${AGENT_ENGINE_APP_RESOURCE_ID}"
AGENT_NAME="${AGENT_NAME}"
AGENT_DESCRIPTION="${AGENT_DESCRIPTION}"
TOOL_DESCRIPTION="${AGENT_TOOL_DESCRIPTION}"

# Print the above variables returned from .env file
echo "PROJECT_ID: ${PROJECT_ID}"
echo "COLLECTION_ID: ${COLLECTION_ID}"
echo "ENGINE_ID: ${ENGINE_ID}"
echo "ASSISTANT_ID: ${ASSISTANT_ID}"
echo "REASONING_ENGINE_ID: ${REASONING_ENGINE_ID}"
echo "AGENT_NAME: ${AGENT_NAME}"
echo "AGENT_DESCRIPTION: ${AGENT_DESCRIPTION}"
echo "TOOL_DESCRIPTION: ${TOOL_DESCRIPTION}"

# Get the Project Number from the Project ID
PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format='get(projectNumber)')
echo "PROJECT_NUMBER: ${PROJECT_NUMBER}"

# Build the service account principal using the Project Number service-[ProjectNumber]@gcp-sa-aiplatform-re.iam.gserviceaccount.com
SERVICE_ACCOUNT_PRINCIPAL="service-${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
# Grand the role of Application Integration Invoker to the service account principal
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SERVICE_ACCOUNT_PRINCIPAL}" \
    --role="roles/integrations.integrationInvoker"

# Build API Endpoint - it must use the 'global' location hard coded
API_ENDPOINT="https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/collections/${COLLECTION_ID}/engines/${ENGINE_ID}/assistants/${ASSISTANT_ID}/agents"

# JSON Payload to create the Agent Object inside Agentspace
JSON_PAYLOAD=$(cat <<EOF
{
    "displayName": "${AGENT_NAME}",
    "description": "${AGENT_DESCRIPTION}",
    "adk_agent_definition": {
        "tool_settings": {
            "tool_description": "${TOOL_DESCRIPTION}"
        },
        "provisioned_reasoning_engine": {
            "reasoning_engine": "${REASONING_ENGINE_ID}"
        }
    }
}
EOF
)

# Execute
curl -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "X-Goog-User-Project: ${PROJECT_ID}" \
    "${API_ENDPOINT}" \
    -d "${JSON_PAYLOAD}"

# Go to Agentspace and click Agents to view and test your agent.
# If you want to delete the Agent, just click the 3 dots on the Agent
# and select Delete.