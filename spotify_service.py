from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from config import settings

class SpotifyService:
    def __init__(self):
        self.sp_oauth = SpotifyOAuth(
            client_id=settings.spotipy_client_id,
            client_secret=settings.spotipy_client_secret,
            redirect_uri=settings.spotipy_redirect_uri,
            scope="user-read-private playlist-read-private",
            show_dialog=True,
            cache_path=None
        )

    def get_auth_url(self):
        return self.sp_oauth.get_authorize_url()

    def get_token(self, code: str):
        return self.sp_oauth.get_access_token(code)

    def get_user_playlists(self, token: str):
        sp = Spotify(auth=token)
        results = sp.current_user_playlists(limit=50)
        
        playlists = []
        for item in results['items']:
            playlists.append({
                "id": item['id'],
                "name": item['name'],
                "description": item['description'],
                "total_tracks": item['items']['total'] if item['items'] else 0,
                "image_url": item['images'][0]['url'] if item['images'] else None
            })
        return playlists, results['total']

spotify_service = SpotifyService()