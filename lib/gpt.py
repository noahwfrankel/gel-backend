import os
import json
from openai import AsyncOpenAI


def _get_client() -> AsyncOpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "paste_your_key_here":
        raise ValueError(
            "OPENAI_API_KEY is not set or is still the placeholder. Add your key to .env"
        )
    return AsyncOpenAI(api_key=api_key)

AESTHETIC_SYSTEM_PROMPT = """You are a music culture and fashion expert with deep knowledge of how musical genres connect to visual aesthetics and clothing styles throughout history.

Given a music genre and a list of artists that represent it, return a detailed aesthetic profile as a JSON object.

Return ONLY valid JSON with no extra text, no markdown, no backticks. The JSON must match this exact shape:
{
  "aesthetic_label": "string (2-4 words, e.g. 'Late 90s Skate', 'Harlem Soul', 'Berlin Techno')",
  "era": "string (e.g. '1990s', '1970s-1980s', 'Contemporary')",
  "description": "string (2-3 sentences describing the overall aesthetic and its cultural roots)",
  "colors": ["array of 4-6 color names that define this aesthetic, e.g. 'washed black', 'burnt orange'"],
  "silhouettes": ["array of 3-5 silhouette descriptions, e.g. 'oversized hoodies', 'wide-leg trousers'"],
  "key_garments": ["array of 5-8 specific garment types core to this aesthetic"],
  "key_brands": ["array of 4-6 brands historically associated with this aesthetic"],
  "ebay_search_keywords": ["array of 8-12 specific search terms to find secondhand items for this aesthetic on eBay, be specific e.g. 'vintage adidas track jacket 90s', 'washed black cargo pants', 'dickies work pants vintage'"],
  "avoid": ["array of 2-3 things that would clash with this aesthetic"]
}"""

async def get_aesthetic_from_genre(genre: str, artists: list[str]) -> dict:
    client = _get_client()
    artists_str = ", ".join(artists) if artists else "unknown artists"

    user_prompt = f"""Genre: {genre}
Representative artists from this person's listening history: {artists_str}

Generate a fashion aesthetic profile for someone who listens to this genre."""

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": AESTHETIC_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=800,
        response_format={"type": "json_object"}
    )

    raw = response.choices[0].message.content
    return json.loads(raw)
