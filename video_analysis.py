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
    trick_score: float
    previous_tricks: str
    final_run_score: float
    commentary: str


def analyze_video(local_video_path):
    """
    Analyzes a video from a local path using the Gemini 2.5 Pro model.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in .env file.")

    client = genai.Client(api_key=GEMINI_API_KEY)

    print(f"Analyzing video from local path: {local_video_path}")

    prompt = """You are a professional judge at a skateboarding vert competition. Use the official World Skate vert rules to analyze this video. Identify each trick that a skater performs and note the time stamps for the beggining and ending of the trick. Analyze each trick performed, name it, describe it,give it a score based on the provided criteria, and explain the reasoning for the score. 
    Do not make up trick names and scores if you are not able to identify the trick. Create commentary ouput like your a sports commentary explaining all of these elements. The commentary output should include a score value for the trick and a total run score. Keep track of each trick performed as well as the score for the trick. The total run score should start at 0 on the first trick. After the last trick is performed the final score should be an average of the top 3 tricks performed. In the commentary don't mention the running score until the last trick.

First, record the number of tricks the skateboarder performs. Note each tricks corresponding start and end timestamps.

Then, analyze each trick based on the trick time stamps created in the previous step.

Think through the problem step by step.

<criteria>
1. **Scoring Criteria Assessment**:
   - Difficulty and Variety of tricks
   - Quality of Execution
   - Use of the Vert Ramp
   - Flow and Consistency
   - Avoidance of Repetition
2. **Judge's Score Estimate** (0.00–100.00):
   - Use two decimal places
   - If it is a trick, classify as:
     - 00.01–45.00 = Standard level
     - 45.01–65.00 = Advanced
     - 65.01–85.00 = Expert
     - 85.01–100.00 = Master level
   - If it is a full run, score based on the top three tricks performed

3. **Judge’s Comment**: Explain your score briefly, as if giving notes to a fellow judge or coach.
</criteria>"""

# Here’s a realistic example of how one judge might evaluate a single vert run and arrive at a score using the World Skate scoring system. We’ll walk through each judging criterion and how it contributes to the overall impression score (0.00–100.00).

# <example>
# 🧑‍⚖️ Example: Judge Scoring a Vert Run

# 🎥 Skater’s Run Summary
# 	•	The skater performs a 30-second run.
# 	•	Lands 7 tricks:
# 	1.	Backside air
# 	2.	540 McTwist
# 	3.	Lien to tail
# 	4.	Kickflip Indy
# 	5.	Tailgrab
# 	6.	Varial 540
# 	7.	Ollie 540 (bail)

# ⸻

# ✅ Judging Breakdown

# Criterion	Judge’s Evaluation	Impact on Score
# 1. Difficulty & Variety	Mix of advanced (McTwist, Kickflip Indy) and expert-level (Varial 540); diverse set	High
# 2. Quality of Execution	Most tricks clean; slight wobble on landing for Tailgrab; final trick bailed	Medium-High
# 3. Use of Ramp	Used entire vert ramp, including extensions and tailcoping sections	High
# 4. Flow & Consistency	Good rhythm; brief hesitation after bail but didn’t disrupt prior flow	Medium-High
# 5. Repetition	All tricks unique; no repetition	High


# ⸻

# 🧮 Judge’s Thought Process
# 	•	The skater showed high difficulty, great variety, and used the ramp well.
# 	•	A single bail slightly lowers execution and flow.
# 	•	No trick was repeated, which helps the score stay strong.

# Estimated Score from this Judge: 90.75

# This score fits in the “High level of criteria met” range (70–100), leaning toward the top because of innovation, variety, and overall performance quality.

# ⸻

# 🗒️ Notes the Judge Might Write

# “Excellent mix of difficulty and variety; standout Varial 540. Slight control loss on Tailgrab and bail on final trick prevents it from entering the 95+ range.”

# </example>
# """

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
