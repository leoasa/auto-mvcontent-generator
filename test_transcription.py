from src.audio_processing import transcribe_audio
from src.config import OPENAI_API_KEY
import os

def test_transcription():
    # Set OpenAI API key
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

    # Audio file path from your config
    audio_file = "/Users/leoasatoorian/Documents/UP.wav"

    # Verify file exists
    if not os.path.exists(audio_file):
        print(f"Error: Audio file not found at {audio_file}")
        return

    # Test transcription
    print("\n=== Starting Transcription Test ===")
    print(f"Audio file: {audio_file}")
    
    try:
        print("\nProcessing...")
        lyrics = transcribe_audio(audio_file)
        
        print("\n=== Transcription Results ===")
        print("Length:", len(lyrics), "characters")
        print("\nFirst 200 characters:")
        print("-" * 50)
        print(lyrics[:200])
        print("-" * 50)
        print("\nFull transcription:")
        print("=" * 50)
        print(lyrics)
        print("=" * 50)
        
    except Exception as e:
        print(f"\nError during transcription: {str(e)}")
        raise

if __name__ == "__main__":
    test_transcription()