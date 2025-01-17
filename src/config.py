import os
from dotenv import load_dotenv

load_dotenv()

def get_env_variable(name):
    value = os.getenv(name)
    if value is None:
        raise ValueError(f"Environment variable {name} is not set")
    return value

TIKTOK_API_KEY = get_env_variable('TIKTOK_API_KEY')
TIKTOK_API_SECRET = get_env_variable('TIKTOK_API_SECRET')
TIKTOK_REDIRECT_URI = 'https://b30b-137-25-7-17.ngrok/callback/'
YOUTUBE_API_KEY = get_env_variable('YOUTUBE_API_KEY')
OPENAI_API_KEY = get_env_variable('OPENAI_API_KEY')