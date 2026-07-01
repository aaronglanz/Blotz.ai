"""Generate demo search results tailored to a user's query.

Used when demo mode is enabled or ANTHROPIC_API_KEY is not set,
so the frontend can show a full results experience with rankings,
matched/not-matched tags, scores, and realistic Cape Town rental data.
"""

import random
import re

DEMO_LISTINGS = [
    {
        "title": "Luxury 3-Bed Penthouse with Panoramic Sea Views",
        "location": "Camps Bay",
        "price": "R45,000/mo",
        "beds": 3,
        "baths": 2,
        "size": "185m²",
        "furnished": True,
        "pets": False,
        "lease": "12 months",
        "amenities": ["Sea views", "Pool", "Covered parking", "24hr security", "Balcony"],
        "url": "https://www.property24.com/to-rent/camps-bay/cape-town/western-cape/10023",
        "source": "Property24",
        "image_url": "https://images.unsplash.com/photo-1591280063444-d3c514eb6e13?w=600&q=75",
        "availability": "now",
        "features": {"sea views", "pool", "luxury", "camps bay", "furnished", "3 bed", "penthouse", "balcony", "parking", "security", "atlantic seaboard"},
    },
    {
        "title": "Modern 2-Bed Apartment in Sea Point",
        "location": "Sea Point",
        "price": "R22,000/mo",
        "beds": 2,
        "baths": 1,
        "size": "78m²",
        "furnished": True,
        "pets": True,
        "lease": "12 months",
        "amenities": ["Mountain views", "Gym", "Rooftop deck", "Fibre internet"],
        "url": "https://www.property24.com/to-rent/sea-point/cape-town/western-cape/10045",
        "source": "Property24",
        "image_url": "https://images.unsplash.com/photo-1580060839134-75a5edca2e99?w=600&q=75",
        "availability": "now",
        "features": {"mountain views", "gym", "sea point", "furnished", "pet friendly", "2 bed", "modern", "fibre", "rooftop", "atlantic seaboard"},
    },
    {
        "title": "Spacious 3-Bed Family Home with Garden",
        "location": "Constantia",
        "price": "R35,000/mo",
        "beds": 3,
        "baths": 2,
        "size": "220m²",
        "furnished": False,
        "pets": True,
        "lease": "24 months",
        "amenities": ["Garden", "Double garage", "Solar panels", "Borehole", "Study nook"],
        "url": "https://www.property24.com/to-rent/constantia/cape-town/western-cape/10067",
        "source": "Property24",
        "image_url": "https://images.unsplash.com/photo-1571939228382-b2f2b585ce15?w=600&q=75",
        "availability": "now",
        "features": {"garden", "family", "solar", "constantia", "pet friendly", "3 bed", "garage", "borehole", "spacious", "southern suburbs"},
    },
    {
        "title": "Stylish 1-Bed Studio in De Waterkant",
        "location": "De Waterkant",
        "price": "R14,500/mo",
        "beds": 1,
        "baths": 1,
        "size": "45m²",
        "furnished": True,
        "pets": False,
        "lease": "6 months",
        "amenities": ["Walkable to V&A", "Fibre internet", "Secure parking"],
        "url": "https://www.property24.com/to-rent/de-waterkant/cape-town/western-cape/10089",
        "source": "Property24",
        "image_url": "https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=600&q=75",
        "availability": "now",
        "features": {"de waterkant", "studio", "furnished", "1 bed", "walkable", "city bowl", "fibre", "compact", "trendy"},
    },
    {
        "title": "Oceanfront 2-Bed with Private Pool",
        "location": "Clifton",
        "price": "R55,000/mo",
        "beds": 2,
        "baths": 2,
        "size": "130m²",
        "furnished": True,
        "pets": False,
        "lease": "12 months",
        "amenities": ["Sea views", "Private pool", "Staff quarters", "Wine cellar", "Outdoor shower"],
        "url": "https://www.property24.com/to-rent/clifton/cape-town/western-cape/10102",
        "source": "Property24",
        "image_url": "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=600&q=75",
        "availability": "rare",
        "features": {"sea views", "pool", "luxury", "clifton", "furnished", "2 bed", "oceanfront", "wine cellar", "atlantic seaboard"},
    },
    {
        "title": "Renovated 2-Bed in Green Point Village",
        "location": "Green Point",
        "price": "R19,500/mo",
        "beds": 2,
        "baths": 1,
        "size": "82m²",
        "furnished": False,
        "pets": True,
        "lease": "12 months",
        "amenities": ["Near promenade", "Mountain views", "Open-plan kitchen", "Built-in braai"],
        "url": "https://www.property24.com/to-rent/green-point/cape-town/western-cape/10118",
        "source": "Property24",
        "image_url": "https://images.unsplash.com/photo-1577948000111-9c970dfe3743?w=600&q=75",
        "availability": "now",
        "features": {"mountain views", "green point", "pet friendly", "2 bed", "promenade", "braai", "renovated", "atlantic seaboard"},
    },
    {
        "title": "Executive 3-Bed Penthouse in Bantry Bay",
        "location": "Bantry Bay",
        "price": "R65,000/mo",
        "beds": 3,
        "baths": 3,
        "size": "250m²",
        "furnished": True,
        "pets": False,
        "lease": "12 months",
        "amenities": ["Sea views", "Pool", "Concierge", "Home automation", "Gym", "Sauna"],
        "url": "https://www.property24.com/to-rent/bantry-bay/cape-town/western-cape/10134",
        "source": "Property24",
        "image_url": "https://images.unsplash.com/photo-1613977257363-707ba9348227?w=600&q=75",
        "availability": "rare",
        "features": {"sea views", "pool", "luxury", "bantry bay", "furnished", "3 bed", "penthouse", "gym", "concierge", "sauna", "atlantic seaboard"},
    },
    {
        "title": "Bright 1-Bed Loft in Woodstock",
        "location": "Woodstock",
        "price": "R11,000/mo",
        "beds": 1,
        "baths": 1,
        "size": "55m²",
        "furnished": True,
        "pets": True,
        "lease": "Month-to-month",
        "amenities": ["High ceilings", "Exposed brick", "Fibre internet", "Shared courtyard"],
        "url": "https://www.property24.com/to-rent/woodstock/cape-town/western-cape/10156",
        "source": "Property24",
        "image_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=75",
        "availability": "now",
        "features": {"woodstock", "loft", "furnished", "pet friendly", "1 bed", "fibre", "affordable", "creative", "trendy"},
    },
    {
        "title": "Secure 3-Bed Townhouse in Hout Bay",
        "location": "Hout Bay",
        "price": "R28,000/mo",
        "beds": 3,
        "baths": 2,
        "size": "160m²",
        "furnished": False,
        "pets": True,
        "lease": "12 months",
        "amenities": ["Mountain views", "Garden", "Double garage", "Near beach", "Alarm system"],
        "url": "https://www.property24.com/to-rent/hout-bay/cape-town/western-cape/10178",
        "source": "Property24",
        "image_url": "https://images.unsplash.com/photo-1583847268964-b28dc8f51f92?w=600&q=75",
        "availability": "now",
        "features": {"mountain views", "garden", "hout bay", "pet friendly", "3 bed", "beach", "family", "garage", "secure"},
    },
    {
        "title": "Contemporary 2-Bed with Table Mountain Views",
        "location": "Oranjezicht",
        "price": "R25,000/mo",
        "beds": 2,
        "baths": 2,
        "size": "95m²",
        "furnished": True,
        "pets": False,
        "lease": "12 months",
        "amenities": ["Mountain views", "Pool", "Covered parking", "Balcony", "Built-in cupboards"],
        "url": "https://www.property24.com/to-rent/oranjezicht/cape-town/western-cape/10190",
        "source": "Property24",
        "image_url": "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=600&q=75",
        "availability": "now",
        "features": {"mountain views", "pool", "oranjezicht", "furnished", "2 bed", "balcony", "contemporary", "parking", "city bowl"},
    },
]

