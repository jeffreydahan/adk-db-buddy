# Pull in all env variables
source .env

# Authenticate gcloud
gcloud auth login
gcloud auth application-default login

# Set default quota project
gcloud auth application-default set-quota-project ${GOOGLE_CLOUD_PROJECT_ID}
gcloud config set project ${GOOGLE_CLOUD_PROJECT_ID}


# This script deploys the camera tool to Cloud Run using Secret Manager
# and then deploys the main agent to Agent Engine.

# --- Preamble: Enable APIs and Load Environment ---
gcloud services enable run.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable connectors.googleapis.com
gcloud services enable compute.googleapis.com

# Deploy database infrastructure
python3 connector_deployment/db_deploy.py postgres

# Open another terminal to run the next command if desired in parallel
python3 connector_deployment/db_deploy.py sqlsvr

# Open another terminal to run the next command if desired in parallel
# Create RAG engine
python3 connector_deployment/rag_create.py

# Populate databases
# These may fail to run remotely depending on the network setup of the
# Cloud SQL instances.  If so, run the SQL commands from the 
# Google Cloud Console SQL interface - via the Query Editor.
# The specific commands are in the respective .sql files. under
# connector_deployment/

# Create Postgres user (privileges are granted in the populate script)
gcloud sql users create $GOOGLE_CLOUD_POSTGRES_USER --password=$GOOGLE_CLOUD_POSTGRES_PASSWORD --instance=$GOOGLE_CLOUD_POSTGRES_INSTANCE 

# Populate Postgres database
INSTANCE_NAME=$(grep GOOGLE_CLOUD_POSTGRES_INSTANCE .env | cut -d '=' -f2)
DB_NAME=$(grep GOOGLE_CLOUD_POSTGRES_DB .env | cut -d '=' -f2)
gcloud sql connect $INSTANCE_NAME --database=$DB_NAME < connector_deployment/db_postgres_populate.sql

# Populate SQL Server database
INSTANCE_NAME=$(grep GOOGLE_CLOUD_SQLSVR_INSTANCE .env | cut -d '=' -f2)
DB_NAME=$(grep GOOGLE_CLOUD_SQLSVR_DB .env | cut -d '=' -f2)
gcloud sql connect $GOOGLE_CLOUD_SQLSVR_INSTANCE --database=$DGOOGLE_CLOUD_SQLSVR_DB --user=sqlserver < connector_deployment/db_sqlsvr_populate.sql

# Create RAG engine
python3 connector_deployment/rag_create.py

# Ensure you follow the readme.md to deploy the connectors
# from the Google Cloud Console

# At this point, you can try to run the agent locally using:
# adk web
# select db_buddy as the agent on the right-hand side
# and test queries against the databases and RAG engine.

# Optional deploy to Agent Engine
# Provide Agent Engine principal access to invoke connectors
# Get the Google Cloud Project Number
PROJECT_NUMBER=$(gcloud projects describe ${GOOGLE_CLOUD_PROJECT_ID} --format='get(projectNumber)')
# Build the service account principal using the Project Number service-[ProjectNumber]@gcp-sa-aiplatform-re.iam.gserviceaccount.com
AGENT_ENGINE_ACCOUNT_PRINCIPAL="service-${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"

# Grant the role of roles/integrations.integrationInvoker to the Agent Engine service account principal
gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT_ID} \
    --member="serviceAccount:${AGENT_ENGINE_ACCOUNT_PRINCIPAL}" \
    --role="roles/integrations.integrationInvoker"

# Grant the role of roles/cloudtrace.agent to the Agent Engine service account principal
gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT_ID} \
    --member="serviceAccount:${AGENT_ENGINE_ACCOUNT_PRINCIPAL}" \
    --role="roles/cloudtrace.agent"

# Grant the role of roles/connectors.viewer to the Agent Engine service account principal
gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT_ID} \
    --member="serviceAccount:${AGENT_ENGINE_ACCOUNT_PRINCIPAL}" \
    --role="roles/connectors.viewer"

# Grant the role of roles/aiplatform.reasoningEngineServiceAgent to the Agent Engine service account principal
gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT_ID} \
    --member="serviceAccount:${AGENT_ENGINE_ACCOUNT_PRINCIPAL}" \
    --role="roles/aiplatform.reasoningEngineServiceAgent"

# Grant the role of roles/aiplatform.user to the Agent Engine service account principal
gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT_ID} \
    --member="serviceAccount:${AGENT_ENGINE_ACCOUNT_PRINCIPAL}" \
    --role="roles/aiplatform.user"

# Deploy to Agent Engine
python3 deploy_to_agent_engine.py --service-account="${AGENT_ENGINE_ACCOUNT_PRINCIPAL}"
echo $AGENT_ENGINE_APP_RESOURCE_ID

# Ensure correct permissions for Gemini Enterprise service account'
GEMINI_ENTERPRISE_ACCOUNT_PRINCIPAL="service-${PROJECT_NUMBER}@gcp-sa-discoveryengine.iam.gserviceaccount.com"

# Grant the role of roles/aiplatform.user to the Gemini Enterprise service account principal
gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT_ID} \
    --member="serviceAccount:${GEMINI_ENTERPRISE_ACCOUNT_PRINCIPAL}" \
    --role="roles/aiplatform.user"

# Deploy to Gemini Enterprise
bash deploy_to_gemini_enterprise.sh

### REMOVAL SECTION ###

# Remove from Gemini Enterprise
bash remove_from_gemini_enterprise.sh

# Remove from Agent Engine (based on Agent Name in env file; if updated, run the
# source command)
python remove_from_agent_engine.py


# if session restarts, kill the terminal and open a new terminal.  Ensure that
# you run gcloud auth login and gcloud auth application-default login again.
