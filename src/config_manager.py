import yaml
from typing import Dict, Any

class ConfigManager:
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def get_video_source_config(self) -> Dict[str, Any]:
        return self.config.get('video_source', {})
    
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
        return self.get_video_source_config().get('use_youtube_search', True)
    
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
        return self.prompt is not None and self.audio_file is not None