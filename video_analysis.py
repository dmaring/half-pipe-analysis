import os
import time
import datetime
import google.genai as genai
from pydantic import BaseModel
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class Trick(BaseModel):
    trick_name: str
    time_stamp_start: str
    time_stamp_end: str
    description: str
    score: float
    commentary: str


def analyze_video(local_video_path):
    """
    Analyzes a video from a local path using the Gemini 2.5 Pro model.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in .env file.")

    client = genai.Client(api_key=GEMINI_API_KEY)

    print(f"Analyzing video from local path: {local_video_path}")

    prompt = """Your task is to act like a judge for the half-pipe competition. 
    Analyze each trick performed in this skateboarding video, name it, describe it, 
    give it a score, and explain the reasoning for the score. Create commentary ouput like
    your a sports commentary explaining all of these elements. The commentary output should include a score value."""

    print("Uploading file to Gemini...")
    video_file = client.files.upload(file=local_video_path)
    video_file_name = video_file.name

    # Wait for the video to be processed
    while video_file.state == types.FileState.PROCESSING:
        print('.', end='', flush=True)
        time.sleep(10)
        if video_file_name:
            video_file = client.files.get(name=video_file_name)

    if video_file.state == types.FileState.FAILED:
        raise ValueError(f"Video processing failed: {video_file.state}")

    print("\nFile uploaded and processed.")
    
    response = client.models.generate_content(
        model='models/gemini-2.5-pro',
        contents=[prompt, video_file],
        config={
        "response_mime_type": "application/json",
        "response_schema": list[Trick],
    },
    )

    # Clean up the uploaded file from the Gemini service
    if video_file_name:
        client.files.delete(name=video_file_name)
        print(f"Deleted file from Gemini service: {video_file_name}")

    return response.text
