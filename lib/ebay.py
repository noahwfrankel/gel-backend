import os
import httpx
import asyncio
import base64
import time
from typing import Optional

EBAY_API_BASE = "https://api.ebay.com"
EBAY_CLOTHING_CATEGORY = "11450"

# In-memory token cache
_token_cache = {
    "access_token": None,
    "expires_at": 0.0
}

async def get_ebay_token() -> str:
    """Get a valid eBay OAuth token, using cache if available."""
    now = time.time()
    if _token_cache["access_token"] and _token_cache["expires_at"] > now + 60:
        return _token_cache["access_token"]

    app_id = os.getenv("EBAY_APP_ID")
    cert_id = os.getenv("EBAY_CERT_ID")

    if not app_id or not cert_id:
        raise ValueError("EBAY_APP_ID and EBAY_CERT_ID must be set")

    credentials = base64.b64encode(f"{app_id}:{cert_id}".encode()).decode()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{EBAY_API_BASE}/identity/v1/oauth2/token",
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data="grant_type=client_credentials&scope=https://api.ebay.com/oauth/api_scope"
        )
        response.raise_for_status()
        data = response.json()

        _token_cache["access_token"] = data["access_token"]
        _token_cache["expires_at"] = now + data.get("expires_in", 7200)

        return _token_cache["access_token"]

def build_gender_filter(gender: str) -> Optional[str]:
    """Map onboarding gender selection to eBay category filter."""
    # eBay sub-categories within Clothing, Shoes & Accessories:
    # Men's: 1059 (Men's Clothing)
    # Women's: 15724 (Women's Clothing)
    # For unisex we use the parent category 11450
    if gender == "mens":
        return "1059"
    elif gender == "womens":
        return "15724"
    return None  # Use parent category for unisex

async def search_single_keyword(
    keyword: str,
    token: str,
    budget_min: float,
    budget_max: float,
    gender: str,
    limit: int = 3,
    excluded_ids: set[str] | None = None
) -> list[dict]:
    """Search eBay for a single keyword and return normalized items."""

    category_id = build_gender_filter(gender) or EBAY_CLOTHING_CATEGORY

    price_filter = f"price:[{int(budget_min)}..{int(budget_max)}],priceCurrency:USD"
    condition_filter = "conditions:{USED|VERY_GOOD|GOOD|ACCEPTABLE}"

    params = {
        "q": keyword,
        "category_ids": category_id,
        "filter": f"{condition_filter},{price_filter}",
        "sort": "newlyListed",
        "limit": str(limit),
        "fieldgroups": "MATCHING_ITEMS"
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{EBAY_API_BASE}/buy/browse/v1/item_summary/search",
            headers=headers,
            params=params
        )

        if response.status_code != 200:
            return []

        data = response.json()
        items = data.get("itemSummaries", [])

        results = []
        for item in items:
            # Get the best available image
            image_url = None
            if item.get("image"):
                image_url = item["image"].get("imageUrl")
            elif item.get("additionalImages"):
                image_url = item["additionalImages"][0].get("imageUrl")

            if not image_url:
                continue  # Skip items without images

            # Get price
            price_obj = item.get("price", {})
            try:
                price = float(price_obj.get("value", 0))
            except (ValueError, TypeError):
                continue

            if price <= 0:
                continue

            # Get condition
            condition = item.get("condition", "Pre-owned")
            if condition == "USED":
                condition = "Pre-owned"

            item_id = item.get("itemId", "")
            if excluded_ids and item_id and item_id in excluded_ids:
                continue

            results.append({
                "title": item.get("title", ""),
                "price": price,
                "image_url": image_url,
                "item_url": item.get("itemWebUrl", "https://www.ebay.com"),
                "condition": condition,
                "source": "eBay",
                "item_id": item_id
            })

        return results

async def search_fashion_items(
    keywords: list[str],
    budget_min: float,
    budget_max: float,
    gender: str,
    limit: int = 12,
    excluded_ids: list[str] = []
) -> list[dict]:
    """
    Search eBay for fashion items using multiple keywords in parallel.
    Returns deduplicated results up to the limit.
    """
    if not keywords:
        return []

    # Clamp budget to reasonable values
    budget_min = max(0, budget_min)
    budget_max = min(1000, budget_max)
    if budget_max < 10:
        budget_max = 500  # fallback if budget is too narrow

    try:
        token = await get_ebay_token()
    except Exception as e:
        print(f"eBay token error: {e}")
        return []

    # Use top 6 keywords and search 2-3 items each in parallel
    top_keywords = keywords[:6]
    items_per_keyword = max(2, limit // len(top_keywords))
    excluded_set = set(excluded_ids) if excluded_ids else None

    tasks = [
        search_single_keyword(kw, token, budget_min, budget_max, gender, items_per_keyword, excluded_set)
        for kw in top_keywords
    ]

    results_per_keyword = await asyncio.gather(*tasks, return_exceptions=True)

    # Flatten, deduplicate by item_id, and return up to limit
    seen_ids = set()
    seen_titles = set()
    all_items = []

    for result in results_per_keyword:
        if isinstance(result, Exception):
            continue
        for item in result:
            item_id = item.get("item_id", "")
            title_lower = item.get("title", "").lower()[:50]

            # Skip duplicates
            if item_id and item_id in seen_ids:
                continue
            if title_lower in seen_titles:
                continue

            if item_id:
                seen_ids.add(item_id)
            seen_titles.add(title_lower)
            all_items.append(item)

    return all_items[:limit]
