import os

def get_user_input(use_youtube_search: bool = True):
    """Get user input based on configuration"""
    prompt = None
    if use_youtube_search:
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
    
    audio_path = input("Enter path to audio file: ")
    
    if use_youtube_search:
        return prompt, audio_path
    return video_paths, audio_path 