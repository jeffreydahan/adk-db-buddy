import os
import sys
import time
from dotenv import load_dotenv
import vertexai
from vertexai import rag
from google.cloud import storage
from google.api_core import exceptions

# Load environment variables
load_dotenv()

# Get environment variables
project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
rag_engine_region = os.getenv("RAG_ENGINE_REGION")
rag_engine_name = os.getenv("RAG_ENGINE_NAME")
rag_source_folder = os.getenv("RAG_SOURCE_FOLDER")
rag_source_bucket = os.getenv("RAG_SOURCE_BUCKET")
rag_source_bucket_folder = os.getenv("RAG_SOURCE_BUCKET_FOLDER")
rag_import_results_bucket_folder = os.getenv("RAG_IMPORT_RESULTS_BUCKET_FOLDER")

def main():
    """Main function to create a RAG engine."""

    # Validate environment variables
    required_env_vars = {
        "GOOGLE_CLOUD_PROJECT_ID": project_id,
        "RAG_ENGINE_REGION": rag_engine_region,
        "RAG_ENGINE_NAME": rag_engine_name,
        "RAG_SOURCE_FOLDER": rag_source_folder,
        "RAG_SOURCE_BUCKET": rag_source_bucket,
        "RAG_SOURCE_BUCKET_FOLDER": rag_source_bucket_folder,
        "RAG_IMPORT_RESULTS_BUCKET_FOLDER": rag_import_results_bucket_folder
    }
    missing_vars = [key for key, value in required_env_vars.items() if not value]
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)

    # Validate RAG source folder
    if not os.path.isdir(rag_source_folder):
        print(f"Error: RAG source folder '{rag_source_folder}' not found.")
        sys.exit(1)

    # Create GCS bucket if it doesn't exist
    storage_client = storage.Client(project=project_id)
    try:
        bucket = storage_client.get_bucket(rag_source_bucket)
        print(f"Bucket {rag_source_bucket} already exists.")
    except exceptions.NotFound:
        print(f"Bucket {rag_source_bucket} not found. Creating bucket.")
        storage_client.create_bucket(rag_source_bucket, location=rag_engine_region)
        print(f"Bucket {rag_source_bucket} created.")

    # Upload files to GCS
    bucket = storage_client.get_bucket(rag_source_bucket)
    gcs_uris = []
    for root, _, files in os.walk(rag_source_folder):
        for file in files:
            local_path = os.path.join(root, file)
            gcs_path = os.path.join(rag_source_bucket_folder, file)
            blob = bucket.blob(gcs_path)
            blob.upload_from_filename(local_path)
            gcs_uris.append(f"gs://{rag_source_bucket}/{gcs_path}")
            print(f"File {local_path} uploaded to gs://{rag_source_bucket}/{gcs_path}.")

    # Initialize Vertex AI
    vertexai.init(project=project_id, location=rag_engine_region)

    # Delete existing corpus to force re-import
    for corpus in rag.list_corpora():
        if corpus.display_name == rag_engine_name:
            print(f"Deleting existing RAG Corpus '{rag_engine_name}'...")
            rag.delete_corpus(name=corpus.name)
            print("Corpus deleted.")
            break

    # Create a new RAG Corpus
    print(f"Creating RAG Corpus '{rag_engine_name}'...")
    rag_corpus = rag.create_corpus(
        display_name=rag_engine_name,
    )
    print(f"RAG Corpus {rag_corpus.name} created successfully.")

    print(f"Importing files into corpus {rag_corpus.name}...")
    response = rag.import_files(
        corpus_name=rag_corpus.name,
        paths=gcs_uris,
    )
    print(response)

if __name__ == "__main__":
    main()