import httpx
import os
import random

# Mock items pool — realistic secondhand fashion items
MOCK_ITEMS = [
    {
        "title": "Vintage Carhartt WIP Double Knee Pant",
        "price": 48.00,
        "image_url": "https://picsum.photos/seed/carhartt/400/500",
        "item_url": "https://www.ebay.com",
        "condition": "Pre-owned",
        "source": "eBay",
    },
    {
        "title": "90s Adidas Trefoil Track Jacket Black",
        "price": 62.00,
        "image_url": "https://picsum.photos/seed/adidas/400/500",
        "item_url": "https://www.ebay.com",
        "condition": "Pre-owned",
        "source": "eBay",
    },
    {
        "title": "Levi's 550 Relaxed Fit Jeans Vintage Wash",
        "price": 35.00,
        "image_url": "https://picsum.photos/seed/levis/400/500",
        "item_url": "https://www.ebay.com",
        "condition": "Pre-owned",
        "source": "eBay",
    },
    {
        "title": "Dickies 874 Work Pants Black Vintage",
        "price": 28.00,
        "image_url": "https://picsum.photos/seed/dickies/400/500",
        "item_url": "https://www.ebay.com",
        "condition": "Pre-owned",
        "source": "eBay",
    },
    {
        "title": "Nike ACG Fleece Pullover 90s Vintage",
        "price": 85.00,
        "image_url": "https://picsum.photos/seed/nikeacg/400/500",
        "item_url": "https://www.ebay.com",
        "condition": "Pre-owned",
        "source": "eBay",
    },
    {
        "title": "Polo Ralph Lauren Oxford Shirt Vintage",
        "price": 32.00,
        "image_url": "https://picsum.photos/seed/polo/400/500",
        "item_url": "https://www.ebay.com",
        "condition": "Pre-owned",
        "source": "eBay",
    },
    {
        "title": "Tommy Hilfiger Windbreaker Jacket 90s",
        "price": 75.00,
        "image_url": "https://picsum.photos/seed/tommy/400/500",
        "item_url": "https://www.ebay.com",
        "condition": "Pre-owned",
        "source": "eBay",
    },
    {
        "title": "Vintage Levi's Denim Trucker Jacket",
        "price": 55.00,
        "image_url": "https://picsum.photos/seed/denim/400/500",
        "item_url": "https://www.ebay.com",
        "condition": "Pre-owned",
        "source": "eBay",
    },
    {
        "title": "Champion Reverse Weave Crewneck Sweatshirt",
        "price": 42.00,
        "image_url": "https://picsum.photos/seed/champion/400/500",
        "item_url": "https://www.ebay.com",
        "condition": "Pre-owned",
        "source": "eBay",
    },
    {
        "title": "Wrangler Western Shirt Pearl Snap Vintage",
        "price": 29.00,
        "image_url": "https://picsum.photos/seed/wrangler/400/500",
        "item_url": "https://www.ebay.com",
        "condition": "Pre-owned",
        "source": "eBay",
    },
    {
        "title": "Stussy Graphic Tee 90s Vintage Single Stitch",
        "price": 95.00,
        "image_url": "https://picsum.photos/seed/stussy/400/500",
        "item_url": "https://www.ebay.com",
        "condition": "Pre-owned",
        "source": "eBay",
    },
    {
        "title": "Patagonia Fleece Synchilla Pullover Vintage",
        "price": 68.00,
        "image_url": "https://picsum.photos/seed/patagonia/400/500",
        "item_url": "https://www.ebay.com",
        "condition": "Pre-owned",
        "source": "eBay",
    },
]


async def search_fashion_items(
    keywords: list[str],
    budget_min: float,
    budget_max: float,
    gender: str,
    limit: int = 12
) -> list[dict]:
    """
    Search for fashion items matching the given keywords and budget.
    Currently returns mock data filtered by budget.
    Replace this with real eBay Browse API calls in Sprint 3.
    """
    # Filter mock items by budget
    filtered = [
        item for item in MOCK_ITEMS
        if budget_min <= item["price"] <= budget_max
    ]

    # If budget filter is too strict, return all items
    if len(filtered) < 4:
        filtered = list(MOCK_ITEMS)

    # Shuffle for variety and return up to limit
    random.shuffle(filtered)
    return filtered[:limit]
