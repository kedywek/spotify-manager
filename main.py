import json
from fastapi import FastAPI, Query, Response, Request
from fastapi.responses import RedirectResponse
from spotify_service import spotify_service
from models import PlaylistListResponse, PlaylistBase

app = FastAPI()

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


@app.get("/playlists/{playlist_id}", response_model = PlaylistBase)
def list_tracks(playlist_id: str, request: Request):

    session_data = request.cookies.get("spotify_session")
    if not session_data:
        return RedirectResponse(url="/login")
    
    token_info = json.loads(session_data)
    
    playlist = spotify_service.get_playlist(token_info['access_token'], playlist_id)
    
    return playlist
