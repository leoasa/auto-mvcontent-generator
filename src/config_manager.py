import yaml
from typing import Dict, Any

class ConfigManager:
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def get_video_source_config(self) -> Dict[str, Any]:
        return self.config.get('video_source', {})
    
    def get_video_processing_config(self) -> Dict[str, Any]:
        return self.config.get('video_processing', {})
    
    def get_output_config(self) -> Dict[str, Any]:
        return self.config.get('output', {})
    
    @property
    def use_youtube_search(self) -> bool:
        return self.get_video_source_config().get('use_youtube_search', True)
    
    @property
    def max_youtube_results(self) -> int:
        return self.get_video_source_config().get('max_youtube_results', 5) 