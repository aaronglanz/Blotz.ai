"""Extract structured feature tags from property listing descriptions.

These tags enable fast DB-level filtering without needing Claude for every search.
Keywords are matched against the description text and structured amenities.
"""

import re

# Each feature: (tag_name, keywords_to_search_for)
FEATURE_PATTERNS: list[tuple[str, list[str]]] = [
    # Views & Feel
    ("sea_views", ["sea view", "ocean view", "sea-view", "ocean-view", "ocean facing", "sea facing"]),
    ("mountain_views", ["mountain view", "table mountain", "mountain-view", "mountain facing"]),
    ("natural_light", ["natural light", "sunlight", "sun-filled", "sun filled", "bright and airy", "light-filled", "light filled", "north facing", "north-facing"]),
    ("balcony", ["balcony", "patio", "terrace", "deck", "veranda", "verandah"]),
    ("garden", ["garden", "private garden", "landscaped garden", "courtyard"]),
    ("quiet", ["quiet street", "quiet area", "peaceful", "tranquil", "cul-de-sac", "cul de sac"]),
    ("walk_to_beach", ["walk to beach", "walking distance.*beach", "close to beach", "beachfront", "beach front", "promenade"]),
    ("walkable", ["walkable", "walk to shops", "close to restaurants", "walking distance"]),
    ("morning_sun", ["morning sun", "east.facing", "east facing", "north.facing", "north facing"]),
    ("trendy_area", ["trendy", "vibrant", "hip area", "buzzing", "trendy area", "up.and.coming"]),
    # Building
    ("pool", ["swimming pool", "pool", "heated pool", "rooftop pool"]),
    ("gym", ["gym", "fitness centre", "fitness center", "fitness room"]),
    ("security", ["24.*security", "24.*hour.*security", "cctv", "secure complex", "access control", "security guard", "gated"]),
    ("parking", ["parking", "garage", "covered parking", "secure parking", "basement parking", "parking bay"]),
    ("double_garage", ["double garage", "2.*garage", "two.*garage"]),
    ("lift", ["lift", "elevator"]),
    ("fibre", ["fibre", "fiber", "fibre ready", "fibre installed", "high.speed internet"]),
    ("backup_power", ["solar", "backup power", "generator", "inverter", "ups", "load.?shedding"]),
    ("boutique", ["boutique", "small complex", "exclusive complex", "intimate complex"]),
    ("concierge", ["concierge", "building manager", "on-site management"]),
    # Lifestyle
    ("modern", ["modern", "contemporary", "renovated", "newly renovated", "revamped", "designer", "high.end finish"]),
    ("open_plan", ["open plan", "open-plan", "open living"]),
    ("storage", ["built.in cupboard", "bic", "ample storage", "storage", "walk.in closet", "walk-in closet"]),
    ("pet_friendly", ["pet friendly", "pet-friendly", "pets allowed", "pets welcome"]),
    ("work_from_home", ["work from home", "study", "home office", "wfh", "work.from.home"]),
    ("lock_up_and_go", ["lock.up.and.go", "lock up and go", "low maintenance"]),
    ("entertaining", ["entertaining", "entertainment area", "braai", "bbq", "great for hosting"]),
    ("family", ["family", "family home", "child friendly", "children", "safe for kids"]),
    ("near_schools", ["school", "near.*school", "close to school"]),
    ("privacy", ["private", "privacy", "not overlooked", "secluded"]),
    # Comfort
    ("aircon", ["air.?con", "air conditioning", "a/c", "hvac", "climate control"]),
    ("underfloor_heating", ["underfloor heating", "under-floor heating", "heated floors"]),
    ("dishwasher", ["dishwasher"]),
    ("washing_machine", ["washing machine", "laundry"]),
    # Lease & billing
    ("short_lease", ["short.term", "short lease", "month.to.month", "month to month", "6.month", "flexible lease", "minimum.*3 month", "minimum.*6 month"]),
    ("bills_included", ["bills included", "water included", "levies included", "electricity included", "utilities included", "inclusive of"]),
    # Bedrooms & bathrooms
    ("en_suite", ["en.suite", "ensuite", "en suite"]),
    ("guest_bathroom", ["guest bath", "guest toilet", "guest w/?c", "powder room", "separate bathroom"]),
    ("studio", ["studio", "bachelor", "bachelor flat"]),
    # Furnishing
    ("furnished", ["fully furnished", "furnished"]),
    ("semi_furnished", ["semi.furnished", "partially furnished"]),
]


def extract_features(description: str | None, amenities: list[str] | None = None) -> list[str]:
    """Extract feature tags from a listing description and amenities list.

    Returns a list of tag strings like ["sea_views", "pool", "modern", "parking"].
    """
    if not description and not amenities:
        return []

    text = (description or "").lower()
    if amenities:
        text += " " + " ".join(a.lower() for a in amenities)

    found: list[str] = []
    for tag, patterns in FEATURE_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                found.append(tag)
                break

    return found
