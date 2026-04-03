from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from lib.ebay import search_fashion_items

router = APIRouter()

class FashionSearchRequest(BaseModel):
    keywords: list[str]
    budget_min: float = 0
    budget_max: float = 500
    gender: str = "unisex"
    limit: int = 12
    excluded_item_ids: list[str] = []

class FashionItem(BaseModel):
    title: str
    price: float
    image_url: str
    item_url: str
    condition: str
    source: str

class FashionSearchResponse(BaseModel):
    items: list[FashionItem]
    total: int

@router.post("/search", response_model=FashionSearchResponse)
async def search_fashion(request: FashionSearchRequest):
    if not request.keywords:
        raise HTTPException(status_code=400, detail="At least one keyword is required")

    try:
        items = await search_fashion_items(
            keywords=request.keywords,
            budget_min=request.budget_min,
            budget_max=request.budget_max,
            gender=request.gender,
            limit=request.limit,
            excluded_ids=request.excluded_item_ids
        )
        return {"items": items, "total": len(items)}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fashion search failed: {str(e)}"
        )
