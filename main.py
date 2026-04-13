import json
from fastapi import FastAPI, Query, Response, Request
from fastapi.responses import RedirectResponse
from spotify_service import spotify_service
from models import PlaylistListResponse, PlaylistBase
from fastapi import Depends
from sqlalchemy.orm import Session
from database import get_db, engine
import models
from clusterer import MusicClusterer


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

@app.get("/playlists/{playlist_id}/tags")
async def get_playlist_tags(playlist_id: str, request: Request, db: Session = Depends(get_db)):
    session_data = request.cookies.get("spotify_session")
    if not session_data:
        return RedirectResponse(url="/login")
    token = json.loads(session_data)['access_token']

    tracks = spotify_service.get_playlist_tracks(token, playlist_id)
    tracks_ids = [t['id'] for t in tracks]

    cached = db.query(models.TrackCache).filter(models.TrackCache.spotify_id.in_(tracks_ids)).all()
    cached_ids = {c.spotify_id for c in cached}

    ids_to_fetch = set(tracks_ids) - cached_ids

    if ids_to_fetch:
        unique_to_fetch = {t['id']: t for t in tracks if t['id'] in ids_to_fetch}.values()

        new_tags_data = await spotify_service.get_tags_batch(list(unique_to_fetch))
        new_entries = [
            models.TrackCache(spotify_id=item['id'], tags=",".join(item['tags'])) 
            for item in new_tags_data
        ]
        db.add_all(new_entries)
        db.commit()

    final_cache = db.query(models.TrackCache).filter(models.TrackCache.spotify_id.in_(tracks_ids)).all()
    tag_map = {c.spotify_id: c.tags.split(",") for c in final_cache}

    for t in tracks:
        t['tags'] = tag_map.get(t['id'], [])

    return tracks

@app.get("/playlists/{playlist_id}/clusters")
async def get_clusters(playlist_id: str, request: Request, db: Session = Depends(get_db), n: int = 5):
    tracks = await get_playlist_tags(playlist_id, request, db)
    
    clusterer = MusicClusterer(n_clusters=n)
    clustered_tracks = clusterer.process(tracks)
    
    keywords = clusterer.get_cluster_keywords()
    
    response = {
        "cluster_definitions": keywords,
        "clusters": {}
    }
    
    for i in range(n):
        response["clusters"][i] = [t for t in clustered_tracks if t['cluster'] == i]
        
    return response

@app.post("/playlists/{playlist_id}/export")
async def export_clusters_to_spotify(playlist_id: str, request: Request, db: Session = Depends(get_db), n: int = 5):
    session_data = request.cookies.get("spotify_session")
    token = json.loads(session_data)['access_token']
    tracks_with_tags = await get_playlist_tags(playlist_id, request, db)
    
    clusterer = MusicClusterer(n_clusters=n)
    clustered_tracks = clusterer.process(tracks_with_tags)
    keywords = clusterer.get_cluster_keywords()

    created_playlists = []
    
    for i in range(n):
        track_ids = [t['id'] for t in clustered_tracks if t['cluster'] == i]
        
        if not track_ids:
            continue
            
        cluster_name = f"Vibe: {', '.join(keywords[i][:3]).title()}"
        
        url = spotify_service.create_playlist_from_cluster(
            token=token,
            name=cluster_name,
            track_ids=track_ids
        )
        created_playlists.append({"name": cluster_name, "url": url})

    return {"message": "Success!", "exported_playlists": created_playlists}