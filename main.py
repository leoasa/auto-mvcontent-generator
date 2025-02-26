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
    input_data, audio_file = get_user_input(config_manager)
    
    # Add status message
    print(f"Searching for '{input_data}' clips for audio file at '{audio_file}'...")
    
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
    edited_video = generate_music_video(clips, audio_file, config_manager)
    
    final_video = edited_video
    # Only process lyrics if enabled in config
    if config_manager.enable_lyrics:
        try:
            # Get lyrics using Whisper
            lyrics = transcribe_audio(audio_file)
            
            # Add lyrics overlay with configuration
            final_video = add_lyrics_overlay(
                edited_video, 
                lyrics, 
                config_manager.get_video_processing_config()
            )
        except Exception as e:
            print(f"Warning: Lyrics processing failed: {str(e)}")
            print("Continuing without lyrics overlay...")
    
    # First, ensure output directory exists
    if not os.path.exists(config_manager.output_directory):
        os.makedirs(config_manager.output_directory)

    # Save final video
    final_video_path = os.path.join(
        config_manager.output_directory,
        output_config.get('music_video_filename', 'generated_music_video.mp4')
    )
    try:
        import shutil
        if os.path.exists(final_video_path):
            os.remove(final_video_path)  # Remove existing file if present
        shutil.copy2(final_video, final_video_path)
        print(f"Video forcefully copied to: {final_video_path}")
    except Exception as e:
        print(f"Error saving video to output directory: {str(e)}")
        final_video_path = final_video  # Fallback to temp location
    
    # Post to TikTok only if configured to do so
    if config_manager.should_post_to_social:
        title = f"AI-generated music video for: {input_data if config_manager.use_youtube_search else 'custom clips'}"
        success = post_to_tiktok(final_video_path, title)
        if not success:
            print("Failed to post video to TikTok")
    else:
        print(f"Video saved to: {final_video_path}")
        
    # Cleanup temporary files
    cleanup_files(
        clips + [edited_video] if edited_video != final_video else [edited_video]
    )

if __name__ == "__main__":
    main()
