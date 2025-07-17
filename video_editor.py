import json
import os
import ffmpeg
from tts_utils import generate_commentary_audio
from video_analysis import Trick

def create_commentary_video(source_video_path, analysis_json, output_video_path, temp_dir):
    """
    Creates a new video with commentary overlaid on the original video.
    """
    try:
        tricks_data = json.loads(analysis_json)
        tricks = [Trick(**trick) for trick in tricks_data]
        print(f"Tricks JSON: \n{tricks}")
    except (json.JSONDecodeError, TypeError) as e:
        print(f"Error parsing analysis JSON: {e}")
        return

    if not tricks:
        print("No tricks found in the analysis text.")
        return

    temp_audio_files = []
    video_streams = []
    audio_streams = []
    last_end_time = 0

    # Get the original video's audio stream
    original_audio = ffmpeg.input(source_video_path)['a']

    for i, trick in enumerate(tricks):
        # Generate commentary audio for the trick
        audio_filename = os.path.join(temp_dir, f"temp_audio_{i}.wav")
        if not os.path.exists(audio_filename):
            generate_commentary_audio(trick.commentary, audio_filename)
        temp_audio_files.append(audio_filename)
        commentary_audio = ffmpeg.input(audio_filename)['a']

        # Get the end time of the trick
        time_parts = list(map(int, trick.time_stamp_end.split(':')))
        if len(time_parts) == 3:
            h, m, s = time_parts
            trick_end_time = h * 3600 + m * 60 + s
        elif len(time_parts) == 2:
            m, s = time_parts
            trick_end_time = m * 60 + s
        else:
            raise ValueError(f"Invalid timestamp format: {trick.time_stamp_end}")

        # Get the duration of the commentary audio
        audio_probe = ffmpeg.probe(audio_filename)
        audio_duration = float(audio_probe['format']['duration'])

        # Add the video segment for the trick
        video_streams.append(
            ffmpeg.input(source_video_path).trim(start=last_end_time, end=trick_end_time).setpts('PTS-STARTPTS')
        )
        
        # Add a "paused" frame at the end of the trick
        temp_frame_path = os.path.join(temp_dir, f"temp_frame_{i}.jpg")
        ffmpeg.input(source_video_path, ss=trick_end_time).output(temp_frame_path, vframes=1).run(overwrite_output=True)
        
        paused_clip = ffmpeg.input(temp_frame_path, loop=1, t=audio_duration)
        video_streams.append(paused_clip['v'])
        
        # Add the original audio segment for the trick
        audio_streams.append(
            original_audio.filter('atrim', start=last_end_time, end=trick_end_time).filter('asetpts', 'PTS-STARTPTS')
        )
        
        # Add the commentary audio
        audio_streams.append(commentary_audio)
        

        last_end_time = trick_end_time

    # Add the remainder of the video and audio
    # Get the final score from the last trick
    final_score = tricks[-1].final_run_score
    score_text = f"Final Score: {final_score}"

    # Add the remainder of the video with the score overlay
    remainder_video = (
        ffmpeg.input(source_video_path)
        .trim(start=last_end_time)
        .setpts("PTS-STARTPTS")
        .drawtext(
            text=score_text,
            x="w-tw-10",
            y="h-th-10",
            fontsize=48,
            fontcolor="white",
            box=1,
            boxcolor="black@0.5",
            boxborderw=5,
            enable="between(t,1,6)",  # Show for 5 seconds, 1 second after the last trick
        )
    )
    video_streams.append(remainder_video)
    audio_streams.append(
        original_audio.filter("atrim", start=last_end_time).filter(
            "asetpts", "PTS-STARTPTS"
        )
    )

    # Concatenate all video and audio streams
    final_video = ffmpeg.concat(*video_streams, v=1, a=0)
    final_audio = ffmpeg.concat(*audio_streams, v=0, a=1)

    # Combine the final video and audio
    ffmpeg.output(final_video, final_audio, output_video_path).run(overwrite_output=True)

    # Clean up temporary audio files


def add_score_overlay(source_video_path, analysis_json, output_video_path):
    """
    Adds a final score overlay to the video without commentary.
    """
    try:
        tricks_data = json.loads(analysis_json)
        tricks = [Trick(**trick) for trick in tricks_data]
    except (json.JSONDecodeError, TypeError) as e:
        print(f"Error parsing analysis JSON: {e}")
        return

    if not tricks:
        print("No tricks found in the analysis text.")
        return

    # Get video duration
    probe = ffmpeg.probe(source_video_path)
    duration = float(probe["format"]["duration"])
    overlay_start_time = duration - 5

    final_score = tricks[-1].final_run_score
    score_text = f"Final Score: {final_score}"

    video_input = ffmpeg.input(source_video_path)
    video_with_overlay = video_input.video.drawtext(
        text=score_text,
        x="w-tw-10",
        y="h-th-10",
        fontsize=48,
        fontcolor="white",
        box=1,
        boxcolor="black@0.5",
        boxborderw=5,
        enable=f"gte(t,{overlay_start_time})",
    )

    ffmpeg.output(video_with_overlay, video_input.audio, output_video_path).run(overwrite_output=True)
