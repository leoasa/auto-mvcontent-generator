# auto-mvcontent-generator

A Python-based tool that automatically generates music videos from video clips and audio, with optional lyrics overlay and social media posting capabilities.

## Features

- YouTube clip search and download
- Local video file support
- Audio processing from YouTube or local files
- Automatic lyrics transcription (using OpenAI Whisper)
- Vertical video formatting (9:16 aspect ratio)
- TikTok posting integration
- Configurable video generation parameters

## Dependencies

Required installations:
- Python 3.13.1
- FFmpeg
- ImageMagick (for lyrics overlay)
- CUDA (optional, for better performance)

Python packages (from requirements.txt):
- google-api-python-client
- openai
- httpx
- requests
- yt-dlp
- isodate
- moviepy
- attrs
- PyWavelets
- unidecode
- python-dotenv
- PyYAML

## Installation

1. **System Requirements**:

   Install required system packages:

   - **macOS**:
     ```bash
     brew install ffmpeg imagemagick
     ```

   - **Ubuntu/Debian**:
     ```bash
     sudo apt-get install ffmpeg imagemagick
     ```

2. **Python Environment**:

   Set up a virtual environment and install Python packages:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/macOS
   # Windows: venv\Scripts\activate

   pip install -r requirements.txt
   ```

3. **Environment Variables**:

   Create a `.env` file with your API keys:

   ```plaintext
   YOUTUBE_API_KEY=your_key
   TIKTOK_API_KEY=your_key
   TIKTOK_API_SECRET=your_secret
   OPENAI_API_KEY=your_key
   ```

## Usage

1. **Configure** `config.yaml`:

   ```yaml
   video_source:
     method: "youtube_search"  # Options: youtube_search/youtube_links/file_paths/combination
     prompt: "concert footage"  # Search query for YouTube
     max_youtube_results: 5

   audio_source:
     method: "file"
     file_path: "/path/to/audio.wav"

   video_processing:
     enable_lyrics: true
     text_color: "yellow"
     text_position: "top"

   output:
     post_to_social: false
   ```

2. **Run the program**:

   ```bash
   python main.py
   ```

## Key Configuration Options

- **Video Sources**:
  - YouTube Search: Set `method: youtube_search` and provide a `prompt`.
  - Local Files: Set `method: file_paths` and list paths under `file_paths`.
  - Combination: Use both YouTube links and local files.

- **Audio Processing**:
  - Use local files or YouTube links for audio.
  - Enable lyrics transcription with `enable_lyrics: true`. 
  - **Note**: Lyric transcription is not supported due to the incompatibility of PyTorch for stem splitting with the working version of Python.

- **Output Settings**:
  - Control social media posting with `post_to_social`.
  - Customize output filename and directory.
  - Adjust video dimensions (9:16 vertical format is automatic).

- **Note**:
  - Rhythm pattern configurations and APIs are not thoroughly tested. Please use with caution and report any issues.

## Features

All features can be configured through `config.yaml`:
- Multiple video source types
- Automatic vertical formatting
- Lyrics synchronization (needs OpenAI Whisper)
- Rhythm-based editing (see rhythm_patterns example in config)
- Social media integration
- Audio/video quality controls

This README provides a comprehensive guide to setting up and using the auto-mvcontent-generator tool, including installation, configuration, and usage instructions. Adjust the `config.yaml` file to customize the video generation process according to your needs.
