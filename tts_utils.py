import os
import wave
import google.genai as genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def _wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
   """Saves PCM data to a WAV file."""
   with wave.open(filename, "wb") as wf:
      wf.setnchannels(channels)
      wf.setsampwidth(sample_width)
      wf.setframerate(rate)
      wf.writeframes(pcm)


def generate_commentary_audio(text, output_filename):
    """
    Generates audio commentary from text using the Gemini API and saves it to a file.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in .env file.")

    client = genai.Client(api_key=GEMINI_API_KEY)

    print(f"Generating audio for: '{text}'")

    prompt = f"Read in the voice of an action sports commentator speaking quickly with excitement: {text}"
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_modalities=[types.MediaModality.AUDIO],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name='Schedar',
                        )
                    )
                ),
            )
        )

        if (response
            and response.candidates
            and response.candidates[0].content
            and response.candidates[0].content.parts):
            
            audio_part = response.candidates[0].content.parts[0]
            if audio_part.inline_data and audio_part.inline_data.data:
                data = audio_part.inline_data.data
                _wave_file(output_filename, data)
                print(f"Audio saved to {output_filename}")
                return output_filename

        raise ValueError("Could not extract audio data from the response.")

    except Exception as e:
        print(f"Error generating audio: {e}")
        return None