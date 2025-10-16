#!/bin/bash

# Load environment variables from .env file
if [ -f ../.env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# --- Configuration ---
# Ensure these environment variables are set in your .env file or directly in your shell
# GOOGLE_CLOUD_PROJECT_ID="your-project-id"
# GOOGLE_CLOUD_SQLSVR_REGION="your-instance-region" # e.g., us-central1
# GOOGLE_CLOUD_SQLSVR_INSTANCE_NAME="your-sql-server-instance-name"

# Check if required environment variables are set
if [ -z "$GOOGLE_CLOUD_PROJECT_ID" ] || [ -z "$GOOGLE_CLOUD_SQLSVR_REGION" ] || [ -z "$GOOGLE_CLOUD_SQLSVR_INSTANCE_NAME" ]; then
    echo "Error: Missing one or more required environment variables."
    echo "Please ensure GOOGLE_CLOUD_PROJECT_ID, GOOGLE_CLOUD_SQLSVR_REGION, and GOOGLE_CLOUD_SQLSVR_INSTANCE_NAME are set in your .env file."
    exit 1
fi

INSTANCE_CONNECTION_NAME="${GOOGLE_CLOUD_PROJECT_ID}:${GOOGLE_CLOUD_SQLSVR_REGION}:${GOOGLE_CLOUD_SQLSVR_INSTANCE_NAME}"
PROXY_EXECUTABLE="./cloud_sql_proxy"

# 1. Download the Cloud SQL Auth Proxy
if [ ! -f "$PROXY_EXECUTABLE" ]; then
    echo "Downloading Cloud SQL Auth Proxy..."
    curl -o "$PROXY_EXECUTABLE" https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64
    if [ $? -ne 0 ]; then
        echo "Error: Failed to download Cloud SQL Auth Proxy."
        exit 1
    fi
    chmod +x "$PROXY_EXECUTABLE"
fi

# 2. Enable Cloud SQL Admin API
gcloud services enable sqladmin.googleapis.com --project="$GOOGLE_CLOUD_PROJECT_ID"
if [ $? -ne 0 ]; then
    echo "Error: Failed to enable Cloud SQL Admin API. Please ensure gcloud CLI is authenticated and has permissions."
    exit 1
fi

# 3. Run the proxy with IAM database authentication enabled
"$PROXY_EXECUTABLE" -instances="$INSTANCE_CONNECTION_NAME"=tcp:1433 &