# Broad keyword → normalized feature tag mapping
KEYWORD_MAP = {
    # Views
    "sea view": "sea views", "ocean view": "sea views", "sea views": "sea views",
    "ocean": "sea views", "oceanfront": "sea views",
    "mountain view": "mountain views", "mountain views": "mountain views",
    "mountain": "mountain views", "table mountain": "mountain views",
    "views": "sea views",
    # Amenities
    "pool": "pool", "swimming": "pool",
    "garden": "garden", "yard": "garden",
    "pet": "pet friendly", "pets": "pet friendly", "dog": "pet friendly", "cat": "pet friendly",
    "furnished": "furnished",
    "solar": "solar", "panels": "solar",
    "gym": "gym", "fitness": "gym",
    "fibre": "fibre", "wifi": "fibre", "internet": "fibre",
    "parking": "parking", "garage": "garage",
    "braai": "braai", "bbq": "braai",
    "security": "security", "secure": "security",
    "balcony": "balcony", "terrace": "balcony",
    # Style
    "luxury": "luxury", "luxurious": "luxury", "upmarket": "luxury", "high-end": "luxury",
    "affordable": "affordable", "cheap": "affordable", "budget": "affordable",
    "family": "family", "kids": "family", "children": "family",
    "spacious": "spacious", "big": "spacious", "large": "spacious",
    "modern": "modern", "new": "modern",
    "contemporary": "modern",
    "loft": "loft", "studio": "studio", "penthouse": "penthouse",
    "walkable": "walkable", "walk": "walkable",
    "beach": "beach", "beachfront": "beach",
    "promenade": "promenade",
    "trendy": "trendy", "hip": "trendy",
    # Locations
    "camps bay": "camps bay", "campsbay": "camps bay",
    "sea point": "sea point", "seapoint": "sea point",
    "clifton": "clifton",
    "green point": "green point", "greenpoint": "green point",
    "bantry bay": "bantry bay",
    "de waterkant": "de waterkant", "waterkant": "de waterkant",
    "woodstock": "woodstock",
    "constantia": "constantia",
    "hout bay": "hout bay", "houtbay": "hout bay",
    "oranjezicht": "oranjezicht",
    "city bowl": "city bowl",
    "atlantic seaboard": "atlantic seaboard",
    "southern suburbs": "southern suburbs",
}


