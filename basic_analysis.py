import argparse
import os
from google.cloud import videointelligence, storage
from dotenv import load_dotenv

load_dotenv()
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
GCS_SOURCE_VIDEO_FOLDER = os.getenv("GCS_SOURCE_VIDEO_FOLDER", "videos")

def upload_to_gcs(local_path, gcs_bucket_name, gcs_folder):
    """Uploads a file to the given GCS bucket and folder."""
    client = storage.Client()
    bucket = client.bucket(gcs_bucket_name)
    blob_name = os.path.basename(local_path)
    gcs_path = f"{gcs_folder}/{blob_name}"
    blob = bucket.blob(gcs_path)

    print(f"Uploading {local_path} to gs://{gcs_bucket_name}/{gcs_path}...")
    blob.upload_from_filename(local_path)
    print("Upload complete.")
    return f"gs://{gcs_bucket_name}/{gcs_path}"

def analyze_video_gcp(video_uri):
    client = videointelligence.VideoIntelligenceServiceClient()
    features = [videointelligence.Feature.LABEL_DETECTION]

    operation = client.annotate_video(
        request={"features": features, "input_uri": video_uri}
    )
    print(f"Processing video {video_uri}...")
    result = operation.result(timeout=600)

    if not result or not result.annotation_results:
        print("No annotations found.")
        return

    annotations = result.annotation_results[0]

    for label in annotations.segment_label_annotations:
        print(f"Label: {label.entity.description}")
        for segment in label.segments:
            start = segment.segment.start_time_offset.total_seconds()
            end = segment.segment.end_time_offset.total_seconds()
            print(f"  Segment: {start:.2f}s to {end:.2f}s")

    for label in annotations.shot_label_annotations:
        print(f"Shot Label: {label.entity.description}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze videos with Google Cloud Video Intelligence API.")
    parser.add_argument("--local-file", help="Path to a local MP4 file to analyze.")
    parser.add_argument("--gcs-uri", nargs='+', help="One or more GCS URIs of videos to analyze (e.g., gs://bucket/video.mp4).")

    args = parser.parse_args()

    if args.local_file:
        if not GCS_BUCKET_NAME or GCS_BUCKET_NAME == "your-gcs-bucket-name-here":
            print("Please set the GCS_BUCKET_NAME in your .env file.")
        else:
            gcs_uri = upload_to_gcs(args.local_file, GCS_BUCKET_NAME, GCS_SOURCE_VIDEO_FOLDER)
            analyze_video_gcp(gcs_uri)

    if args.gcs_uri:
        for uri in args.gcs_uri:
            analyze_video_gcp(uri)

    if not args.local_file and not args.gcs_uri:
        print("Please provide a local file or a GCS URI to analyze.")
        parser.print_help()