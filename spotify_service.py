from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from config import settings
import requests
import asyncio
import httpx
import re

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
        self.lastfm_api_key = settings.lastfm_api_key
        self.lastfm_base_url = "http://ws.audioscrobbler.com/2.0/"

    def get_auth_url(self):
        return self.sp_oauth.get_authorize_url()

    def get_token(self, code: str):
        return self.sp_oauth.get_access_token(code)
    
    def get_spotify_client(self, token_info: dict):
        if self.sp_oauth.is_token_expired(token_info):
            token_info = self.sp_oauth.refresh_access_token(token_info['refresh_token'])
        return Spotify(auth=token_info['access_token']), token_info
    
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

    def get_playlist(self, token: str, playlist_id: str):
        sp = Spotify(auth=token)
        result = sp.playlist(playlist_id=playlist_id)
        images = result.get('images', [])
        
        playlist = {
            "id": result['id'],
            "name": result['name'],
            "description": result['description'],
            "image_url": images[0]['url'] if images else None
            }
        
        return result
    
    def get_track(self, token: str, track_id: str):
        sp = Spotify(auth=token)
        result = sp.track(track_id = track_id)
        
        track = {
            "artists": [
                {"id": artist["id"], "name": artist["name"]} 
                for artist in result["artists"]
            ],
            "id" : result["id"],
            "name" : result["name"]
        }
        return track
   
    def get_lastfm_tags(self, artist: str, track:str):
        
        params = {
            "method": "track.gettoptags",
            "artist": artist,
            "track": track,
            "api_key": self.lastfm_api_key,
            "format": "json"
        }
        try:
            response = requests.get(self.lastfm_base_url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            tags_list = data.get("toptags", {}).get("tag", [])
            return [tag["name"].lower() for tag in tags_list[:10]]
        except Exception as e:
            print(f"Last.fm error: {e}")
            return []
    
    def get_playlist_tracks(self, token: str, playlist_id: str):
        from spotipy import Spotify
        sp = Spotify(auth=token)
        
        results = sp.playlist_items(playlist_id, limit=100)
        tracks = []
        for item in results.get('items', []):
            t = item.get('item')
            if not t or not t.get('id'):
                continue
            
            tracks.append({
                "id": t["id"],
                "name": t["name"],
                "artist": t["artists"][0]["name"] if t.get("artists") else "Unknown",
                "year": t["album"]["release_date"][:4] if t.get("album") and t["album"].get("release_date") else "0000"
            })
        return tracks
        
    async def get_tags_batch(self, tracks_to_get):

        sem = asyncio.Semaphore(5)

        async with httpx.AsyncClient() as client:
            tasks = []
            for track in tracks_to_get:
                tasks.append(self._fetch_track_tag(client, track, sem))
            return await asyncio.gather(*tasks)

    async def _fetch_track_tag(self, client, track, sem):
        async with sem:
            params = {
                "method": "track.gettoptags",
                "artist": track['artist'],
                "track": track['name'],
                "api_key": self.lastfm_api_key,
                "format": "json"
            }
        try:
            await asyncio.sleep(0.21)
            r = await client.get("http://ws.audioscrobbler.com/2.0/", params=params, timeout=5)
            data = r.json()
            tags = data.get('toptags', {}).get('tag', [])
            return {
                "id": track['id'],
                "tags": [t['name'].lower() for t in tags[:5]]
            }
        except Exception:
            return {"id": track['id'], "tags": []}
spotify_service = SpotifyService()