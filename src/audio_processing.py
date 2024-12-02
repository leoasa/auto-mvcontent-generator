import openai
import os
from .config import OPENAI_API_KEY

def transcribe_audio(audio_file):
    openai.api_key = OPENAI_API_KEY
    with open(audio_file, "rb") as file:
        transcript = openai.Audio.transcribe("whisper-1", file)
    return transcript.text 