def _parse_price(price_str: str) -> int:
    nums = re.sub(r"[^\d]", "", price_str.split("/")[0])
    return int(nums) if nums else 0


def _extract_beds_wanted(query: str) -> int | None:
    m = re.search(r"(\d)\s*[-+]?\s*bed", query.lower())
    return int(m.group(1)) if m else None


def _extract_budget(query: str) -> int | None:
    # Match patterns like "under R25k", "under R25,000", "under 25000", "< R30k", "max R20,000"
    q = query.lower().replace(",", "").replace(" ", "")
    m = re.search(r"(?:under|below|max|<|lessthan)\s*r?(\d+)", q)
    if m:
        val = int(m.group(1))
        if val < 1000:
            val *= 1000  # "under r25" → R25,000
        return val
    # Also match "R10k-R20k" style ranges (use upper bound)
    m = re.search(r"r?(\d+)k?\s*[-–to]+\s*r?(\d+)k?", q)
    if m:
        val = int(m.group(2))
        if val < 1000:
            val *= 1000
        return val
    return None


def _extract_query_tags(query: str) -> set[str]:
    q = query.lower()
    tags = set()
    for keyword, tag in sorted(KEYWORD_MAP.items(), key=lambda x: -len(x[0])):
        if keyword in q:
            tags.add(tag)
    return tags


