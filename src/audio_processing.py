from openai import OpenAI
import subprocess
import tempfile
import os
import json

def compress_audio(input_path: str, max_size_mb: int = 24) -> str:
    """Compress audio file to meet OpenAI's size limit"""
    # Create temp file with .wav extension
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
        temp_path = temp_file.name
    
    # Convert and compress audio using ffmpeg, maintaining volume
    cmd = f'ffmpeg -y -i "{input_path}" -ar 16000 -ac 1 -c:a pcm_s16le -filter:a "volume=1.0" "{temp_path}"'
    subprocess.run(cmd, shell=True, check=True)
    
    # Check if file size is within limit
    size_mb = os.path.getsize(temp_path) / (1024 * 1024)
    if size_mb > max_size_mb:
        # If still too large, compress further but maintain volume
        bitrate = int((max_size_mb / size_mb) * 16000)
        final_temp = temp_path + '_compressed.wav'
        cmd = f'ffmpeg -y -i "{temp_path}" -ar {bitrate} -ac 1 -c:a pcm_s16le -filter:a "volume=1.0" "{final_temp}"'
        subprocess.run(cmd, shell=True, check=True)
        os.unlink(temp_path)  # Remove intermediate file
        return final_temp
    
    return temp_path

def get_duration(file_path: str) -> float:
    """Get duration of audio file using ffprobe"""
    cmd = f'ffprobe -v quiet -print_format json -show_format "{file_path}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    data = json.loads(result.stdout)
    return float(data['format']['duration'])

def split_audio(file_path: str, chunk_size_mb: int = 24) -> list:
    """Split audio file into chunks using ffmpeg and compress each chunk"""
    # Get audio duration
    duration = get_duration(file_path)
    
    # Calculate chunk duration based on file size and chunk size limit
    file_size = os.path.getsize(file_path)
    chunk_duration = (chunk_size_mb * 1024 * 1024 / file_size) * duration
    
    chunks = []
    current_time = 0
    
    while current_time < duration:
        # First create uncompressed chunk
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            chunk_path = temp_file.name
            
            # Extract chunk
            cmd = f'ffmpeg -y -i "{file_path}" -ss {current_time} -t {chunk_duration} "{chunk_path}"'
            subprocess.run(cmd, shell=True, check=True)
            
            # Compress the chunk
            compressed_chunk = compress_audio(chunk_path)
            chunks.append(compressed_chunk)
            
            # Clean up uncompressed chunk
            os.unlink(chunk_path)
            
            current_time += chunk_duration
    
    return chunks

def transcribe_chunk(client: OpenAI, chunk_path: str) -> str:
    """Transcribe a single audio chunk"""
    with open(chunk_path, "rb") as file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=file,
            response_format="text"
        )
    return transcript

def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio file using OpenAI Whisper API"""
    client = OpenAI()
    
    # First try compressing
    compressed_audio = compress_audio(audio_path)
    
    try:
        # Try to transcribe the compressed file directly
        try:
            with open(compressed_audio, "rb") as file:
                return client.audio.transcriptions.create(
                    model="whisper-1",
                    file=file,
                    response_format="text"
                )
        except Exception as e:
            if "413" not in str(e):  # If error is not related to file size, re-raise
                raise
            
            # If file is still too large, split into chunks
            print("File still too large, splitting into chunks...")
            chunks = split_audio(compressed_audio)
            
            try:
                # Transcribe each chunk and combine
                transcripts = []
                for chunk in chunks:
                    transcript = transcribe_chunk(client, chunk)
                    transcripts.append(transcript)
                    
                return " ".join(transcripts)
            finally:
                # Clean up chunk files
                for chunk in chunks:
                    if os.path.exists(chunk):
                        os.unlink(chunk)
                        
    finally:
        # Clean up compressed file
        if os.path.exists(compressed_audio):
            os.unlink(compressed_audio)