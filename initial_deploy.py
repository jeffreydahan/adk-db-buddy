import os
import logging
import time
import pathlib
import subprocess
from dotenv import load_dotenv
from google.cloud import storage
from google.api_core.exceptions import NotFound
import vertexai
from vertexai import rag
from google.cloud import discoveryengine_v1beta as discoveryengine
# Corrected import for SQL Admin API
from googleapiclient import discovery
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_bucket_if_not_exists(project_id, bucket_name, location):
    """Creates a new bucket if it does not exist."""
    storage_client = storage.Client(project=project_id)
    try:
        storage_client.get_bucket(bucket_name)
        logger.info(f"Bucket {bucket_name} already exists.")
    except NotFound:
        logger.info(f"Bucket {bucket_name} not found. Creating new bucket.")
        bucket = storage_client.create_bucket(bucket_name, location=location)
        logger.info(f"Bucket {bucket.name} created in {bucket.location} with storage class {bucket.storage_class}")

def upload_folder_contents(bucket_name, source_folder, destination_prefix=""):
    """Uploads the contents of a folder to a GCS bucket, optionally under a prefix."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    source_path = pathlib.Path(source_folder)

    for file_path in source_path.rglob('*'):
        if file_path.is_file():
            # Create blob path relative to the source folder
            relative_path = file_path.relative_to(source_path).as_posix()
            # Prepend the destination prefix if it exists
            if destination_prefix:
                destination_blob_name = f"{destination_prefix}/{relative_path}"
            else:
                destination_blob_name = relative_path
            blob = bucket.blob(destination_blob_name)
            blob.upload_from_filename(str(file_path))
            logger.info(f"File {file_path} uploaded to {destination_blob_name}.")

def wait_for_instance_to_be_runnable(service, project_id, instance_name):
    """Waits for a Cloud SQL instance to become RUNNABLE."""
    logger.info(f"Waiting for instance '{instance_name}' to be ready...")
    while True:
        try:
            instance_info = service.instances().get(project=project_id, instance=instance_name).execute()
            state = instance_info.get("state")
            logger.info(f"Instance '{instance_name}' is currently in state: {state}")

            if state == "RUNNABLE":
                logger.info(f"Instance '{instance_name}' is now RUNNABLE.")
                return True
            elif state in ["PENDING_CREATE", "MAINTENANCE", "STOPPED", "UNKNOWN_STATE"]:
                logger.info("Instance is not ready yet. Checking again in 60 seconds...")
                time.sleep(60)
            else: # FAILED, SUSPENDED
                logger.error(f"Instance '{instance_name}' is in a non-recoverable state: {state}. Aborting.")
                return False
        except HttpError as e:
            logger.error(f"Error checking instance status: {e}")
            # If we can't even get the instance, something is wrong.
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred while waiting for instance: {e}")
            return False

def wait_for_operation_to_complete(service, project_id, operation_name):
    """Waits for a Cloud SQL operation to complete."""
    logger.info(f"Waiting for operation '{operation_name}' to complete...")
    while True:
        try:
            operation = service.operations().get(project=project_id, operation=operation_name).execute()
            status = operation.get("status")
            logger.info(f"Operation '{operation_name}' is currently in status: {status}")

            if status == "DONE":
                logger.info(f"Operation '{operation_name}' completed successfully.")
                if "error" in operation:
                    logger.error(f"Operation failed with error: {operation['error']}")
                    return False
                return True
            
            time.sleep(10) # Poll every 10 seconds
        except HttpError as e:
            logger.error(f"Error checking operation status: {e}")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred while waiting for operation: {e}")
            return False

def create_postgres_instance_if_not_exists(project_id, instance_name, region):
    """Creates a PostgreSQL instance if it does not exist."""
    # Initialize the Cloud SQL Admin API client
    service = discovery.build("sqladmin", "v1beta4")

    try:
        instance = service.instances().get(project=project_id, instance=instance_name).execute()
        logger.info(f"Cloud SQL instance '{instance_name}' already exists in state: {instance.get('state')}")
        
        settings = instance.get("settings", {})
        database_flags = settings.get("databaseFlags", [])
        
        iam_auth_flag_index = -1
        for i, flag in enumerate(database_flags):
            if flag.get("name") == "cloudsql.iam_authentication":
                iam_auth_flag_index = i
                break

        needs_update = False
        if iam_auth_flag_index != -1:
            # Flag exists, check if it needs to be updated
            if database_flags[iam_auth_flag_index].get("value") != "On":
                database_flags[iam_auth_flag_index]["value"] = "On"
                needs_update = True
        else:
            # Flag doesn't exist, add it
            database_flags.append({"name": "cloudsql.iam_authentication", "value": "On"})
            needs_update = True

        if needs_update:
            logger.info("Enabling IAM database authentication...")
            settings["databaseFlags"] = database_flags
            instance_body = {"settings": settings}
            operation = service.instances().patch(project=project_id, instance=instance_name, body=instance_body).execute()
            logger.info(f"Waiting for instance update to complete... Operation: {operation}")
            if not wait_for_operation_to_complete(service, project_id, operation['name']):
                return False

    except HttpError as e:
        if e.resp.status == 404:
            logger.info(f"Cloud SQL instance {instance_name} not found. Creating new instance.")
            instance_body = {
                "name": instance_name,
                "project": project_id,
                "databaseVersion": "POSTGRES_14",
                "region": region,
                "settings": {
                    "tier": "db-f1-micro",
                    "backupConfiguration": {"enabled": True},
                    "ipConfiguration": {
                        "ipv4Enabled": True,
                        "requireSsl": True,
                    },
                    "databaseFlags": [
                        {
                            "name": "cloudsql.iam_authentication",
                            "value": "On"
                        }
                    ]
                },
            }
            operation = service.instances().insert(project=project_id, body=instance_body).execute()
            logger.info(f"Waiting for Cloud SQL instance {instance_name} creation to complete...")
            logger.info(f"Operation for instance creation: {operation}")
            if not wait_for_operation_to_complete(service, project_id, operation['name']):
                return False
        else:
            logger.error(f"Error checking/creating Cloud SQL instance: {e}")
            raise
    except Exception as e:
        logger.error(f"An unexpected error occurred with Cloud SQL instance: {e}")
        raise
    
    return wait_for_instance_to_be_runnable(service, project_id, instance_name)



def create_postgres_database_if_not_exists(project_id, instance_name, db_name):
    """Creates a PostgreSQL database within an instance if it does not exist."""
    # Initialize the Cloud SQL Admin API client
    service = discovery.build("sqladmin", "v1beta4")

    try:
        service.databases().get(project=project_id, instance=instance_name, database=db_name).execute()
        logger.info(f"Database {db_name} already exists in instance {instance_name}.")
    except HttpError as e:
        if e.resp.status == 404:
            logger.info(f"Database {db_name} not found in instance {instance_name}. Creating new database.")
            database_body = {
                "name": db_name,
                "charset": "UTF8",
                "collation": "en_US.UTF8",
            }
            operation = service.databases().insert(project=project_id, instance=instance_name, body=database_body).execute()
            logger.info(f"Waiting for database {db_name} creation to complete...")
            logger.info(f"Operation for database creation: {operation}")
            wait_for_operation_to_complete(service, project_id, operation['name'])
        elif e.resp.status == 400 and "instance is not running" in str(e.content):
            logger.error(f"Cannot create database '{db_name}' because instance '{instance_name}' is not running. Please start the instance and try again.")
            raise
        else:
            logger.error(f"Error checking/creating database: {e}")
            raise
    except Exception as e:
        logger.error(f"An unexpected error occurred with database: {e}")
        raise

def get_gcloud_user():
    """Gets the currently logged in gcloud user."""
    try:
        command = [
            "gcloud",
            "auth",
            "list",
            "--filter=status:ACTIVE",
            "--format=value(account)",
        ]
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting gcloud user: {e.stderr}")
        raise

def add_iam_policy_binding(project_id, user_email):
    """Adds the Cloud SQL Admin role to the user."""
    logger.info(f"Adding Cloud SQL Admin role to {user_email}...")
    command = [
        "gcloud",
        "projects",
        "add-iam-policy-binding",
        project_id,
        f"--member=user:{user_email}",
        "--role=roles/cloudsql.admin",
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        logger.info("Cloud SQL Admin role added successfully.")
    except subprocess.CalledProcessError as e:
        # It's possible the policy binding already exists, which would cause an error.
        # We can safely ignore this.
        if "already exists" in e.stderr:
            logger.info("IAM policy binding already exists.")
        else:
            logger.error(f"Error adding IAM policy binding: {e.stderr}")
            raise

def add_iam_user_to_instance(project_id, instance_name, user_email):
    """Adds an IAM user to the Cloud SQL instance."""
    logger.info(f"Adding IAM user {user_email} to instance {instance_name}...")
    command = [
        "gcloud",
        "sql",
        "users",
        "create",
        user_email,
        f"--instance={instance_name}",
        "--type=CLOUD_IAM_USER",
        f"--project={project_id}",
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        logger.info(f"IAM user {user_email} added successfully.")
    except subprocess.CalledProcessError as e:
        if "already exists" in e.stderr:
            logger.info(f"IAM user {user_email} already exists.")
        else:
            logger.error(f"Error adding IAM user: {e.stderr}")
            raise


def create_RAG_corpus(rag_corpus_name):
    """Creates a RAG corpus if it does not already exist."""
    # Check if corpus already exists
    try:
        existing_corpora = rag.list_corpora()
        for corpus in existing_corpora:
            if corpus.display_name == rag_corpus_name:
                logger.info(f"RAG corpus '{rag_corpus_name}' already exists.")
                return corpus.name
    except Exception as e:
        logger.warning(f"Could not check for existing RAG corpora, proceeding with creation. Error: {e}")


    logger.info(f"Creating RAG corpus '{rag_corpus_name}'...")
    
    # Configure embedding model
    embedding_model_config = rag.RagEmbeddingModelConfig(
        vertex_prediction_endpoint=rag.VertexPredictionEndpoint(
            publisher_model="publishers/google/models/text-embedding-005"
        )
    )

    backend_config = rag.RagVectorDbConfig(
        rag_embedding_model_config=embedding_model_config
    )

    # Create the corpus
    corpus = rag.create_corpus(
        display_name=rag_corpus_name,
        backend_config=backend_config,
    )
    logger.info(f"RAG corpus '{rag_corpus_name}' created successfully with name: {corpus.name}")
    return corpus.name

def ingest_files(rag_corpus_name, paths):
    logger.info(f"Checking for existing files in corpus {rag_corpus_name}...")
    existing_files = rag.list_files(corpus_name=rag_corpus_name)
    existing_file_names = [f.display_name for f in existing_files]
    logger.info(f"Found {len(existing_file_names)} existing files.")

    files_to_upload = []
    for path in paths:
        file_name = os.path.basename(path)
        if file_name not in existing_file_names:
            files_to_upload.append(path)

    if not files_to_upload:
        logger.info("All files already exist in the corpus. Nothing to ingest.")
        return

    logger.info(f"Ingesting {len(files_to_upload)} new files...")
    transformation_config = rag.TransformationConfig(
        chunking_config=rag.ChunkingConfig(
            chunk_size=512,
            chunk_overlap=100,
        ),
    )

    rag.import_files(
        rag_corpus_name,
        files_to_upload,
        transformation_config=transformation_config,  # Optional
        max_embedding_requests_per_min=1000,  # Optional
    )

    # List the files in the rag corpus
    rag.list_files(rag_corpus_name)



def main():
    """Main function to create bucket, upload files, create data store, import documents, create Postgres instance and database."""
    load_dotenv()

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
    gcs_bucket_name = os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET_DOCS")
    gcs_location = os.getenv("GOOGLE_CLOUD_STORAGE_REGION")
    postgres_instance_name = os.getenv("GOOGLE_CLOUD_POSTGRES_INSTANCE")
    postgres_db_name = os.getenv("GOOGLE_CLOUD_POSTGRES_DB")
    postgres_region = os.getenv("GOOGLE_CLOUD_POSTGRES_REGION") 
    gcs_bucket_postgres_folder=os.getenv("GOOGLE_CLOUD_POSTGRES_DOC_FOLDER")
    rag_corpus_name=os.getenv("GOOGLE_CLOUD_RAG_ENGINE_CORPUS_NAME")
    
    if not all([project_id, gcs_bucket_name, gcs_location,
                postgres_instance_name, postgres_db_name, postgres_region, 
                gcs_bucket_postgres_folder, rag_corpus_name]):
        logger.error("Missing required environment variables. Please check your .env file.")
        return

    gcloud_user = None
    try:
        gcloud_user = get_gcloud_user()
    except Exception as e:
        logger.error(f"Could not get gcloud user: {e}")

    if gcloud_user:
        try:
            add_iam_policy_binding(project_id, gcloud_user)
        except Exception as e:
            logger.error(f"Could not add IAM policy binding: {e}")

    # GCS Bucket and Document Upload
    create_bucket_if_not_exists(project_id, gcs_bucket_name, gcs_location)
    upload_folder_contents(gcs_bucket_name, "documentation/postgres", gcs_bucket_postgres_folder)
    
    # PostgreSQL Instance and Database
    logger.info("Creating PostgreSQL instance...")
    instance_ready = create_postgres_instance_if_not_exists(project_id, postgres_instance_name, postgres_region)
    
    if instance_ready:
        if gcloud_user:
            try:
                add_iam_user_to_instance(project_id, postgres_instance_name, gcloud_user)
            except Exception as e:
                logger.error(f"Could not add IAM user to instance: {e}")

        logger.info("Creating PostgreSQL database...")
        create_postgres_database_if_not_exists(project_id, postgres_instance_name, postgres_db_name)
    else:
        logger.error(f"Could not proceed to database creation because instance '{postgres_instance_name}' is not ready.")

    # Create Rag Engine Corpus
    logger.info("Creating RAG corpus...")
    rag_corpus_full_name = create_RAG_corpus(rag_corpus_name)

    # Ingest data into RAG
    storage_client = storage.Client()
    bucket = storage_client.bucket(gcs_bucket_name)
    blobs = bucket.list_blobs(prefix=gcs_bucket_postgres_folder)
    paths = [f"gs://{gcs_bucket_name}/{blob.name}" for blob in blobs if blob.name.endswith('.pdf')]
    ingest_files(rag_corpus_full_name, paths)

if __name__ == "__main__":
    main()