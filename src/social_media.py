import os
import hashlib
import secrets
import requests
from typing import Optional
from typing_extensions import Tuple
from .config import TIKTOK_API_KEY, TIKTOK_API_SECRET, TIKTOK_REDIRECT_URI

class TikTokAPI:
    def __init__(self):
        self.auth_url = 'https://tiktok.com/v2/auth/authorize/'
        self.post_url = 'https://tiktokapis.com/v2/post/publish/video/init/'
        self.status_url = 'https://tiktokapis.com/v2/post/publish/status/fetch/'
        self.access_token: Optional[str] = None
        
    def generate_auth_params(self) -> Tuple[str, str, str]:
        """Generate PKCE parameters for TikTok authentication"""
        # Generate code verifier
        code_verifier = secrets.token_urlsafe(64)[:128]
        
        # Generate code challenge using SHA256
        code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).hexdigest()
        
        # Generate state token
        state = secrets.token_urlsafe(32)
        
        return code_verifier, code_challenge, state
    
    def get_auth_url(self) -> str:
        """Generate TikTok authorization URL"""
        code_verifier, code_challenge, state = self.generate_auth_params()
        
        params = {
            'client_key': TIKTOK_API_KEY,
            'scope': 'video.publish',
            'response_type': 'code',
            'redirect_uri': TIKTOK_REDIRECT_URI,
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }
        
        # Store code_verifier for later use
        self.code_verifier = code_verifier
        self.state = state
        
        # Build URL with parameters
        auth_url = self.auth_url + '?' + '&'.join([f'{k}={v}' for k, v in params.items()])
        return auth_url

    def handle_callback(self, code: str, state: str) -> bool:
        """Handle TikTok OAuth callback and get access token"""
        if state != self.state:
            raise ValueError("State mismatch - possible CSRF attack")
            
        token_url = 'https://open.tiktokapis.com/v2/oauth/token/'
        data = {
            'client_key': TIKTOK_API_KEY,
            'client_secret': TIKTOK_API_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'code_verifier': self.code_verifier
        }
        
        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            self.access_token = response.json()['access_token']
            return True
        return False

    def post_video(self, video_path: str, title: str) -> Optional[str]:
        """Post video to TikTok using Content Posting API"""
        if not self.access_token:
            raise ValueError("Not authenticated - call handle_callback first")

        # Get video file size
        video_size = os.path.getsize(video_path)
        
        # Initialize video upload
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        init_data = {
            "post_info": {
                "title": title,
                "privacy_level": "PUBLIC_TO_EVERYONE",
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": video_size,  # Upload in single chunk if small
                "total_chunk_count": 1
            }
        }
        
        # Initialize upload
        response = requests.post(self.post_url, headers=headers, json=init_data)
        if response.status_code != 200:
            return None
            
        upload_info = response.json()['data']
        publish_id = upload_info['publish_id']
        upload_url = upload_info['upload_url']
        
        # Upload video file
        with open(video_path, 'rb') as f:
            video_data = f.read()
            
        upload_headers = {
            'Content-Type': 'video/mp4',
            'Content-Range': f'bytes 0-{video_size-1}/{video_size}'
        }
        
        upload_response = requests.put(upload_url, headers=upload_headers, data=video_data)
        if upload_response.status_code != 200:
            return None
            
        return publish_id

    def check_post_status(self, publish_id: str) -> dict:
        """Check status of video post"""
        if not self.access_token:
            raise ValueError("Not authenticated - call handle_callback first")
            
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        data = {'publish_id': publish_id}
        response = requests.post(self.status_url, headers=headers, json=data)
        
        if response.status_code == 200:
            return response.json()['data']
        return {'status': 'error'}

def post_to_tiktok(video_path: str, title: str = "Check out this video!") -> bool:
    """Main function to handle TikTok video posting"""
    tiktok = TikTokAPI()
    
    # Get authorization URL - in a real app, redirect user to this URL
    auth_url = tiktok.get_auth_url()
    print(f"Please authorize at: {auth_url}")
    
    # In a real app, this would be handled by your callback endpoint
    code = input("Enter the authorization code from callback URL: ")
    
    # Handle authentication
    if not tiktok.handle_callback(code, tiktok.state):
        print("Authentication failed")
        return False
        
    # Post video
    publish_id = tiktok.post_video(video_path, title)
    if not publish_id:
        print("Failed to initialize video upload")
        return False
        
    # Check status
    status = tiktok.check_post_status(publish_id)
    return status.get('status') == 'success' 