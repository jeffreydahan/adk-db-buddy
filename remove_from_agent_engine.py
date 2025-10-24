import os
import click
import vertexai
import google.auth
from dotenv import load_dotenv, unset_key

load_dotenv()

@click.command()
@click.option(
    "--project",
    default=None,
    help="GCP project ID (defaults to application default credentials)",
)
@click.option(
    "--location",
    default=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
    help="GCP region (defaults to us-central1)",
)
def remove_agent_engine_app(
    project: str | None,
    location: str,
) -> None:
    """Remove the agent engine app from Vertex AI."""

    agent_engine_app_resource_id = os.getenv("AGENT_ENGINE_APP_RESOURCE_ID")

    if not agent_engine_app_resource_id:
        print("Error: AGENT_ENGINE_APP_RESOURCE_ID not found in .env file. Please deploy an agent first.")
        return

    if not project:
        _, project = google.auth.default()

    vertexai.init(project=project, location=location)
    client = vertexai.Client(project=project, location=location)

    print(f"Attempting to delete agent: {agent_engine_app_resource_id}")
    try:
        client.agent_engines.delete(name=agent_engine_app_resource_id)
        print(f"Successfully deleted agent: {agent_engine_app_resource_id}")
        
        # Remove the AGENT_ENGINE_APP_RESOURCE_ID from the .env file
        dotenv_path = ".env"
        set_key(dotenv_path, "AGENT_ENGINE_APP_RESOURCE_ID", "DELETED")
        print(f"Removed AGENT_ENGINE_APP_RESOURCE_ID from {dotenv_path}")

    except Exception as e:
        print(f"Error deleting agent {agent_engine_app_resource_id}: {e}")

if __name__ == "__main__":
    remove_agent_engine_app()
