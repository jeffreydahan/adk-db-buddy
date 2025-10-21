from dotenv import load_dotenv
import vertexai.agent_engines
import os
from google.adk.agents import Agent
import vertexai
import asyncio

# Helper function to get environment variables
load_dotenv()
def get_env_var(key):
    value = os.getenv(key)
    if value is None:
        raise ValueError(f"Environment variable '{key}' not found.")
    return value


async def main():
    # Get environment variables
    project_id=get_env_var("GOOGLE_CLOUD_PROJECT_ID")
    location=get_env_var("GOOGLE_CLOUD_LOCATION")

    # Use the consistent staging bucket environment variable name
    # and ensure it has the 'gs://' prefix for vertexai.init()
    staging_bucket_name_from_env = get_env_var("GOOGLE_CLOUD_STORAGE_STAGING_BUCKET")
    if not staging_bucket_name_from_env.startswith("gs://"):
        staging_bucket = f"gs://{staging_bucket_name_from_env}"
    else:
        staging_bucket = staging_bucket_name_from_env

    dotenv_path = "adk-db-buddy/.env"  # Relative to project root
    if not dotenv_path: # If .env is not found, default to creating one in the current directory
        print(f"dotenv_path does not exist: {dotenv_path}")
    load_dotenv(dotenv_path=dotenv_path, override=True) # Force reload from the .env file
    agent_engine_id = os.getenv("AGENT_ENGINE_APP_RESOURCE_ID")

    # initialitze vertexai
    vertexai.init(
        project=project_id,
        location=location,
        staging_bucket=staging_bucket,
    )

    remote_app = vertexai.agent_engines.get(agent_engine_id)

    user_id = "u_458"

    remote_session = await remote_app.async_create_session(user_id=user_id)
    print("Created session:")
    print(remote_session)

    print("\nQuerying agent with message...")
    print(f"User ID: u_456")
    print(f"Session ID: {remote_session['id']}")
    message = "what car models are recommended for snowy weather conditions?"
    print(f"Message: {message}")

    print("\nStreaming responses:")
    async for event in remote_app.async_stream_query(
        user_id="u_456",
        session_id=remote_session["id"],
        message=message,
        #message="please list the average tip by day for nyc taxi rides.  Also include the weather for each day and recommend a car make and model based upon the weather conditions.",
    ):
        print(event)

if __name__ == "__main__":
    asyncio.run(main())
