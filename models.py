from pydantic import BaseModel
from typing import List

class PlaylistBase(BaseModel):
    id: str
    name: str
    description: str | None = None
    total_tracks: int
    image_url: str | None = None    

class PlaylistListResponse(BaseModel):
    playlists: List[PlaylistBase]
    total: int
