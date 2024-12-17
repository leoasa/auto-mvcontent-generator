from googleapiclient.discovery import build
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
from moviepy.config import change_settings
import os
from mvgen.mvgen import MVGen
import tempfile
from .config_manager import ConfigManager

class SimpleNotifier:
    def notify(self, message):
        # Handle both string and dictionary messages
        if isinstance(message, dict):
            status = message.get('status', 'Unknown status')
            print(f"MVGen Status: {status}")
        else:
            print(f"MVGen Status: {message}")

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
    """
    if not clips:
        raise ValueError("No video clips provided for music video generation")
        
    if not audio_file:
        raise ValueError("Audio file path cannot be None")
        
    if not os.path.exists(audio_file):
        raise FileNotFoundError(f"Audio file not found at path: {audio_file}")
        
    # Get audio duration using moviepy
    audio_clip = AudioFileClip(audio_file)
    duration = audio_clip.duration
    audio_clip.close()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create directory structure expected by MVGen
        temp_dir_abs = os.path.abspath(temp_dir)
        raw_dir = os.path.join(temp_dir_abs, 'raw')
        work_dir = os.path.join(temp_dir_abs, 'work')
        ready_dir = os.path.join(temp_dir_abs, 'ready')
        segments_dir = os.path.join(temp_dir_abs, 'segments')
        
        # Create all required directories
        for directory in [raw_dir, work_dir, ready_dir, segments_dir]:
            os.makedirs(directory, exist_ok=True)
            
        # Copy clips to raw directory
        sources = []
        for i, clip in enumerate(clips):
            source_dir = os.path.join(raw_dir, f'source_{i}')
            os.makedirs(source_dir, exist_ok=True)
            
            try:
                new_path = os.path.join(source_dir, f'clip_{i}.mp4')
                import shutil
                shutil.copy2(clip, new_path)
                sources.append(f'source_{i}')
            except (IOError, OSError) as e:
                raise ValueError(f"Error copying clip {clip}: {str(e)}")
        
        # Initialize MVGen with proper directory structure and custom FFmpeg options
        notifier = SimpleNotifier()
        mvgen = MVGen(
            raw_dir, 
            segments_dir,
            work_dir
        )

        mvgen.notifier = notifier
        
        # Load audio and generate
        mvgen.load_audio(audio_file)
        # Use a smaller duration value (e.g., 1 second) to create shorter segments
        mvgen.generate(duration=1, sources=sources, src_directory=raw_dir)
        
        # Create and process the final video
        mvgen.make_join_file()
        output_path = mvgen.join()
        
        # Create final output path and finalize
        final_path = "generated_music_video.mp4"
        mvgen.finalize(
            ready_directory=ready_dir,
            delete_work_dir=False
        )
        
        # Use the correct filename that MVGen creates - "segments.mp4"
        source_video = os.path.join(ready_dir, "segments.mp4")
        
        # Copy the final video from ready_dir to current directory
        if not os.path.exists(source_video):
            raise FileNotFoundError(f"MVGen did not create the expected output file at {source_video}")
        
        shutil.copy2(source_video, final_path)
        
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
    # Configure MoviePy to use ImageMagick
    if os.name == 'nt':  # Windows
        change_settings({"IMAGEMAGICK_BINARY": r"C:\\Program Files\\ImageMagick-7.0.10-Q16\\magick.exe"})
    else:  # macOS/Linux
        change_settings({"IMAGEMAGICK_BINARY": "convert"})
    
    video = VideoFileClip(video_path)
    
    # Create text clip with proper font
    txt_clip = TextClip(
        lyrics, 
        fontsize=config.get('fontsize', 24),
        color=config.get('text_color', 'white'),
        font='Arial'  # Specify a common font
    )
    
    # Position the text
    position = config.get('text_position', 'bottom')
    if position == 'bottom':
        txt_clip = txt_clip.set_position(('center', 'bottom')).set_duration(video.duration)
    elif position == 'top':
        txt_clip = txt_clip.set_position(('center', 'top')).set_duration(video.duration)
    else:
        txt_clip = txt_clip.set_position('center').set_duration(video.duration)
    
    # Combine video and text
    final_clip = CompositeVideoClip([video, txt_clip])
    
    # Write output
    output_path = config.get('final_video_filename', "final_video.mp4")
    final_clip.write_videofile(output_path)
    
    # Clean up
    video.close()
    txt_clip.close()
    final_clip.close()
    
    return output_path