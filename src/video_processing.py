from googleapiclient.discovery import build
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import os
from mvgen.mvgen import MVGen
import tempfile
from .config_manager import ConfigManager

def search_youtube(prompt, api_key, max_results=5):
    print(f"Searching YouTube for: {prompt}")
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.search().list(
        part='snippet',
        q=prompt,
        type='video',
        videoDuration='short',  # Returns only videos under ~4 minutes
        maxResults=max_results,
        fields='items(id/videoId)'  # Optimize by only requesting needed fields
    )
    response = request.execute()
    print(f"Search response: {response}")
    
    # Get detailed video information to filter by exact duration
    video_ids = [item['id']['videoId'] for item in response['items']]
    videos_request = youtube.videos().list(
        part='contentDetails',
        id=','.join(video_ids)
    )
    videos_response = videos_request.execute()
    
    # Filter videos under 2 minutes (120 seconds)
    filtered_ids = []
    for item in videos_response['items']:
        duration = item['contentDetails']['duration']  # Returns in ISO 8601 format
        seconds = parse_duration(duration)
        if seconds <= 120:  # 2 minutes = 120 seconds
            filtered_ids.append(item['id'])
    
    return filtered_ids

def parse_duration(duration):
    """Convert ISO 8601 duration to seconds"""
    import re
    import isodate
    return int(isodate.parse_duration(duration).total_seconds())

def download_youtube_clips(video_ids):
    """Download YouTube clips using yt-dlp"""
    import yt_dlp
    
    clips = []
    for vid_id in video_ids:
        output_path = f'clip_{vid_id}.mp4'
        ydl_opts = {
            'format': 'mp4',
            'outtmpl': output_path,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            url = f'https://youtube.com/watch?v={vid_id}'
            ydl.download([url])
        clips.append(output_path)
    return clips

def generate_music_video(clips, audio_file):
    """
    Generate a music video using mvgen library by combining video clips with audio
    
    Args:
        clips (list): List of paths to video clips
        audio_file (str): Path to the audio file
    
    Returns:
        str: Path to the generated music video
    """
    if not clips:
        raise ValueError("No video clips provided for music video generation")
        
    with tempfile.TemporaryDirectory() as temp_dir:
        # Add debug logging
        print(f"Temporary directory created at: {temp_dir}")
        
        clips_dir = os.path.join(temp_dir, 'clips')
        os.makedirs(clips_dir, exist_ok=True)
        
        # Add debug logging
        print(f"Clips directory created at: {clips_dir}")
        print(f"Clips to process: {clips}")
        
        # Copy clips to the clips directory
        clip_paths = []
        for i, clip in enumerate(clips):
            new_path = os.path.join(clips_dir, f'clip_{i}.mp4')
            os.system(f'cp "{clip}" "{new_path}"')
            clip_paths.append(new_path)
        
        # Add debug logging
        print(f"Copied clips to: {clip_paths}")
        
        # Verify directory exists and has content
        if not os.path.exists(clips_dir):
            raise ValueError(f"Clips directory does not exist: {clips_dir}")
        if not os.listdir(clips_dir):
            raise ValueError(f"Clips directory is empty: {clips_dir}")
            
        # Add more robust path validation
        if not os.path.isdir(clips_dir):
            raise ValueError(f"Invalid clips directory: {clips_dir}")
            
        # Ensure all clips were copied successfully
        if len(os.listdir(clips_dir)) != len(clips):
            raise ValueError(f"Not all clips were copied successfully. Expected {len(clips)} clips, found {len(os.listdir(clips_dir))}")
        
        mvgen = MVGen(
            work_directory=temp_dir,
            uid=None
        )
        
        mvgen.load_audio(audio_file)
        
        # Ensure clips_dir is valid before passing to generate
        if not clips_dir or not os.path.exists(clips_dir):
            raise ValueError(f"Invalid clips directory before generate: {clips_dir}")
            
        # Pass the clips directory path directly
        mvgen.generate(clips_dir)
        
        mvgen.make_join_file()
        output_path = mvgen.join()
        
        # Create final output path
        final_path = "generated_music_video.mp4"
        mvgen.finalize(output_path, final_path)
        
        return final_path

def prepare_video_clips(config_manager: ConfigManager, prompt: str = None, video_paths: list = None, api_key: str = None) -> list:
    """Prepare video clips based on configuration"""
    if config_manager.use_youtube_search:
        if not api_key:
            raise ValueError("YouTube API key is required when using YouTube search")
        video_ids = search_youtube(prompt, api_key, max_results=config_manager.max_youtube_results)
        if not video_ids:
            raise ValueError("No suitable video clips found for the given search prompt")
        return download_youtube_clips(video_ids)
    else:
        if not video_paths:
            raise ValueError("Video paths are required when not using YouTube search")
        return video_paths

def add_lyrics_overlay(video_path: str, lyrics: str, config: dict) -> str:
    """Add lyrics overlay with configurable parameters"""
    video = VideoFileClip(video_path)
    txt_clip = TextClip(
        lyrics, 
        fontsize=config.get('fontsize', 24),
        color=config.get('text_color', 'white')
    )
    txt_clip = txt_clip.set_position(config.get('text_position', 'bottom')).set_duration(video.duration)
    final_clip = CompositeVideoClip([video, txt_clip])
    output_path = config.get('final_video_filename', "final_video.mp4")
    final_clip.write_videofile(output_path)
    return output_path 