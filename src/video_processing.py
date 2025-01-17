from googleapiclient.discovery import build
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, ColorClip
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
        videoDuration='short',
        maxResults=max_results,
        fields='items(id/videoId)'
    )
    response = request.execute()
    
    # Get video IDs directly from search results
    video_ids = [item['id']['videoId'] for item in response['items']]
    
    # Get duration information
    videos_request = youtube.videos().list(
        part='contentDetails',
        id=','.join(video_ids)
    )
    videos_response = videos_request.execute()
    
    # Filter videos under 2 minutes
    filtered_ids = []
    for item in videos_response['items']:
        duration = item['contentDetails']['duration']
        seconds = parse_duration(duration)
        if seconds <= 120:  # 2 minutes = 120 seconds
            filtered_ids.append(item['id'])
    
    return filtered_ids

def extract_video_dimensions(embed_html):
    """Extract width and height from YouTube embed HTML"""
    import re
    width_match = re.search(r'width="(\d+)"', embed_html)
    height_match = re.search(r'height="(\d+)"', embed_html)
    
    if width_match and height_match:
        return int(width_match.group(1)), int(height_match.group(1))
    return None, None

def parse_duration(duration):
    """Convert ISO 8601 duration to seconds"""
    import re
    import isodate
    return int(isodate.parse_duration(duration).total_seconds())