def _score_listing(
    listing: dict,
    query_tags: set[str],
    beds_wanted: int | None,
    budget: int | None,
) -> tuple[int, list[str], list[str]]:
    """Score a listing against query. Always returns meaningful matched/not_matched."""
    features = listing["features"]
    matched = []
    not_matched = []
    listing_price = _parse_price(listing["price"])

    if query_tags:
        for tag in query_tags:
            if tag in features:
                matched.append(tag.title())
            else:
                not_matched.append(tag.title())
    else:
        # No specific tags extracted — score based on general listing quality
        # Always show some of the listing's best amenities as matched
        matched = list(listing["amenities"][:3])

    # Bed matching
    if beds_wanted is not None:
        if listing["beds"] == beds_wanted:
            matched.append(f"{beds_wanted} bedrooms")
        elif listing["beds"] > beds_wanted:
            matched.append(f"{listing['beds']} bedrooms")
        else:
            not_matched.append(f"Only {listing['beds']} bed (wanted {beds_wanted})")

    # Budget matching
    if budget is not None:
        if listing_price <= budget:
            matched.append("Within budget")
        else:
            not_matched.append(f"Over budget ({listing['price']})")

    # Pets — always note it since it matters to renters
    if "pet friendly" not in query_tags:
        if listing["pets"]:
            matched.append("Pets allowed")
        else:
            not_matched.append("No pets")

    # Furnished status
    if "furnished" not in query_tags:
        if listing["furnished"]:
            matched.append("Furnished")

    # Ensure we always have at least some matched items from amenities
    if len(matched) < 2:
        for amenity in listing["amenities"]:
            if amenity not in matched and len(matched) < 3:
                matched.append(amenity)

    # Cap the lists for clean display
    matched = matched[:3]
    not_matched = not_matched[:2]

    # Calculate score
    total = len(matched) + len(not_matched)
    if total == 0:
        score = 65
    elif not query_tags and beds_wanted is None and budget is None:
        # Generic query — spread scores based on listing variety
        score = random.randint(58, 88)
    else:
        raw = (len(matched) / total) * 100
        score = max(20, min(97, int(raw + random.randint(-5, 5))))

    return score, matched, not_matched


def _match_reason(
    listing: dict, score: int, matched: list[str], not_matched: list[str],
) -> str:
    if score >= 85:
        prefix = "Excellent match"
    elif score >= 65:
        prefix = "Good fit"
    elif score >= 45:
        prefix = "Partial match"
    else:
        prefix = "Doesn't quite fit"

    if matched:
        highlights = " and ".join(m.lower() for m in matched[:2])
        reason = f"{prefix} — offers {highlights} in {listing['location']}."
    else:
        reason = f"{prefix} — a {listing['beds']}-bed in {listing['location']} at {listing['price']}."

    if not_matched and score < 80:
        reason += f" Missing: {not_matched[0].lower()}."

    return reason


def generate_demo_results(query: str) -> list[dict]:
    """Return demo listings scored and ranked against the user's query."""
    query_tags = _extract_query_tags(query)
    beds_wanted = _extract_beds_wanted(query)
    budget = _extract_budget(query)

    scored = []
    for listing in DEMO_LISTINGS:
        score, matched, not_matched = _score_listing(
            listing, query_tags, beds_wanted, budget,
        )
        reason = _match_reason(listing, score, matched, not_matched)

        scored.append({
            "title": listing["title"],
            "location": listing["location"],
            "price": listing["price"],
            "beds": listing["beds"],
            "baths": listing["baths"],
            "size": listing["size"],
            "furnished": listing["furnished"],
            "pets": listing["pets"],
            "lease": listing["lease"],
            "amenities": listing["amenities"],
            "url": listing["url"],
            "source": listing["source"],
            "image_url": listing["image_url"],
            "availability": listing["availability"],
            "match_score": score,
            "matched": matched,
            "not_matched": not_matched,
            "match_reason": reason,
        })

    scored.sort(key=lambda r: r["match_score"], reverse=True)
    return scored
