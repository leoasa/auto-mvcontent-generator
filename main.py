import os
from src.video_processing import (
    prepare_video_clips,
    generate_music_video,
    add_lyrics_overlay
)
from src.social_media import post_to_tiktok
from src.audio_processing import transcribe_audio
from src.user_interface import get_user_input
from src.utils import cleanup_files
from src.config import YOUTUBE_API_KEY
from src.config_manager import ConfigManager

def main():
    # Load configuration
    config_manager = ConfigManager()
    
    # Get user input based on configuration
    input_data, audio_file = get_user_input(config_manager.use_youtube_search)
    
    # Prepare video clips (either from YouTube or manual input)
    clips = prepare_video_clips(
        config_manager,
        prompt=input_data if config_manager.use_youtube_search else None,
        video_paths=input_data if not config_manager.use_youtube_search else None,
        api_key=YOUTUBE_API_KEY if config_manager.use_youtube_search else None
    )
    
    print("Clips:", clips)
    
    # Generate music video
    output_config = config_manager.get_output_config()
    edited_video = generate_music_video(clips, audio_file)
    
    # Get lyrics using Whisper
    lyrics = transcribe_audio(audio_file)
    
    # Add lyrics overlay with configuration
    final_video = add_lyrics_overlay(
        edited_video, 
        lyrics, 
        config_manager.get_video_processing_config()
    )
    
    # Post to TikTok with a title
    title = f"AI-generated music video for: {input_data if config_manager.use_youtube_search else 'custom clips'}"
    success = post_to_tiktok(final_video, title)
    
    if not success:
        print("Failed to post video to TikTok")
    
    # Cleanup temporary files
    cleanup_files(
        clips + [edited_video, final_video] if config_manager.use_youtube_search else [edited_video, final_video]
    )

if __name__ == "__main__":
    main()