def fit_to_vertical(clip):
    """Fit video clip to 9:16 ratio by cropping and adding black bars"""
    target_ratio = 9/16
    current_ratio = clip.w / clip.h
    
    if current_ratio > target_ratio:  # Video is too wide (e.g., 16:9)
        # Calculate new width to maintain aspect ratio
        new_width = int(clip.h * target_ratio)
        # Center crop the width
        x_center = clip.w // 2
        x1 = x_center - (new_width // 2)
        cropped = clip.crop(x1=x1, y1=0, width=new_width, height=clip.h)
        return cropped
    elif current_ratio < target_ratio:  # Video is too tall
        # Calculate new height to maintain aspect ratio
        new_height = int(clip.w / target_ratio)
        # Center crop the height
        y_center = clip.h // 2
        y1 = y_center - (new_height // 2)
        cropped = clip.crop(x1=0, y1=y1, width=clip.w, height=new_height)
        return cropped
    return clip

def download_youtube_clips(video_ids):
    """Download YouTube clips using yt-dlp and fit to 9:16 ratio"""
    import yt_dlp
    from moviepy.editor import VideoFileClip, ColorClip, CompositeVideoClip
    
    clips = []
    for vid_id in video_ids:
        output_path = f'clip_{vid_id}.mp4'
        final_path = f'vertical_clip_{vid_id}.mp4'
        
        # Download the clip
        ydl_opts = {
            'format': 'mp4',
            'outtmpl': output_path,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            url = f'https://youtube.com/watch?v={vid_id}'
            ydl.download([url])
        
        # Load and process the clip
        with VideoFileClip(output_path) as clip:
            # Fit to vertical aspect ratio
            processed_clip = fit_to_vertical(clip)
            
            # Create a black background with 9:16 ratio
            target_height = processed_clip.h
            target_width = int(target_height * 9/16)
            
            # Create black background
            bg = ColorClip(size=(target_width, target_height), 
                         color=(0,0,0),
                         duration=processed_clip.duration)
            
            # Center the video on black background
            x_center = (target_width - processed_clip.w) // 2
            y_center = (target_height - processed_clip.h) // 2
            
            final_clip = CompositeVideoClip([
                bg,
                processed_clip.set_position((x_center, y_center))
            ])
            
            # Write the final clip
            final_clip.write_videofile(
                final_path,
                codec='libx264',
                audio_codec='aac',
                preset='medium'
            )
            
            clips.append(final_path)
            
            # Clean up original clip
            os.remove(output_path)
    
    return clips

def generate_music_video(clips, audio_file, config_manager=None):
    """Generate a music video using mvgen library"""
    if not clips:
        raise ValueError("No video clips provided for music video generation")
        
    if not audio_file:
        raise ValueError("Audio file path cannot be None")
        
    if not os.path.exists(audio_file):
        raise FileNotFoundError(f"Audio file not found at path: {audio_file}")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize MVGen with work directory
        mvgen = MVGen(
            work_directory=temp_dir,
            uid=None
        )
        
        # Add notifier for status updates
        notifier = SimpleNotifier()
        mvgen.notifier = notifier
        
        # Create clips directory
        clips_dir = os.path.join(temp_dir, 'clips')
        os.makedirs(clips_dir, exist_ok=True)
        
        # Copy clips to clips directory
        sources = []
        for i, clip in enumerate(clips):
            source_dir = os.path.join(clips_dir, f'source_{i}')
            os.makedirs(source_dir, exist_ok=True)
            
            try:
                video_path = os.path.join(source_dir, 'video.mp4')
                import shutil
                shutil.copy2(clip, video_path)
                sources.append(f'source_{i}')
            except (IOError, OSError) as e:
                raise ValueError(f"Error copying clip {clip}: {str(e)}")
        
        # Create necessary directories
        os.makedirs(os.path.join(temp_dir, 'segments'), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, 'random'), exist_ok=True)
        
        # Load audio and set rhythm patterns if available
        mvgen.load_audio(audio_file)
        if config_manager and hasattr(config_manager, 'rhythm_patterns'):
            mvgen.rhythm_patterns = config_manager.rhythm_patterns
            
        # Force CPU encoding and set segment codec
        mvgen.cuda = False
        mvgen.segment_codec = '-c:v libx264 -preset ultrafast -crf 23'
        
        # Generate with duration and sources
        mvgen.generate(
            duration=1,
            sources=sources,
            src_directory=clips_dir,
        )
        
        # Use CPU encoding for joining
        mvgen.output_codec = '-c:v libx264 -preset medium -crf 23'
        
        mvgen.make_join_file()
        output_path = mvgen.join()
        
        # Create final output path using config
        output_config = config_manager.get_output_config() if config_manager else {}
        final_path = output_config.get('music_video_filename', "generated_music_video.mp4")
        
        # Finalize the video
        mvgen.finalize(output_path, final_path)
        
        return final_path

def prepare_video_clips(config_manager: ConfigManager, prompt: str = None, video_paths: list = None, api_key: str = None) -> list:
    """Prepare video clips based on configuration"""
    method = config_manager.video_source_method
    
    if method == "youtube_search":
        if not api_key:
            raise ValueError("YouTube API key is required when using YouTube search")
        video_ids = search_youtube(prompt, api_key, max_results=config_manager.max_youtube_results)
        if not video_ids:
            raise ValueError("No suitable video clips found for the given search prompt")
        return download_youtube_clips(video_ids)
    
    elif method == "youtube_links":
        links = config_manager.youtube_links
        if not links:
            raise ValueError("No YouTube links provided in configuration")
        # Extract video IDs from links
        video_ids = [link.split('v=')[-1] for link in links]
        return download_youtube_clips(video_ids)
    
    elif method == "file_paths":
        paths = config_manager.file_paths
        if not paths:
            raise ValueError("No video file paths provided in configuration")
        # Verify all paths exist
        for path in paths:
            if not os.path.exists(path):
                raise ValueError(f"Video file not found: {path}")
        return paths
    
    elif method == "combination":
        clips = []
        
        # Process YouTube links if any
        links = config_manager.youtube_links
        if links:
            video_ids = [link.split('v=')[-1] for link in links]
            clips.extend(download_youtube_clips(video_ids))
            
        # Process local files if any
        paths = config_manager.file_paths
        for path in paths:
            if os.path.exists(path):
                clips.append(path)
            else:
                print(f"Warning: Skipping non-existent file: {path}")
        
        if not clips:
            raise ValueError("No valid video sources found in combination configuration")
        
        return clips
    
    else:
        raise ValueError(f"Invalid video source method: {method}")

def add_lyrics_overlay(video_path: str, lyrics: str, config: dict) -> str:
    print(f"Adding lyrics overlay to video: {video_path}")
    print(f"Lyrics content: {lyrics[:100]}...")  # Print first 100 chars
    
    # Configure MoviePy to use ImageMagick
    if os.name == 'nt':  # Windows
        change_settings({"IMAGEMAGICK_BINARY": r"C:\\Program Files\\ImageMagick-7.0.10-Q16\\magick.exe"})
    else:  # macOS/Linux
        change_settings({"IMAGEMAGICK_BINARY": "convert"})
    
    if not lyrics or lyrics.strip() == "":
        print("Warning: No lyrics provided for overlay")
        return video_path
    
    video = VideoFileClip(video_path)
    print(f"Video loaded. Duration: {video.duration}s")
    
    try:
        # Create text clip with proper font
        txt_clip = TextClip(
            lyrics, 
            fontsize=config.get('fontsize', 24),
            color=config.get('text_color', 'white'),
            font='Arial',
            size=(video.w * 0.8, None),  # Wrap text to 80% of video width
            method='caption'  # Use caption method for better text wrapping
        )
        print("Text clip created successfully")
        
        # Position the text
        position = config.get('text_position', 'bottom')
        if position == 'bottom':
            txt_clip = txt_clip.set_position(('center', 0.8)).set_duration(video.duration)
        elif position == 'top':
            txt_clip = txt_clip.set_position(('center', 0.1)).set_duration(video.duration)
        else:
            txt_clip = txt_clip.set_position('center').set_duration(video.duration)
        
        # Combine video and text
        final_clip = CompositeVideoClip([video, txt_clip])
        
        # Write output with preserved quality
        output_path = config.get('final_video_filename', "final_video.mp4")
        print(f"Writing final video to: {output_path}")
        final_clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            bitrate='8000k',
            preset='medium',  # Changed from 'slow' for faster processing during debug
            remove_temp=True,
            threads=4
        )
        
        return output_path
    except Exception as e:
        print(f"Error in lyrics overlay: {str(e)}")
        raise
    finally:
        # Clean up
        video.close()
        if 'txt_clip' in locals():
            txt_clip.close()
        if 'final_clip' in locals():
            final_clip.close()

def download_audio_from_youtube(youtube_link: str) -> str:
    """Download audio from YouTube video"""
    import yt_dlp
    
    # Create temporary file for audio
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
        output_path = temp_file.name
    
    # Configure yt-dlp for audio download
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
        'outtmpl': output_path,
    }
    
    # Download audio
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_link])
    
    return output_path