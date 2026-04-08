import json
from fastapi import FastAPI, Query, Response, Request
from fastapi.responses import RedirectResponse
from spotify_service import spotify_service
from models import PlaylistListResponse, PlaylistBase
from fastapi import Depends
from sqlalchemy.orm import Session
from database import get_db, engine
import models


app = FastAPI()
models.Base.metadata.create_all(bind=engine)

@app.get("/login")
def login():
    return {"auth_url": spotify_service.get_auth_url()}

@app.get("/callback")
def callback(code: str):
    token_info = spotify_service.get_token(code)
    response = RedirectResponse(url="/playlists")
    response.set_cookie(
        key="spotify_session",
        value=json.dumps(token_info),
        httponly=True
    )
    return response

@app.get("/playlists", response_model=PlaylistListResponse)
def list_playlists(request: Request):
    session_data = request.cookies.get("spotify_session")
    
    if not session_data:
        return RedirectResponse(url="/login")
    token_info = json.loads(session_data)
    items, total = spotify_service.get_user_playlists(token_info['access_token'])
    
    return {"playlists": items, "total": total}


@app.get("/playlists/{playlist_id}")
def detail_playlist(playlist_id: str, request: Request):

    session_data = request.cookies.get("spotify_session")
    if not session_data:
        return RedirectResponse(url="/login")
    
    token_info = json.loads(session_data)
    
    playlist = spotify_service.get_playlist(token_info['access_token'], playlist_id)
    
    return playlist

@app.get("/track/{track_id}")
def detail_track(track_id: str, request: Request, db: Session = Depends(get_db)):

    session_data = request.cookies.get("spotify_session")
    if not session_data:
        return RedirectResponse(url="/login")
    
    token_info = json.loads(session_data)

    cached_entry = db.query(models.TrackCache).filter(models.TrackCache.spotify_id == track_id).first()

    track = spotify_service.get_track(token_info['access_token'], track_id)
    artist_name = track['artists'][0]["name"]
    track_name = track['name']

    if cached_entry:
        tags = cached_entry.tags.split(",")
        track["data_source"] = "local_cache"
    else:
        tags = spotify_service.get_lastfm_tags(artist=artist_name, track=track_name)
        new_cache = models.TrackCache(spotify_id=track_id, tags=",".join(tags))
        db.add(new_cache)
        db.commit()
        track["data_source"] = "lastfm_api"
        
    track["tags"] = tags
    return track