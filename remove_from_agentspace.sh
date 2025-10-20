#!/bin/bash

# This script removes an agent from Google Cloud Discovery Engine Agentspace.
# It finds the agent by its displayName (AGENT_NAME) and then issues a delete command.

# Source environment variables from .env file
if [ -f .env ]; then
    set -a # Automatically export all variables
    source .env
    set +a # Stop automatically exporting
fi

# Get GCP Access Token
ACCESS_TOKEN=$(gcloud auth print-access-token)
if [ -z "${ACCESS_TOKEN}" ]; then
    echo "Error: Failed to get GCP Access Token."
    echo "Please ensure you are authenticated with 'gcloud auth login' and 'gcloud auth application-default login'."
    exit 1
fi

# Check if jq is installed
if ! command -v jq &> /dev/null
then
    echo "Error: jq could not be found. jq is required to parse API responses."
    echo "Please install jq. For example:"
    echo "  On Debian/Ubuntu: sudo apt-get install jq"
    echo "  On macOS: brew install jq"
    exit 1
fi

# Configuration: Use variables from .env or provide defaults/ensure they are set
PROJECT_ID="${GOOGLE_CLOUD_PROJECT}"
COLLECTION_ID="${COLLECTION_ID:-default_collection}" # Default if not in .env
ENGINE_ID="${AGENTSPACE_ENGINE_ID}"
ASSISTANT_ID="${ASSISTANT_ID:-default_assistant}"   # Default if not in .env

### Change this variable as needed if you want to delete other agents as well
AGENT_NAME_TO_DELETE="CameraCleaningAgent"               # Agent's displayName to delete

# Validate required variables that don't have defaults
if [ -z "${PROJECT_ID}" ]; then
    echo "Error: GOOGLE_CLOUD_PROJECT is not set. Please set it in your .env file or environment."
    exit 1
fi
if [ -z "${ENGINE_ID}" ]; then
    echo "Error: AGENTSPACE_ENGINE_ID is not set. Please set it in your .env file or environment."
    exit 1
fi
if [ -z "${AGENT_NAME_TO_DELETE}" ]; then
    echo "Error: AGENT_NAME is not set. Please set it in your .env file or environment to specify which agent to delete."
    exit 1
fi

# API Endpoint to list agents
LIST_AGENTS_API_ENDPOINT="https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/global/collections/${COLLECTION_ID}/engines/${ENGINE_ID}/assistants/${ASSISTANT_ID}/agents"

echo "Attempting to find agent with displayName: '${AGENT_NAME_TO_DELETE}'..."

# List agents and extract the resource name of the agent to delete
# Uses jq to parse the JSON and find the agent by its displayName.
# Takes the first match if multiple agents have the same displayName.
AGENT_RESOURCE_NAME=$(curl -s -X GET \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "X-Goog-User-Project: ${PROJECT_ID}" \
    "${LIST_AGENTS_API_ENDPOINT}" \
    | jq -r --arg agent_name "${AGENT_NAME_TO_DELETE}" '.agents[]? | select(.displayName == $agent_name) | .name' | head -n 1)

if [ -z "${AGENT_RESOURCE_NAME}" ] || [ "${AGENT_RESOURCE_NAME}" == "null" ]; then
    echo "Error: Agent with displayName '${AGENT_NAME_TO_DELETE}' not found under project '${PROJECT_ID}', collection '${COLLECTION_ID}', engine '${ENGINE_ID}', assistant '${ASSISTANT_ID}'."
    echo "Please check the AGENT_NAME in your .env file and ensure the agent exists in Agentspace."
    exit 1
fi

echo "Found agent. Full resource name: ${AGENT_RESOURCE_NAME}"

# The AGENT_RESOURCE_NAME is the full path like projects/.../agents/AGENT_ID
# The API endpoint for deletion uses this full resource name.
DELETE_API_ENDPOINT="https://discoveryengine.googleapis.com/v1alpha/${AGENT_RESOURCE_NAME}"

echo "Attempting to delete agent: ${AGENT_RESOURCE_NAME}..."

# Execute Delete request
curl -X DELETE \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "X-Goog-User-Project: ${PROJECT_ID}" \
    "${DELETE_API_ENDPOINT}"

echo "" # Newline for better readability of curl output
echo "Deletion request sent for agent '${AGENT_NAME_TO_DELETE}' (Resource: ${AGENT_RESOURCE_NAME})."
echo "If the agent existed and permissions are correct, it should now be deleted."
echo "Please verify in Agentspace."

exit 0