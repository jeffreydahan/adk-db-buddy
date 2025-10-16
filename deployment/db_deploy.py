import os
import logging
import time
import subprocess
from dotenv import load_dotenv
from google.cloud import storage
from google.api_core.exceptions import NotFound
from googleapiclient import discovery
from googleapiclient.errors import HttpError
import argparse


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

def create_db_instance_if_not_exists(project_id, instance_name, region, db_type, db_version):
    f"""Creates a {db_type} instance if it does not exist."""
    # Initialize the Cloud SQL Admin API client
    service = discovery.build("sqladmin", "v1beta4")

    try:
        instance = service.instances().get(project=project_id, instance=instance_name).execute()
        logger.info(f"Cloud SQL instance '{instance_name}' already exists in state: {instance.get('state')}")
        
        settings = instance.get("settings", {})
        database_flags = settings.get("databaseFlags", [])
        
        if db_type != "sqlsvr":
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
                "databaseVersion": db_version,
                "region": region,
                "settings": {
                    "backupConfiguration": {"enabled": True},
                    "ipConfiguration": {
                        "ipv4Enabled": True,
                        "requireSsl": True,
                    },
                },
            }

            if db_type == "sqlsvr":
                tier = os.getenv("GOOGLE_CLOUD_SQLSVR_INSTANCE_TIER")
                password = os.getenv("GOOGLE_CLOUD_SQLSVR_PASSWORD")

                if not all([tier, password]):
                    logger.error("Missing GOOGLE_CLOUD_SQLSVR_INSTANCE_TIER or GOOGLE_CLOUD_SQLSVR_PASSWORD for sqlsvr.")
                    return False

                instance_body["settings"]["tier"] = tier
                instance_body["rootPassword"] = password
            if db_type == "postgres":
                # Add databaseFlags only for non-sqlsvr types
                instance_body["settings"]["databaseFlags"] = [
                    {
                        "name": "cloudsql.iam_authentication",
                        "value": "On"
                    }
                ]
                instance_body["settings"]["tier"] = "db-f1-micro"
            print(instance_body)
            print(instance_body)
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

def create_database_if_not_exists(project_id, instance_name, db_name, db_type):
    f"""Creates a {db_type} database within an instance if it does not exist."""
    # Initialize the Cloud SQL Admin API client
    service = discovery.build("sqladmin", "v1beta4")

    try:
        service.databases().get(project=project_id, instance=instance_name, database=db_name).execute()
        logger.info(f"Database {db_name} already exists in instance {instance_name}.")
        return True
    except HttpError as e:
        if e.resp.status == 404:
            logger.info(f"Database {db_name} not found in instance {instance_name}. Creating new database.")
            database_body = {
                "name": db_name,
            }
            if db_type != "sqlsvr":
                database_body["charset"] = "UTF8"
                database_body["collation"] = "en_US.UTF8"
            
            operation = service.databases().insert(project=project_id, instance=instance_name, body=database_body).execute()
            logger.info(f"Waiting for database {db_name} creation to complete...")
            logger.info(f"Operation for database creation: {operation}")
            if not wait_for_operation_to_complete(service, project_id, operation['name']):
                logger.error(f"Database creation operation for '{db_name}' failed.")
                return False

            # Validation step
            try:
                time.sleep(5) # Give a moment for the API to be consistent
                service.databases().get(project=project_id, instance=instance_name, database=db_name).execute()
                logger.info(f"Successfully validated that database '{db_name}' was created.")
                return True
            except HttpError as e_validate:
                logger.error(f"Validation failed. Database '{db_name}' not found after creation attempt. Error: {e_validate}")
                return False
        elif e.resp.status == 400 and "instance is not running" in str(e.content):
            logger.error(f"Cannot create database '{db_name}' because instance '{instance_name}' is not running. Please start the instance and try again.")
            raise
        else:
            logger.error(f"Error checking/creating database: {e}")
            raise
    except Exception as e:
        logger.error(f"An unexpected error occurred with database: {e}")
        raise
    return False

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

def main():
    """Main function to create bucket, upload files, create data store, import documents, create Postgres instance and database."""
    parser = argparse.ArgumentParser(description="Deploy back end services.")
    parser.add_argument(
        "db_type",
        choices=["postgres", "sqlsvr", "mysql", "bq"],
        help="The type of database to deploy. Choose from: postgres, sqlserver, mysql, bq",
    )
    args = parser.parse_args()
    db_type=args.db_type
    print(f"Deploying dabase back end for {args.db_type}")
    
    logger.info(f"Deploying for database type: {db_type}")
    load_dotenv()

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
    gcs_bucket_name = os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET_DOCS")
    gcs_location = os.getenv("GOOGLE_CLOUD_STORAGE_REGION")
    
    db_type_upper=db_type.upper()
    db_version=os.getenv(f"GOOGLE_CLOUD_{db_type_upper}_VERSION")
    db_instance_name = os.getenv(f"GOOGLE_CLOUD_{db_type_upper}_INSTANCE_NAME")
    db_name = os.getenv(f"GOOGLE_CLOUD_{db_type_upper}_DB")
    db_region = os.getenv(f"GOOGLE_CLOUD_{db_type_upper}_REGION") 
    
    print("Environment variables:")
    print(f"GOOGLE_CLOUD_PROJECT_ID: {project_id}")
    print(f"GOOGLE_CLOUD_STORAGE_BUCKET_DOCS: {gcs_bucket_name}")
    print(f"GOOGLE_CLOUD_STORAGE_REGION: {gcs_location}")
    print(f"GOOGLE_CLOUD_{db_type_upper}_VERSION: {db_version}")
    print(f"GOOGLE_CLOUD_{db_type_upper}_INSTANCE_NAME: {db_instance_name}")
    print(f"GOOGLE_CLOUD_{db_type_upper}_DB: {db_name}")
    print(f"GOOGLE_CLOUD_{db_type_upper}_REGION: {db_region}")
    

    if not all([project_id, gcs_bucket_name, gcs_location,
                db_instance_name, db_name, db_region, ]):
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

    # DB Instance and Database
    logger.info(f"Creating {db_type} instance...")
    instance_ready = create_db_instance_if_not_exists(project_id, db_instance_name, db_region, db_type, db_version)
    
    if instance_ready:
        if gcloud_user and db_type != "sqlsvr":
            try:
                add_iam_user_to_instance(project_id, db_instance_name, gcloud_user)
            except Exception as e:
                logger.error(f"Could not add IAM user to instance: {e}")

        logger.info(f"Creating {db_type} database...")
        db_created = create_database_if_not_exists(project_id, db_instance_name, db_name, db_type)
        if not db_created:
            logger.error(f"Failed to create database '{db_name}'. Aborting further steps.")
            return
    else:
        logger.error(f"Could not proceed to database creation because instance '{db_instance_name}' is not ready.")

if __name__ == "__main__":
    main()