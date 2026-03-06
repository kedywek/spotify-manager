from fastapi import FastAPI
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    spotify_client_id: str
    spotify_client_secret: str
    spotify_redirect_uri: str = "http://localhost:8000/callback"

    class Config:
        env_file = ".env"

settings = Settings()

app = FastAPI(title="Spotify Playlist Manager")

# Spotify OAuth Setup
sp_oauth = SpotifyOAuth(
    client_id=settings.spotify_client_id,
    client_secret=settings.spotify_client_secret,
    redirect_uri=settings.spotify_redirect_uri,
    scope="playlist-modify-public playlist-modify-private"
)

@app.get("/")
async def root():
    return {"message": "API is running", "ai_integration": "pending"}

@app.get("/login")
async def login():
    """Returns the Spotify authorization URL."""
    auth_url = sp_oauth.get_authorize_url()
    return {"login_url": auth_url}

@app.get("/callback")
async def callback(code: str):
    """Handles the redirect from Spotify after user login."""
    token_info = sp_oauth.get_access_token(code)
    return {"message": "Login successful", "token": "Retrieved"}