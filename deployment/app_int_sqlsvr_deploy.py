import os
import logging
from dotenv import load_dotenv
from googleapiclient import discovery

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_latest_connector_version(service, project_id, region, provider, connector_name):
    """Gets the latest connector version for a given connector type."""
    parent = f"projects/{project_id}/locations/{region}/providers/{provider}/connectors/{connector_name}"
    request = service.projects().locations().providers().connectors().versions().list(parent=parent)
    response = request.execute()

    versions = response.get("connectorVersions", [])
    if not versions:
        raise Exception(f"No connector versions found for {connector_name}")

    # Sort versions by name (which includes the version number) and get the latest
    latest_version = sorted(versions, key=lambda x: x["name"], reverse=True)[0]
    return latest_version["name"]

def list_providers(service, project_id, region):
    """Lists all available connector providers."""
    parent = f"projects/{project_id}/locations/{region}"
    request = service.projects().locations().providers().list(parent=parent)
    response = request.execute()
    return response.get("providers", [])

def main():
    """Main function to deploy the application integration connector."""
    load_dotenv()

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
    region = os.getenv("GOOGLE_CLOUD_SQLSVR_REGION")
    instance_name = os.getenv("GOOGLE_CLOUD_SQLSVR_INSTANCE_NAME")
    db_name = os.getenv("GOOGLE_CLOUD_SQLSVR_DB")
    user = os.getenv("GOOGLE_CLOUD_SQLSVR_USER")
    password = os.getenv("GOOGLE_CLOUD_SQLSVR_PASSWORD")

    if not all([project_id, region, instance_name, db_name, user, password]):
        logger.error("Missing required environment variables. Please check your .env file.")
        return

    service = discovery.build("connectors", "v1", credentials=None)

    # # List providers to find the correct one
    # try:
    #     providers = list_providers(service, project_id, "global")
    #     logger.info("Available providers:")
    #     for provider in providers:
    #         logger.info(f"- {provider['name']}")
    # except Exception as e:
    #     logger.error(f"Error listing providers: {e}")
    #     return

    # Get the latest connector version for SQL Server
    # The provider for Google-managed connectors is 'microsoft'
    # The connector name for SQL Server is 'sqlserver'
    try:
        connector_version = get_latest_connector_version(service, project_id, "global", "microsoft", "sqlserver")
        logger.info(f"Using connector version: {connector_version}")
    except Exception as e:
        logger.error(f"Error getting latest connector version: {e}")
        return

    connection_id = "sqlserver-connector"
    parent_path = f"projects/{project_id}/locations/{region}"

    connection_body = {
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
                "value": user
            },
            {
                "key": "database",
                "value": db_name
            }
        ],
        "authConfig": {
            "authType": "USER_PASSWORD",
            "credential": {
                "password": {
                    "secretRef": {
                        "secret": os.getenv('GOOGLE_CLOUD_SQLSVR_PASSWORD_SECRET_NAME'),
                        "version": "latest"
                    }
                }
            }
        },
        "serviceAccount": f"service-732115074534@gcp-sa-integrations.iam.gserviceaccount.com"
    }

    try:
        request = service.projects().locations().connections().create(
            parent=parent_path,
            body=connection_body,
            connectionId=connection_id
        )
        response = request.execute()
        logger.info(f"Connection creation initiated. Operation ID: {response['name']}")
    except Exception as e:
        logger.error(f"Error creating connection: {e}")

if __name__ == "__main__":
    main()
