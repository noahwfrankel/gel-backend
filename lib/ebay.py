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

# ---------------------------------------------------------------------------
# Brand taste scores (fashion scoring schema v1.0)
# ---------------------------------------------------------------------------

BRAND_TASTE_SCORES = {
    # Workwear
    "carhartt wip": 81, "carhartt": 85, "filson": 90, "dickies": 78,
    "red kap": 75, "engineered garments": 86,
    # Denim
    "levi's": 82, "levis": 82, "nudie jeans": 79, "a.p.c.": 83,
    "apc": 83, "lee": 76, "wrangler": 75,
    # Outerwear
    "barbour": 84, "schott nyc": 85, "schott": 85, "woolrich": 83,
    "patagonia": 85, "the north face": 80, "north face": 80,
    "arc'teryx": 82, "arcteryx": 82,
    # Sportswear
    "nike acg": 80, "champion": 76, "nike": 78, "adidas": 78,
    "russell athletic": 72, "fila": 74, "ellesse": 73, "umbro": 72,
    # Streetwear
    "stüssy": 83, "stussy": 83, "supreme": 83, "palace": 81,
    "aimé leon dore": 86, "aime leon dore": 86, "noah": 80,
    "corteiz": 83, "human made": 80,
    # Heritage
    "l.l. bean": 81, "llbean": 81, "pendleton": 85,
    "brooks brothers": 82, "polo ralph lauren": 78, "ralph lauren": 78,
    # Contemporary
    "our legacy": 85, "acne studios": 85, "cos": 80, "lemaire": 91,
    "margaret howell": 84,
    # Japanese
    "needles": 85, "kapital": 88, "visvim": 89, "nanamica": 84,
    "beams plus": 83, "wtaps": 82,
    # Luxury
    "the row": 95, "rick owens": 93, "maison margiela": 93,
    "loewe": 93, "bottega veneta": 92,
    # Low quality — filter OUT (score 0)
    "shein": 0, "fashion nova": 0, "forever 21": 40,
    "boohoo": 30, "prettylittlething": 25,
    # Borderline — allow but low-ranked
    "h&m": 60, "zara": 65, "asos": 55,
}

MIN_TASTE_SCORE = 65

ERA_BONUSES = {
    "vintage gap": 12, "90s gap": 12, "80s gap": 12,
    "reverse weave": 10, "champion reverse": 10,
    "big e": 15, "redline": 15, "lvc": 15,
    "nike acg": 10, "acg 90s": 10, "acg 2000s": 10,
    "prada sport": 15, "linea rossa": 15,
    "russell athletic pro": 10, "pro cotton": 10,
}


def get_brand_score(title: str) -> tuple[int, int]:
    """Returns (taste_score, era_bonus) for an item based on its title."""
    title_lower = title.lower()

    # Check zero-score brands first
    for brand, score in BRAND_TASTE_SCORES.items():
        if brand in title_lower and score == 0:
            return 0, 0

    # Find highest matching brand score (check longer names first)
    best_score = 50  # default for unknown brands
    for brand in sorted(BRAND_TASTE_SCORES, key=len, reverse=True):
        score = BRAND_TASTE_SCORES[brand]
        if brand in title_lower:
            best_score = max(best_score, score)

    era_bonus = 0
    for era_key, bonus in ERA_BONUSES.items():
        if era_key in title_lower:
            era_bonus = max(era_bonus, bonus)

    return best_score, era_bonus


def score_item(item: dict) -> float:
    """
    ranking_score = (taste_score × 0.5) + (condition_score × 0.35) + (era_bonus_scaled × 0.15)
    """
    taste_score, era_bonus = get_brand_score(item.get("title", ""))
    if taste_score == 0:
        return 0.0

    condition = item.get("condition", "").lower()
    condition_map = {
        "new with tags": 100, "new without tags": 95, "like new": 90,
        "very good": 85, "good": 75, "acceptable": 60,
        "pre-owned": 75, "used": 70,
    }
    condition_score = 75
    for cond, s in condition_map.items():
        if cond in condition:
            condition_score = s
            break

    return (taste_score * 0.5) + (condition_score * 0.35) + (min(era_bonus * 10, 100) * 0.15)


# ---------------------------------------------------------------------------
# eBay category maps
# ---------------------------------------------------------------------------

