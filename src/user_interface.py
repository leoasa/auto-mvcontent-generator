import os
from src.video_processing import download_audio_from_youtube

def get_user_input(config_manager):
    """Get user input based on configuration"""
    # Check if input is predefined in config
    if config_manager.has_predefined_input:
        if config_manager.use_youtube_search:
            video_input = config_manager.prompt
        else:
            # For manual video input, split the prompt string into a list of paths
            video_paths = config_manager.prompt.split(',') if config_manager.prompt else []
            video_input = video_paths
    else:
        print("Enter paths to video files (one per line). Press Enter twice when done:")
        video_paths = []
        while True:
            path = input()
            if not path:
                break
            if os.path.exists(path):
                video_paths.append(path)
            else:
                print(f"Warning: File {path} does not exist")
        video_input = video_paths
    
    # Handle audio source
    if config_manager.audio_source_method == "youtube":
        if config_manager.audio_youtube_link:
            audio_path = download_audio_from_youtube(config_manager.audio_youtube_link)
        else:
            raise ValueError("YouTube link for audio not provided in configuration")
    else:  # file method
        audio_path = config_manager.audio_file_path
        if not audio_path:
            audio_path = input("Enter path to audio file: ")
    
    if not audio_path or (config_manager.audio_source_method == "file" and not os.path.exists(audio_path)):
        raise ValueError("Invalid audio file path")
    
    return video_input, audio_path 