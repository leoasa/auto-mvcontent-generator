import os

def get_user_input(config_manager):
    """Get user input based on configuration"""
    # Check if input is predefined in config
    if config_manager.has_predefined_input:
        if config_manager.use_youtube_search:
            return config_manager.prompt, config_manager.audio_file
        else:
            # For manual video input, split the prompt string into a list of paths
            video_paths = config_manager.prompt.split(',') if config_manager.prompt else []
            return video_paths, config_manager.audio_file
        
    prompt = None
    if config_manager.use_youtube_search:
        prompt = input("Enter search prompt for YouTube clips: ")
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
        prompt = video_paths
    
    audio_path = input("Enter path to audio file: ")
    
    return prompt, audio_path 