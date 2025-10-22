gcloud auth login
gcloud auth application-default login

# This script deploys the camera tool to Cloud Run using Secret Manager
# and then deploys the main agent to Agent Engine.

# --- Preamble: Enable APIs and Load Environment ---
gcloud services enable run.googleapis.com
gcloud services enable storage.googleapis.com

# Load environment variables from .env file in the project root
cd ~/code/adk-db-buddy
source .env

# Deploy database infrastructure
python3 connector_deployment/db_deploy.py postgres
python3 connector_deployment/db_deploy.py sqlsvr

# Populate databases
INSTANCE_NAME=$(grep GOOGLE_CLOUD_POSTGRES_INSTANCE_NAME .env | cut -d '=' -f2)
DB_NAME=$(grep GOOGLE_CLOUD_POSTGRES_DB .env | cut -d '=' -f2)
gcloud sql connect $INSTANCE_NAME --database=$DB_NAME < connector_deployment/db_postgres_populate.sql

INSTANCE_NAME=$(grep GOOGLE_CLOUD_SQLSVR_INSTANCE_NAME .env | cut -d '=' -f2)
DB_NAME=$(grep GOOGLE_CLOUD_SQLSVR_DB .env | cut -d '=' -f2)
gcloud sql connect $INSTANCE_NAME --database=$DB_NAME --user=sqlserver < connector_deployment/db_sqlsvr_populate.sql

# Create RAG engine
python3 connector_deployment/rag_create.py

# Deploy to Agent Engine
cd ~/code/adk-db-buddy
source .env
python3 deploy_to_agent_engine.py
echo $AGENT_ENGINE_APP_RESOURCE_ID

# Query from Agent Engine
python3 query_agent_engine.py 

# Deploy to Agentspace
cd ~/code/adk-db-buddy
bash deploy_to_agentspace.sh

# Remove from Agentspace (based on Agent Name in env file; if updated, run the
# source command)
cd ~/code/agent_cleaning
bash remove_from_agentspace.sh


# if session restarts:
source ~/code/agent_cleaning/.venv/bin/activate
source ~/code/agent_cleaning/.env

