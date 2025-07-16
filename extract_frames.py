import cv2
import os
import argparse
import tempfile
import shutil
from google.cloud import storage
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

load_dotenv()
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
GCS_FRAMES_OUTPUT_FOLDER = os.getenv("GCS_FRAMES_OUTPUT_FOLDER", "frames")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)  # pylint: disable=no-member

def download_from_gcs(gcs_uri, local_path):
    """Downloads a file from GCS."""
    client = storage.Client()
    bucket_name, blob_name = gcs_uri.replace("gs://", "").split("/", 1)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.download_to_filename(local_path)
    print(f"Downloaded {gcs_uri} to {local_path}")

def upload_dir_to_gcs(local_dir, gcs_bucket_name, gcs_folder):
    """Uploads a directory to a GCS bucket."""
    client = storage.Client()
    bucket = client.bucket(gcs_bucket_name)
    for local_file in os.listdir(local_dir):
        local_path = os.path.join(local_dir, local_file)
        if os.path.isfile(local_path):
            blob_name = f"{gcs_folder}/{local_file}"
            blob = bucket.blob(blob_name)
            blob.upload_from_filename(local_path)
    print(f"Uploaded frames to gs://{gcs_bucket_name}/{gcs_folder}")


def analyze_frame_with_gemini(image_path):
    """Sends an image to the Gemini API and asks for a description."""
    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY not found in .env file. Skipping analysis.")
        return

    print(f"Analyzing frame: {os.path.basename(image_path)}")
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)  # pylint: disable=no-member
        image = Image.open(image_path)
        prompt = "What skateboarding trick is this person doing in this image?"
        response = model.generate_content([prompt, image])
        print(f"  Gemini says: {response.text.strip()}")
    except Exception as e:
        print(f"  Error analyzing frame: {e}")


def extract_frames(video_path, output_dir, interval=60, analyze=False):
    """
    Extracts frames from a video and optionally analyzes them with Gemini.
    """
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)  # pylint: disable=no-member

    frame_count = 0
    saved_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % interval == 0:
            filename = os.path.join(output_dir, f"frame_{saved_count:04}.jpg")
            cv2.imwrite(filename, frame)  # pylint: disable=no-member
            if analyze:
                analyze_frame_with_gemini(filename)
            saved_count += 1
        frame_count += 1

    cap.release()
    print(f"✅ Extracted {saved_count} frames into '{output_dir}'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract frames from a video.")
    parser.add_argument("--local-file", help="Path to a local video file.")
    parser.add_argument("--gcs-uri", help="GCS URI of the video file.")
    parser.add_argument("--interval", type=int, default=30, help="Frame extraction interval.")
    parser.add_argument("--analyze-frames", action="store_true", help="Enable Gemini analysis for each frame.")

    args = parser.parse_args()

    if not GCS_BUCKET_NAME or GCS_BUCKET_NAME == "your-gcs-bucket-name-here":
        print("Please set the GCS_BUCKET_NAME in your .env file.")
        exit()

    temp_dir = tempfile.mkdtemp()
    video_to_process = None
    is_gcs = False

    try:
        if args.local_file:
            video_to_process = args.local_file
        elif args.gcs_uri:
            is_gcs = True
            temp_video_file = os.path.join(temp_dir, os.path.basename(args.gcs_uri))
            download_from_gcs(args.gcs_uri, temp_video_file)
            video_to_process = temp_video_file
        else:
            parser.print_help()
            exit()

        if video_to_process:
            # Create a unique folder name for the frames in GCS
            video_name = os.path.splitext(os.path.basename(video_to_process))[0]
            gcs_frames_folder = f"{GCS_FRAMES_OUTPUT_FOLDER}/{video_name}"

            extract_frames(video_to_process, temp_dir, args.interval, args.analyze_frames)
            if not args.analyze_frames:
                upload_dir_to_gcs(temp_dir, GCS_BUCKET_NAME, gcs_frames_folder)
            else:
                print("\nSkipping GCS upload because --analyze-frames was used.")

    finally:
        print(f"Cleaning up temporary directory: {temp_dir}")
        shutil.rmtree(temp_dir)