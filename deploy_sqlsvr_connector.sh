#!/bin/bash

# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

if [ -z "$GOOGLE_CLOUD_PROJECT_ID" ]; then
  echo "No GOOGLE_CLOUD_PROJECT_ID variable set in .env file"
  exit 1
fi

if [ -z "$GOOGLE_CLOUD_SQLSVR_REGION" ]; then
  echo "No GOOGLE_CLOUD_SQLSVR_REGION variable set in .env file"
  exit 1
fi

if [ -z "$GOOGLE_CLOUD_SQLSVR_INSTANCE_NAME" ]; then
  echo "No GOOGLE_CLOUD_SQLSVR_INSTANCE_NAME variable set in .env file"
  exit 1
fi

if [ -z "$GOOGLE_CLOUD_SQLSVR_DB" ]; then
  echo "No GOOGLE_CLOUD_SQLSVR_DB variable set in .env file"
  exit 1
fi

if [ -z "$GOOGLE_CLOUD_SQLSVR_USER" ]; then
  echo "No GOOGLE_CLOUD_SQLSVR_USER variable set in .env file"
  exit 1
fi

if [ -z "$GOOGLE_CLOUD_SQLSVR_PASSWORD_SECRET_NAME" ]; then
  echo "No GOOGLE_CLOUD_SQLSVR_PASSWORD_SECRET_NAME variable set in .env file"
  exit 1
fi

PROJECT_ID=$GOOGLE_CLOUD_PROJECT_ID
REGION=$GOOGLE_CLOUD_SQLSVR_REGION
INSTANCE_NAME=$GOOGLE_CLOUD_SQLSVR_INSTANCE_NAME
DB_NAME=$GOOGLE_CLOUD_SQLSVR_DB
DB_USER=$GOOGLE_CLOUD_SQLSVR_USER
PASSWORD_SECRET_NAME=$GOOGLE_CLOUD_SQLSVR_PASSWORD_SECRET_NAME

# Get Project Number
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
if [ -z "$PROJECT_NUMBER" ]; then
  echo "Error: Could not retrieve project number for $PROJECT_ID"
  exit 1
fi

SERVICE_ACCOUNT="service-$PROJECT_NUMBER@gcp-sa-integrations.iam.gserviceaccount.com"

TOKEN=$(gcloud auth print-access-token)

gcloud config set project "$PROJECT_ID"

echo "Assigning roles to Integration Connectors Service Account"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.viewer" \
    --quiet

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet

# Install integrationcli
echo "Installing integrationcli"
curl -L https://raw.githubusercontent.com/GoogleCloudPlatform/application-integration-management-toolkit/main/downloadLatest.sh | sh -
export PATH=$PATH:$HOME/.integrationcli/bin

# Create connector definition file
cat <<EOF > sqlserver-connector.json
{
    "displayName": "My Automated Cloud SQL SQL Server Connection",
    "connectorVersion": "1",
    "configVariables": [
        {
            "key": "host",
            "value": "localhost"
        },
        {
            "key": "port",
            "value": "1433"
        },
        {
            "key": "username",
            "value": "$DB_USER"
        },
        {
            "key": "database",
            "value": "$DB_NAME"
        }
    ],
    "authConfig": {
        "authType": "USER_PASSWORD",
        "credential": {
            "password": {
                "secretRef": {
                    "secret": "$PASSWORD_SECRET_NAME",
                    "version": "latest"
                }
            }
        }
    },
    "serviceAccount": "$SERVICE_ACCOUNT"
}
EOF

echo "Creating SQL Server Integration Connector"
integrationcli connectors apply --file sqlserver-connector.json -p $PROJECT_ID -r $REGION -t $TOKEN -g --wait

echo "SQL Server Integration Connector deployment initiated."
