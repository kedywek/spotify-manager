from pydantic import BaseModel
from typing import List
from sqlalchemy import Column, String
from database import Base

class TrackCache(Base):
    __tablename__ = "track_cache"

    spotify_id = Column(String, primary_key=True, index=True)
    tags = Column(String)

class PlaylistBase(BaseModel):
    id: str
    name: str
    description: str | None = None
    total_tracks: int
    image_url: str | None = None    

class PlaylistListResponse(BaseModel):
    playlists: List[PlaylistBase]
    total: int
