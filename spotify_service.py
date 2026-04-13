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
            scope = "user-read-private playlist-read-private playlist-modify-public playlist-modify-private",
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
            "autocorrect": 1,
            "format": "json",
            
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
        def extract_data(items):
            for item in items:
                t = item.get('item')
                if not t or not t.get('id'):
                    continue
                if t['type'] == 'episode':
                    continue
                tracks.append({
                    "id": t["id"],
                    "name": t["name"],
                    "artist": t["artists"][0]["name"] if t.get("artists") else "Unknown",
                    "year": t["album"]["release_date"][:4] if t.get("album") else "0000"
                })
        extract_data(results['items'])
        while results['next']:
            results = sp.next(results)
            extract_data(results['items'])
        return tracks
    
    async def _fetch_lastfm_api(self, client, params):
        try:
            await asyncio.sleep(0.21)
            r = await client.get(self.lastfm_base_url, params=params, timeout=5)
            if r.status_code != 200:
                return []
            data = r.json()
            return data.get('toptags', {}).get('tag', [])
        except Exception as e:
            print(f"Request error: {repr(e)}")
            return []
        
    async def get_tags_batch(self, tracks_to_get):
        sem = asyncio.Semaphore(5)
        async with httpx.AsyncClient() as client:
            tasks = [self._fetch_track_tag(client, track, sem) for track in tracks_to_get]
            return await asyncio.gather(*tasks)
        

    async def _fetch_track_tag(self, client, track, sem):
        async with sem:
            
            track_params = {
                "method": "track.gettoptags",
                "artist": track['artist'],
                "track": track['name'],
                "api_key": self.lastfm_api_key,
                "autocorrect": 1,
                "format": "json"
            }
            
            raw_tags = await self._fetch_lastfm_api(client, track_params)
            
            if not raw_tags:
                artist_params = {
                    "method": "artist.gettoptags",
                    "artist": track['artist'],
                    "api_key": self.lastfm_api_key,
                    "autocorrect": 1,
                    "format": "json"
                }
                raw_tags = await self._fetch_lastfm_api(client, artist_params)
            
            processed_tags = [t['name'].lower() for t in raw_tags[:5]]
            return {
                "id": track['id'],
                "tags": processed_tags
            }
        

    def create_playlist_from_cluster(self, token: str, name: str, track_ids: list):
        sp = Spotify(auth=token)
        try:
            new_playlist = sp.current_user_playlist_create(
                # user=user_id, 
                name=name, 
                public=False, 
                collaborative=False,
                description="generated by playlist-manager"
            )
            playlist_id = new_playlist['id']
            
            for i in range(0, len(track_ids), 100):
                batch = track_ids[i:i+100]
                sp.playlist_add_items(playlist_id, batch)
                
            return new_playlist['external_urls']['spotify']
        except Exception as e:
            print(f"error {repr(e)}")
            raise e
    
spotify_service = SpotifyService()