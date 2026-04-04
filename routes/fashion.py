from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from lib.ebay import search_fashion_items, CATEGORY_MAP

router = APIRouter()


class FashionSearchRequest(BaseModel):
    keywords: list[str]
    budget_min: float = 0
    budget_max: float = 500
    gender: str = "unisex"
    limit: int = 12
    excluded_item_ids: list[str] = []


class CategorySearchRequest(BaseModel):
    category: str  # "pants", "shirts", "hoodies", "jackets", "sweaters", "shoes", "shorts", "accessories"
    aesthetic_keywords: list[str]
    budget_min: float = 0
    budget_max: float = 500
    gender: str = "unisex"
    excluded_item_ids: list[str] = []
    limit: int = 12


class FashionItem(BaseModel):
    title: str
    price: float
    image_url: str
    item_url: str
    condition: str
    source: str
    item_id: str = ""


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
            excluded_ids=request.excluded_item_ids,
        )
        return {"items": items, "total": len(items)}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fashion search failed: {str(e)}"
        )


@router.post("/search-by-category", response_model=FashionSearchResponse)
async def search_fashion_by_category(request: CategorySearchRequest):
    category = request.category.lower().strip()
    if category not in CATEGORY_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown category '{category}'. Valid: {', '.join(CATEGORY_MAP.keys())}"
        )

    if not request.aesthetic_keywords:
        raise HTTPException(status_code=400, detail="At least one aesthetic keyword is required")

    try:
        items = await search_fashion_items(
            keywords=request.aesthetic_keywords,
            budget_min=request.budget_min,
            budget_max=request.budget_max,
            gender=request.gender,
            limit=request.limit,
            excluded_ids=request.excluded_item_ids,
            category_filter=category,
        )
        return {"items": items, "total": len(items)}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Category search failed: {str(e)}"
        )
