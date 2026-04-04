from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from lib.gpt import get_aesthetic_from_genre

router = APIRouter()

class AestheticRequest(BaseModel):
    genre: str
    artists: list[str] = []

class AestheticResponse(BaseModel):
    aesthetic_label: str
    era: str = ""
    description: str
    colors: list[str]
    silhouettes: list[str] = []
    key_garments: list[str]
    key_brands: list[str] = []
    ebay_search_keywords: list[str]
    artist_influence: list[str] = []
    buying_push: str = ""
    avoid: list[str] = []

@router.post("/from-genre", response_model=AestheticResponse)
async def get_aesthetic(request: AestheticRequest):
    if not request.genre:
        raise HTTPException(status_code=400, detail="Genre is required")

    try:
        result = await get_aesthetic_from_genre(
            genre=request.genre,
            artists=request.artists
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate aesthetic: {str(e)}"
        )
