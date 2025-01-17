from openai import OpenAI
import subprocess
import tempfile
import os
import json
import httpx

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
    print(f"Starting transcription process for: {audio_path}")
    
    # Create a basic httpx client without proxy configuration
    http_client = httpx.Client()
    
    # Initialize OpenAI client with the custom http client
    client = OpenAI(
        http_client=http_client
    )
    
    try:
        # First isolate vocals
        vocals_path = isolate_vocals(audio_path)
        print(f"Vocals isolated to: {vocals_path}")
        
        # Compress the vocals
        compressed_audio = compress_audio(vocals_path)
        print(f"Compressed vocals created at: {compressed_audio}")
        
        try:
            print("Attempting direct transcription of vocals...")
            with open(compressed_audio, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-1",
                    response_format="text",
                    language="en",
                    prompt="This is an English song with lyrics"
                )
                print(f"Transcription successful. Length: {len(transcript)} characters")
                print(f"First 100 characters: {transcript[:100]}")
                return transcript
        except Exception as e:
            print(f"Transcription error: {str(e)}")
            raise
    finally:
        # Clean up temporary files
        for file_path in [vocals_path, compressed_audio]:
            if 'file_path' in locals() and os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                except Exception as e:
                    print(f"Warning: Could not delete temporary file {file_path}: {e}")
        # Close the http client
        http_client.close()

def isolate_vocals(input_path: str) -> str:
    """Extract vocals from audio file using demucs"""
    print("Isolating vocals from audio...")
    import torch
    import torchaudio
    from demucs.pretrained import get_model
    from demucs.apply import apply_model
    import numpy as np
    
    # Create temp file for vocals
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
        vocals_path = temp_file.name
    
    # Load model
    model = get_model('htdemucs')
    model.cuda() if torch.cuda.is_available() else model.cpu()
    
    # Load audio
    wav, sr = torchaudio.load(input_path)
    wav = wav.cuda() if torch.cuda.is_available() else wav
    
    # Separate stems
    ref = wav.mean(0)
    wav = (wav - ref.mean()) / ref.std()
    sources = apply_model(model, wav.unsqueeze(0), progress=True)[0]
    sources = sources * ref.std() + ref.mean()
    
    # Get vocals and save
    vocals = sources[model.sources.index('vocals')]
    torchaudio.save(vocals_path, vocals.cpu(), sr)
    
    return vocals_path