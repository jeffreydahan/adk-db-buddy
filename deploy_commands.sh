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


# Deploy to Agent Engine
cd ~/code/adk-db-buddy
source .env
python3 deploy_to_agent_engine.py
echo $AGENT_ENGINE_APP_RESOURCE_ID

# Query from Agent Engine
python3 adk-db-buddy/query_agent_engine.py 

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

# redeploy cloud run with new IP:
RTSP_IP_ADDRESS="$(curl -s icanhazip.com)" #set the new IP address
echo $RTSP_IP_ADDRESS
sed -i.bak "s/^RTSP_IP_ADDRESS=.*/RTSP_IP_ADDRESS=\"${RTSP_IP_ADDRESS}\"/" .env # update env file
create_or_update_secret "rtsp-ip-address" "$RTSP_IP_ADDRESS" # update the secret
gcloud run deploy camera-tool-svc \
  --image "$GOOGLE_CLOUD_LOCATION-docker.pkg.dev/$GOOGLE_CLOUD_PROJECT/$GOOGLE_CLOUD_ARTIFACT_REPO/camera-tool-image:latest" \
  --platform managed \
  --region "$GOOGLE_CLOUD_LOCATION" \
  --no-allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT"

# Test cloud run
curl -X POST "https://camera-tool-svc-732115074534.us-central1.run.app" \
-H "Authorization: bearer $(gcloud auth print-identity-token)" \
-H "Content-Type: application/json" \
-d '{
  "room": "demobooth"
}'