CATEGORY_MAP = {
    "pants": "57989",
    "shirts": "57990",
    "hoodies": "57988",
    "jackets": "57988",
    "sweaters": "11484",
    "shoes": "93427",
    "shorts": "57989",
    "accessories": "2340",
}


# ---------------------------------------------------------------------------
# Token management
# ---------------------------------------------------------------------------

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
    if gender == "mens":
        return "1059"
    elif gender == "womens":
        return "15724"
    return None


# ---------------------------------------------------------------------------
# Core search
# ---------------------------------------------------------------------------

async def search_single_keyword(
    keyword: str,
    token: str,
    budget_min: float,
    budget_max: float,
    gender: str,
    limit: int = 3,
    excluded_ids: set[str] | None = None,
    category_id_override: str | None = None,
) -> list[dict]:
    """Search eBay for a single keyword, score results, filter low-quality."""

    if category_id_override:
        category_id = category_id_override
    else:
        category_id = build_gender_filter(gender) or EBAY_CLOTHING_CATEGORY

    price_filter = f"price:[{int(budget_min)}..{int(budget_max)}],priceCurrency:USD"
    condition_filter = "conditions:{USED|VERY_GOOD|GOOD|ACCEPTABLE}"

    params = {
        "q": keyword,
        "category_ids": category_id,
        "filter": f"{condition_filter},{price_filter}",
        "sort": "newlyListed",
        "limit": str(limit * 3),  # Fetch more so we have candidates after filtering
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
            image_url = None
            if item.get("image"):
                image_url = item["image"].get("imageUrl")
            elif item.get("additionalImages"):
                image_url = item["additionalImages"][0].get("imageUrl")

            if not image_url:
                continue

            price_obj = item.get("price", {})
            try:
                price = float(price_obj.get("value", 0))
            except (ValueError, TypeError):
                continue

            if price <= 0:
                continue

            item_id = item.get("itemId", "")
            if excluded_ids and item_id and item_id in excluded_ids:
                continue

            condition = item.get("condition", "Pre-owned")
            if condition == "USED":
                condition = "Pre-owned"

            candidate = {
                "title": item.get("title", ""),
                "price": price,
                "image_url": image_url,
                "item_url": item.get("itemWebUrl", "https://www.ebay.com"),
                "condition": condition,
                "source": "eBay",
                "item_id": item_id,
            }

            ranking = score_item(candidate)
            if ranking < MIN_TASTE_SCORE:
                continue

            candidate["_score"] = ranking
            results.append(candidate)

        # Sort by score descending
        results.sort(key=lambda x: x.get("_score", 0), reverse=True)

        # Remove internal score field before returning
        for r in results:
            r.pop("_score", None)

        return results[:limit]


async def search_fashion_items(
    keywords: list[str],
    budget_min: float,
    budget_max: float,
    gender: str,
    limit: int = 12,
    excluded_ids: list[str] = [],
    category_filter: str = "",
) -> list[dict]:
    """
    Search eBay for fashion items using multiple keywords in parallel.
    Returns deduplicated, taste-scored results up to limit.
    """
    if not keywords:
        return []

    budget_min = max(0, budget_min)
    budget_max = min(1000, budget_max)
    if budget_max < 10:
        budget_max = 500

    try:
        token = await get_ebay_token()
    except Exception as e:
        print(f"eBay token error: {e}")
        return []

    excluded_set = set(excluded_ids) if excluded_ids else None
    category_id_override = CATEGORY_MAP.get(category_filter.lower()) if category_filter else None

    top_keywords = keywords[:6]
    items_per_keyword = max(2, limit // len(top_keywords))

    tasks = [
        search_single_keyword(
            kw, token, budget_min, budget_max, gender,
            items_per_keyword, excluded_set, category_id_override
        )
        for kw in top_keywords
    ]

    results_per_keyword = await asyncio.gather(*tasks, return_exceptions=True)

    seen_ids: set[str] = set()
    seen_titles: set[str] = set()
    all_items: list[dict] = []

    for result in results_per_keyword:
        if isinstance(result, Exception):
            continue
        for item in result:
            item_id = item.get("item_id", "")
            title_lower = item.get("title", "").lower()[:50]

            if item_id and item_id in seen_ids:
                continue
            if title_lower in seen_titles:
                continue

            if item_id:
                seen_ids.add(item_id)
            seen_titles.add(title_lower)
            all_items.append(item)

    return all_items[:limit]
