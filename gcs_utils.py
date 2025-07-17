import os
from google.cloud import storage
from dotenv import load_dotenv

load_dotenv()
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")


def upload_to_gcs(local_path, gcs_folder):
    """Uploads a file to the given GCS bucket and folder."""
    if not GCS_BUCKET_NAME or GCS_BUCKET_NAME == "your-gcs-bucket-name-here":
        raise ValueError("GCS_BUCKET_NAME is not set in the .env file.")

    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET_NAME)
    blob_name = os.path.basename(local_path)
    gcs_path = f"{gcs_folder}/{blob_name}"
    blob = bucket.blob(gcs_path)

    print(f"Uploading {local_path} to gs://{GCS_BUCKET_NAME}/{gcs_path}...")
    blob.upload_from_filename(local_path)
    print("Upload complete.")
    return f"gs://{GCS_BUCKET_NAME}/{gcs_path}"


def download_from_gcs(gcs_uri, local_path):
    """Downloads a file from GCS."""
    client = storage.Client()
    bucket_name, blob_name = gcs_uri.replace("gs://", "").split("/", 1)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.download_to_filename(local_path)
    print(f"Downloaded {gcs_uri} to {local_path}")
