# Deploys the agent.py root_agent (and all dependent agents)
# to Vertex AI Agent Engine

# Add the project root to the Python path to allow for absolute imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import everything from the agent.py
from db_buddy.agent import root_agent
import vertexai
from vertexai.preview import reasoning_engines
from vertexai import agent_engines

# Helper function to get environment variables
def get_env_var(key):
    value = os.getenv(key)
    if value is None:
        raise ValueError(f"Environment variable '{key}' not found.")
    return value

# Import packages to assist with writing/reading env variables
from dotenv import set_key, load_dotenv, get_key
load_dotenv()

# Set variables from env
project_id=get_env_var("GOOGLE_CLOUD_PROJECT_ID")
staging_bucket="gs://"+get_env_var("GOOGLE_CLOUD_STORAGE_STAGING_BUCKET")
location=get_env_var("GOOGLE_CLOUD_LOCATION")
agent_description=get_env_var("AGENT_DESCRIPTION")
agent_name=get_env_var("AGENT_NAME")

# initialitze vertexai
vertexai.init(
    project=project_id,
    location=location,
    staging_bucket=staging_bucket,
)

requirements_path = "requirements.txt"
with open(requirements_path, "r") as f:
    requirements_list = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]


# Specific environment variables that you want to pass
# to be included with Agent Engine Deployment
env_vars = {
    "GOOGLE_CLOUD_STORAGE_STAGING_BUCKET": staging_bucket,
    "AGENT_DESCRIPTION": agent_description,
    "AGENT_NAME": agent_name,
}

# Upload the ADK Agent to Agent Engine
remote_app = agent_engines.create(
    agent_engine=root_agent,
    requirements=requirements_list,
    display_name=agent_name,
    description=agent_description,
    extra_packages=[
        "db_buddy/agent.py",
        "db_buddy/prompts.py",
        "db_buddy/tools_native.py",
    ],
    env_vars=env_vars
)

print(remote_app.resource_name)

# Set the Agent Engine Agent ID to an env variable for use in the next phase of
# deploying to Agentspace if desired. This script updates the .env file with
# the new resource ID.
dotenv_path = ".env"  # Relative to project root
set_key(dotenv_path, "AGENT_ENGINE_APP_RESOURCE_ID", remote_app.resource_name)
print(f"AGENT_ENGINE_APP_RESOURCE_ID='{remote_app.resource_name}' has been set in {dotenv_path}")

# Verify the key was written correctly to the .env file
print(f"Verifying AGENT_ENGINE_APP_RESOURCE_ID in {dotenv_path}...")
written_value = get_key(dotenv_path, "AGENT_ENGINE_APP_RESOURCE_ID")
if written_value == remote_app.resource_name:
    print(f"Successfully verified AGENT_ENGINE_APP_RESOURCE_ID: {written_value}")
    # Update the current process's environment for consistency.
    os.environ["AGENT_ENGINE_APP_RESOURCE_ID"] = remote_app.resource_name
else:
    print(f"Error: AGENT_ENGINE_APP_RESOURCE_ID could not be verified in {dotenv_path}. Expected '{remote_app.resource_name}', got '{written_value}'")

# now setting the env variable in the current environment for AGENT_ENGINE_APP_RESOURCE_ID
os.environ["AGENT_ENGINE_APP_RESOURCE_ID"] = remote_app.resource_name

# You can see this agent inside of Vertex AI Agent Engine.  You can delete it from
# the Google Cloud Console if desired.  If you get an error, ensure you have
# deleted all sessions in the Agent first.