import yaml
from typing import Dict, Any
import os

class ConfigManager:
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def get_video_source_config(self) -> Dict[str, Any]:
        return self.config.get('video_source', {})
    
    @property
    def video_source_method(self) -> str:
        return self.get_video_source_config().get('method', 'youtube_search')
    
    @property
    def youtube_links(self) -> list:
        return self.get_video_source_config().get('youtube_links', [])
    
    @property
    def file_paths(self) -> list:
        return self.get_video_source_config().get('file_paths', [])
    
    def get_video_processing_config(self) -> Dict[str, Any]:
        return {
            'fontsize': self.config.get('video_processing', {}).get('fontsize', 24),
            'text_color': self.config.get('video_processing', {}).get('text_color', 'white'),
            'text_position': self.config.get('video_processing', {}).get('text_position', 'bottom'),
            'final_video_filename': self.config.get('output', {}).get('final_video_filename', 'final_video.mp4')
        }
    
    def get_output_config(self) -> Dict[str, Any]:
        return self.config.get('output', {})
    
    @property
    def use_youtube_search(self) -> bool:
        """Check if using YouTube search"""
        return self.video_source_method == "youtube_search"
    
    @property
    def max_youtube_results(self) -> int:
        return self.get_video_source_config().get('max_youtube_results', 5)
    
    @property
    def prompt(self) -> str:
        return self.get_video_source_config().get('prompt')
    
    @property
    def audio_file(self) -> str:
        return self.get_video_source_config().get('audio_file')
    
    @property
    def has_predefined_input(self) -> bool:
        """Check if input is predefined in config"""
        if self.use_youtube_search:
            return bool(self.prompt)
        return bool(self.youtube_links or self.file_paths)
    
    def get_audio_source_config(self) -> Dict[str, Any]:
        return self.config.get('audio_source', {})
    
    @property
    def audio_source_method(self) -> str:
        return self.get_audio_source_config().get('method', 'file')
    
    @property
    def audio_file_path(self) -> str:
        return self.get_audio_source_config().get('file_path')
    
    @property
    def audio_youtube_link(self) -> str:
        return self.get_audio_source_config().get('youtube_link')
    
    @property
    def output_directory(self) -> str:
        return self.config.get('output', {}).get('output_directory', './output')
    
    @property
    def should_post_to_social(self) -> bool:
        return self.config.get('output', {}).get('post_to_social', False)
    
    @property
    def combined_sources(self) -> list:
        """Get combined video sources from config"""
        return self.get_video_source_config().get('sources', [])
    
    @property
    def rhythm_patterns(self) -> list:
        """Get rhythm patterns from config"""
        patterns = self.config.get('rhythm_patterns', [])
        return sorted(patterns, key=lambda x: x.get('timestamp', 0))
    
    def get_pattern_at_timestamp(self, timestamp: float) -> str:
        """Get the rhythm pattern active at a given timestamp"""
        patterns = self.rhythm_patterns
        for pattern in reversed(patterns):
            if timestamp >= pattern.get('timestamp', 0):
                return pattern.get('pattern', '1/4')
        return '1/4'  # Default to quarter notes
    
    @property
    def enable_lyrics(self) -> bool:
        """Check if lyrics processing is enabled"""
        return self.config.get('video_processing', {}).get('enable_lyrics', False)