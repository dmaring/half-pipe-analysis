import argparse
import os
from gcs_utils import upload_to_gcs, download_from_gcs
from video_analysis import analyze_video
from video_editor import create_commentary_video, add_score_overlay
from dotenv import load_dotenv

load_dotenv()
GCS_SOURCE_VIDEO_FOLDER = os.getenv("GCS_SOURCE_VIDEO_FOLDER", "videos")


def main():
    """
    Main function to orchestrate the video analysis.
    """
    parser = argparse.ArgumentParser(
        description="Analyze skateboarding videos with Gemini 2.5 Pro."
    )
    parser.add_argument("--local-file", help="Path to a local video file to analyze.")
    parser.add_argument(
        "--gcs-uri",
        help="GCS URI of a video to analyze (e.g., gs://bucket/video.mp4).",
    )
    parser.add_argument(
        "--with-commentary",
        action="store_true",
        help="Generate a new video with commentary.",
    )
    parser.add_argument(
        "--score-overlay-only",
        action="store_true",
        help="Generate a new video with only the final score overlay.",
    )
    parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="Only generate the analysis JSON file.",
    )
    parser.add_argument(
        "--clean-temp",
        action="store_true",
        help="Remove all files from the temp directory.",
    )

    args = parser.parse_args()

    local_video_path = None
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)

    try:
        if args.clean_temp:
            print("Cleaning up temporary directory...")
            for file in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, file))
            print("Temporary directory cleaned.")
            return

        if args.local_file:
            local_video_path = args.local_file
            video_name = os.path.splitext(os.path.basename(local_video_path))[0]
        elif args.gcs_uri:
            video_name = os.path.splitext(os.path.basename(args.gcs_uri))[0]
            local_video_path = os.path.join(temp_dir, os.path.basename(args.gcs_uri))
            if not os.path.exists(local_video_path):
                print(f"Downloading {args.gcs_uri} to {local_video_path}...")
                download_from_gcs(args.gcs_uri, local_video_path)
                print("Download complete.")
        else:
            parser.print_help()
            return

        analysis_file_path = os.path.join(temp_dir, f"{video_name}_analysis.json")

        if os.path.exists(analysis_file_path):
            print(f"Using cached analysis from {analysis_file_path}")
            with open(analysis_file_path, 'r') as f:
                analysis_result = f.read()
        else:
            print("\nStarting video analysis...")
            analysis_result = analyze_video(local_video_path)
            with open(analysis_file_path, 'w') as f:
                f.write(analysis_result)
            print(f"\nAnalysis saved to {analysis_file_path}")

        print("\n--- Analysis Result ---")
        print(analysis_result)
        print("-----------------------")

        if args.analyze_only:
            return

        if args.with_commentary:
            print("\nGenerating video with commentary...")
            output_video_path = os.path.join(temp_dir, f"{video_name}_commentary.mp4")
            create_commentary_video(local_video_path, analysis_result, output_video_path, temp_dir)
            print(f"\nCommentary video saved to: {output_video_path}")

            try:
                gcs_uri = upload_to_gcs(output_video_path, "output")
                print(f"Uploaded commentary video to: {gcs_uri}")
            except ValueError as e:
                print(f"Error uploading commentary video: {e}")
        elif args.score_overlay_only:
            print("\nAdding score overlay to video...")
            output_video_path = os.path.join(temp_dir, f"{video_name}_score_overlay.mp4")
            add_score_overlay(local_video_path, analysis_result, output_video_path)
            print(f"\nVideo with score overlay saved to: {output_video_path}")

            try:
                gcs_uri = upload_to_gcs(output_video_path, "output")
                print(f"Uploaded video with score overlay to: {gcs_uri}")
            except ValueError as e:
                print(f"Error uploading video with score overlay: {e}")

    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
