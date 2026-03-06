from fastapi import FastAPI, Query
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Pydantic will automatically link these to your .env keys
    spotipy_client_id: str
    spotipy_client_secret: str
    spotipy_redirect_uri: str

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

app = FastAPI(title="Spotify AI Manager")

# Initialize OAuth
sp_oauth = SpotifyOAuth(
    client_id=settings.spotipy_client_id,
    client_secret=settings.spotipy_client_secret,
    redirect_uri=settings.spotipy_redirect_uri,
    scope="user-read-private playlist-read-private"
)

@app.get("/")
def index():
    return {"status": "Ready", "docs": "/docs"}

@app.get("/login")
def login():
    """Step 1: Get the Spotify authorization URL."""
    auth_url = sp_oauth.get_authorize_url()
    return {"auth_url": auth_url}

@app.get("/callback")
def callback(code: str = Query(...)):
    """Step 2: Spotify redirects here with a 'code'."""
    # Exchange code for access token
    token_info = sp_oauth.get_access_token(code)
    access_token = token_info['access_token']
    
    # Use the token to get user info
    sp = Spotify(auth=access_token)
    user_details = sp.current_user()
    
    return {
        "message": f"Hello {user_details['display_name']}!",
        "spotify_id": user_details['id'],
        "followers": user_details['followers']['total']
    }