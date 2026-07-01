"""Search matcher that scores cached listings against a user query using Claude Haiku.

Flow:
1. Pre-filter cached listings by any structured criteria (suburb, price, beds)
2. Send a batch of listing summaries + the user query to Haiku
3. Haiku returns match scores and reasons for each listing
4. Results are sorted by score and returned

This replaces the expensive Sonnet + web search approach — Haiku is ~60x cheaper
and we're searching our own DB instead of the live web.
"""

import json
import logging
import re

import httpx

logger = logging.getLogger(__name__)

HAIKU_MODEL = "claude-haiku-4-5-20251001"
API_URL = "https://api.anthropic.com/v1/messages"


def _build_scoring_prompt(query: str, listings: list[dict]) -> str:
    """Build a prompt that asks Haiku to score listings against the query."""
    listings_text = ""
    for i, l in enumerate(listings):
        desc_preview = (l.get("description") or "")[:400]
        amenities = ", ".join(l.get("amenities") or [])
        listings_text += (
            f"\n[{i}] {l['title']} | {l['location']} | {l['price_display']}"
            f" | {l.get('bedrooms', '?')} bed, {l.get('bathrooms', '?')} bath"
            f" | {l.get('size_sqm', '?')} m²"
            f" | Furnished: {l.get('furnished', 'unknown')}"
            f" | Pets: {l.get('pets_allowed', 'unknown')}"
            f" | Amenities: {amenities or 'none listed'}"
            f"\n  {desc_preview}"
        )

    return (
        f"You are a Cape Town rental property matching expert.\n\n"
        f"USER SEARCH: \"{query}\"\n\n"
        f"Score each listing 0-100 based on how well it matches what the user is looking for.\n\n"
        f"IMPORTANT: Read each listing's description carefully for these specific features:\n"
        f"- VIEWS & FEEL: sea views, mountain views, natural light/sunlight, quiet street, "
        f"balcony/patio, walk to beach, walkable area, garden, morning sun/north-facing, trendy area\n"
        f"- BUILDING: pool, gym, 24hr security, secure parking, garage, lift/elevator, "
        f"fibre internet, solar/backup power/generator, boutique building, concierge\n"
        f"- LIFESTYLE: modern finishes/renovated, open plan, storage/built-in cupboards, "
        f"pet friendly, work from home/study, lock-up-and-go, entertaining space, "
        f"family friendly, near schools, privacy/not overlooked\n"
        f"- LEASE & BILLING: short lease/month-to-month, bills/water/levies included\n"
        f"- BEDROOMS: en-suite bathroom, guest bathroom/toilet, studio/bachelor\n"
        f"- COMFORT: aircon/air conditioning, underfloor heating, dishwasher, washing machine\n\n"
        f"A listing that explicitly mentions a requested feature in its description should score "
        f"much higher than one that doesn't. The description is the most important signal.\n\n"
        f"LISTINGS:{listings_text}\n\n"
        f"Return JSON only — an array of objects, one per listing:\n"
        f'[{{"index":0,"score":85,"matched":["sea views","2 beds","secure parking"],'
        f'"not_matched":["no pool mentioned"],"reason":"Ocean-facing 2-bed with the sea views and parking requested"}}]\n'
        f"Only include listings scoring 40+. Omit poor matches entirely."
    )


def _parse_scores(raw: str) -> list[dict]:
    """Parse the JSON array of scores from Haiku's response."""
    # Strip markdown fences
    s = re.sub(r"```json\s*", "", raw, flags=re.IGNORECASE)
    s = re.sub(r"```\s*", "", s).strip()
    # Find the array
    a = s.find("[")
    b = s.rfind("]")
    if a == -1 or b == -1:
        raise ValueError("No JSON array found in response")
    return json.loads(s[a : b + 1])


async def score_listings(
    api_key: str,
    query: str,
    listings: list[dict],
    max_results: int = 10,
) -> list[dict]:
    """Score a batch of cached listings against a user query using Claude Haiku.

    Args:
        api_key: Anthropic API key
        query: User's natural language search query
        listings: List of listing dicts from cached_listings table
        max_results: Max results to return

    Returns:
        List of scored results sorted by match_score descending.
    """
    if not listings:
        return []

    prompt = _build_scoring_prompt(query, listings)

    body = {
        "model": HAIKU_MODEL,
        "max_tokens": 4000,
        "messages": [{"role": "user", "content": prompt}],
    }

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(API_URL, json=body, headers=headers)
        resp.raise_for_status()

    data = resp.json()
    text = "".join(b["text"] for b in data.get("content", []) if b.get("type") == "text")

    scores = _parse_scores(text)

    # Merge scores back into listing data
    results = []
    for score_item in scores:
        idx = score_item.get("index")
        if idx is None or idx >= len(listings):
            continue

        listing = listings[idx]
        results.append({
            "title": listing["title"],
            "location": listing["location"],
            "price": listing["price_display"],
            "beds": listing.get("bedrooms"),
            "baths": listing.get("bathrooms"),
            "size": f"{listing['size_sqm']} m²" if listing.get("size_sqm") else None,
            "furnished": listing.get("furnished"),
            "pets": listing.get("pets_allowed"),
            "lease": None,
            "amenities": listing.get("amenities", []),
            "match_score": score_item.get("score", 0),
            "matched": score_item.get("matched", []),
            "not_matched": score_item.get("not_matched", []),
            "match_reason": score_item.get("reason", ""),
            "url": listing["source_url"],
            "source": listing["source"],
            "image_url": listing.get("image_url"),
            "availability": listing.get("available_from", "now"),
        })

    results.sort(key=lambda r: r.get("match_score", 0), reverse=True)
    return results[:max_results]
