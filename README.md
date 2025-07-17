# Half-Pipe Analysis

This project analyzes skateboarding videos from a half-pipe competition using Google's Gemini 2.5 Pro multimodal capabilities. It can analyze videos from a local file or a Google Cloud Storage (GCS) bucket.

## Architecture

The project is structured as follows:

-   `main.py`: The entry point for the application. It handles argument parsing and orchestrates the analysis workflow.
-   `video_analysis.py`: Contains the core logic for analyzing videos with the Gemini 2.5 Pro model.
-   `gcs_utils.py`: Provides utility functions for interacting with Google Cloud Storage, such as uploading and downloading files.
-   `extract_frames.py`: (Optional) This script can be used to extract frames from a video for separate analysis, but it is not part of the main analysis workflow.

## Setup

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-repo/half-pipe-analysis.git
    cd half-pipe-analysis
    ```

2.  **Create a virtual environment and install dependencies:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Set up your environment variables:**

    Create a `.env` file in the root of the project and add the following variables:

    ```
    GCS_BUCKET_NAME="your-gcs-bucket-name"
    GEMINI_API_KEY="your-gemini-api-key"
    ```

    -   `GCS_BUCKET_NAME`: The name of your Google Cloud Storage bucket where videos will be uploaded.
    -   `GEMINI_API_KEY`: Your API key for the Gemini API.

## Usage

You can analyze a video from a local file or a GCS URI.

### Analyze a Local Video

To analyze a local video file, use the `--local-file` argument:

```bash
python main.py --local-file /path/to/your/video.mp4
```

The script will upload the video to your GCS bucket and then analyze it.

### Analyze a Video from GCS

To analyze a video that is already in a GCS bucket, use the `--gcs-uri` argument:

```bash
python main.py --gcs-uri gs://your-gcs-bucket-name/videos/your-video.mp4
```

The script will download the video to a temporary local file and then analyze it.

### Generate a Video with Commentary

To generate a new video with commentary, add the `--with-commentary` flag to either of the above commands.

```bash
python main.py --local-file /path/to/your/video.mp4 --with-commentary
```

or

```bash
python main.py --gcs-uri gs://your-gcs-bucket-name/videos/your-video.mp4 --with-commentary
```

This will create a new video file with `_commentary.mp4` appended to the original filename.

### Keep Temporary Files

To keep the temporary audio and video files for debugging, add the `--keep-temp-files` flag:

```bash
python main.py --local-file /path/to/your/video.mp4 --with-commentary --keep-temp-files
```

## Example

```bash
python main.py --local-file test-video.mp4 --with-commentary
```

### Example Output

```
Uploading test-video.mp4 to gs://your-gcs-bucket-name/videos/test-video.mp4...
Upload complete.

Starting video analysis...
.
--- Analysis Result ---
**Trick 1: Ollie**
- **Description:** The skater jumps into the air with the board seemingly stuck to their feet.
- **Score:** 7/10
- **Reasoning:** Good height and clean execution, but the landing was slightly off-balance.

**Trick 2: Kickflip**
- **Description:** The skater kicks the board, causing it to rotate 360 degrees along its longitudinal axis.
- **Score:** 8.5/10
- **Reasoning:** Excellent rotation and control. The board was caught cleanly, and the landing was smooth.
-----------------------

Generating video with commentary...
Generating audio for: 'Ollie. The skater jumps into the air with the board seemingly stuck to their feet.. Score: 7/10. Reasoning: Good height and clean execution, but the landing was slightly off-balance.'
Audio saved to temp_audio_0.wav
Generating audio for: 'Kickflip. The skater kicks the board, causing it to rotate 360 degrees along its longitudinal axis.. Score: 8.5/10. Reasoning: Excellent rotation and control. The board was caught cleanly, and the landing was smooth.'
Audio saved to temp_audio_1.wav

Commentary video saved to: test-video_commentary.mp4
```