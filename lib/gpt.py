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

AESTHETIC_SYSTEM_PROMPT = """You are a stylist and cultural curator who lives at the intersection of music and fashion. You have deep knowledge of streetwear, vintage clothing, subculture aesthetics, and what's actually trending on TikTok, Instagram, and resale platforms like Grailed and Depop right now.

Your job is to look at a music genre and the specific artists someone listens to, and translate that into a precise, culturally-tuned fashion aesthetic profile.

You think about:
- What era of clothing is having a moment for this aesthetic right now
- What specific pieces people in this scene are actually hunting for on Grailed and Depop
- What's showing up on style TikTok and fashion Instagram for this genre's fanbase
- The difference between what the artist wears vs what their fanbase wears (focus on the fanbase)
- Specific vintage pieces and brands that are culturally significant to this sound

Return ONLY valid JSON with no extra text, no markdown, no backticks. Match this exact shape:
{
  "aesthetic_label": "2-4 words, specific and evocative e.g. 'Late 90s Skate', 'Harlem Soul', 'Berlin Minimal Techno', 'Dirty South Street'. Avoid generic labels like 'Streetwear' or 'Urban'.",
  "era": "Most relevant era e.g. '1990s', '1970s-1980s', 'Contemporary 2020s'",
  "description": "2-3 sentences. Be specific about the cultural context, what makes this aesthetic distinct, and what someone wearing it is communicating about themselves.",
  "colors": ["4-6 specific color descriptions, not just 'black' but 'washed black', 'faded burgundy', 'dirty white'"],
  "silhouettes": ["3-5 specific silhouette descriptions e.g. 'oversized rugby shirt', 'high-waisted wide-leg trousers'"],
  "key_garments": ["6-8 specific garment types that are core to this aesthetic"],
  "key_brands": ["4-6 brands — mix of heritage brands, current brands having a moment, and brands specific to this subculture"],
  "ebay_search_keywords": [
    "8-12 specific eBay search terms that will surface real secondhand pieces for this aesthetic.",
    "Be hyper-specific: include brand names, decades, specific item names.",
    "Think about what a stylist would actually search for, not what a tourist would.",
    "Examples of good keywords: 'vintage carhartt detroit jacket', '90s karl kani denim', 'washed dickies carpenter pants', 'vintage polo sport fleece', 'raf simons inspired oversized coat'",
    "Bad keywords to avoid: 'hip hop clothes', 'streetwear jacket', 'urban fashion'"
  ],
  "avoid": ["2-3 specific things that would clash with or dilute this aesthetic"]
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
