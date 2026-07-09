"""Transparent rental listing ranking.

This module moves the core matching logic away from "Claude scores every listing"
and toward deterministic, inspectable ranking.

Flow:
1. Build user preferences from the query + Claude intent.
2. Extract listing features from description/amenities.
3. Score hard filters, soft features, price fit, and location fit.
4. Return ranked listing results in the same shape expected by SearchResult.
"""

from __future__ import annotations

import re
from typing import Any

from app.services.feature_extractor import extract_features


# Maps user-friendly phrases to the internal tags produced by feature_extractor.py
SOFT_FEATURE_ALIASES: dict[str, list[str]] = {
    "natural_light": [
        "natural light",
        "bright",
        "sunny",
        "sunlight",
        "light filled",
        "light-filled",
        "north facing",
        "north-facing",
    ],
    "modern": [
        "modern",
        "renovated",
        "newly renovated",
        "contemporary",
        "designer",
        "new finishes",
        "modern finishes",
    ],
    "balcony": ["balcony", "patio", "terrace", "deck"],
    "sea_views": ["sea view", "sea views", "ocean view", "ocean views", "view of the sea"],
    "mountain_views": ["mountain view", "mountain views", "table mountain"],
    "quiet": ["quiet", "peaceful", "tranquil", "not noisy", "noise", "quiet street"],
    "parking": ["parking", "garage", "secure parking", "parking bay"],
    "security": ["security", "secure", "safe", "gated", "24 hour security", "cctv"],
    "pet_friendly": ["pet friendly", "pets allowed", "dog", "cat", "pets"],
    "work_from_home": ["work from home", "wfh", "home office", "study", "desk"],
    "walkable": ["walkable", "walking distance", "close to shops", "close to restaurants", "cafes"],
    "walk_to_beach": ["beach", "promenade", "walk to beach", "close to beach"],
    "pool": ["pool", "swimming pool"],
    "gym": ["gym", "fitness"],
    "backup_power": ["backup power", "inverter", "generator", "solar", "loadshedding", "load shedding"],
    "fibre": ["fibre", "fiber", "wifi", "internet"],
    "open_plan": ["open plan", "open-plan", "open living"],
    "furnished": ["furnished", "fully furnished"],
    "garden": ["garden", "courtyard"],
    "aircon": ["aircon", "air conditioning", "a/c"],
}


def _normalise_text(value: str | None) -> str:
    return (value or "").lower().strip()


def _humanise_feature(feature: str) -> str:
    return feature.replace("_", " ")


def _parse_money_amounts(text: str) -> list[int]:
    """Extract rough Rand amounts from text.

    Handles:
    - R20000
    - R 20,000
    - 20000
    - 20k
    """
    text = text.lower()
    amounts: list[int] = []

    # 20k / R20k
    for match in re.findall(r"(?:r\s*)?(\d{1,3})\s*k\b", text):
        amounts.append(int(match) * 1000)

    # R 20,000 / R20000 / 20000
    for match in re.findall(r"(?:r\s*)?(\d[\d\s,]{3,})", text):
        cleaned = match.replace(" ", "").replace(",", "")
        try:
            value = int(cleaned)
            if value >= 1000:
                amounts.append(value)
        except ValueError:
            continue

    return amounts


def _parse_min_rooms(text: str, room_word: str) -> int | None:
    """Parse phrases like '2 bed', '2 bedroom', '3 bathrooms'."""
    pattern = rf"(\d+)\s*{room_word}"
    match = re.search(pattern, text)
    if match:
        return int(match.group(1))
    return None


def build_user_preferences(
    query_text: str,
    intent: dict[str, Any] | None = None,
    location: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build structured preferences from the raw user query and Claude intent.

    This intentionally works even if Claude fails, so ranking still runs.
    """
    intent = intent or {}
    query_lower = _normalise_text(query_text)
    improved_prompt = _normalise_text(intent.get("improved_prompt"))

    combined_text = f"{query_lower} {improved_prompt}"

    interpreted_tags = intent.get("interpreted_tags") or []

    # Include Claude tag labels in the text used for soft preference detection
    tag_text = " ".join(_normalise_text(t.get("label")) for t in interpreted_tags)
    combined_text = f"{combined_text} {tag_text}"

    hard_filters: dict[str, Any] = {
        "max_price": None,
        "min_bedrooms": None,
        "min_bathrooms": None,
        "areas": [],
    }

    # Location from frontend is strongest signal
    if location and location.get("name"):
        hard_filters["areas"].append(location["name"])

    # Location tags from Claude intent
    for tag in interpreted_tags:
        if tag.get("category") == "location" and tag.get("label"):
            hard_filters["areas"].append(tag["label"])

    # Budget from text or budget tags
    amounts = _parse_money_amounts(combined_text)
    if amounts:
        hard_filters["max_price"] = max(amounts)

    min_beds = _parse_min_rooms(combined_text, "bed")
    if min_beds is not None:
        hard_filters["min_bedrooms"] = min_beds

    min_baths = _parse_min_rooms(combined_text, "bath")
    if min_baths is not None:
        hard_filters["min_bathrooms"] = min_baths

    # Soft preferences with rough importance weights
    soft_preferences: dict[str, float] = {}

    for feature, phrases in SOFT_FEATURE_ALIASES.items():
        if any(phrase in combined_text for phrase in phrases):
            soft_preferences[feature] = 0.8

    # Increase weight for features that appear in "must have" tags
    for tag in interpreted_tags:
        category = tag.get("category")
        label = _normalise_text(tag.get("label"))

        if category in {"must", "lifestyle", "vibe"}:
            for feature, phrases in SOFT_FEATURE_ALIASES.items():
                if feature in label or any(phrase in label for phrase in phrases):
                    soft_preferences[feature] = 0.9 if category == "must" else 0.75

    # Deduplicate areas while preserving order
    seen = set()
    deduped_areas = []
    for area in hard_filters["areas"]:
        area_norm = _normalise_text(area)
        if area_norm and area_norm not in seen:
            seen.add(area_norm)
            deduped_areas.append(area)

    hard_filters["areas"] = deduped_areas

    return {
        "hard_filters": hard_filters,
        "soft_preferences": soft_preferences,
        "raw_query": query_text,
        "improved_prompt": intent.get("improved_prompt", query_text),
    }


def score_hard_filters(listing: dict[str, Any], hard_filters: dict[str, Any]) -> dict[str, Any]:
    """Score strict filters.

    If price or bedroom minimum is clearly violated, hard_score becomes 0.
    """
    status: dict[str, str] = {}

    score = 1.0

    max_price = hard_filters.get("max_price")
    listing_price = listing.get("price_amount")

    if max_price:
        if listing_price is None:
            status["price"] = "unknown"
            score -= 0.15
        elif listing_price <= max_price:
            status["price"] = "pass"
        elif listing_price <= max_price * 1.1:
            status["price"] = "slightly_over"
            score -= 0.25
        else:
            status["price"] = "fail"
            return {"score": 0.0, "status": status}

    min_bedrooms = hard_filters.get("min_bedrooms")
    bedrooms = listing.get("bedrooms")

    if min_bedrooms:
        if bedrooms is None:
            status["bedrooms"] = "unknown"
            score -= 0.15
        elif bedrooms >= min_bedrooms:
            status["bedrooms"] = "pass"
        else:
            status["bedrooms"] = "fail"
            return {"score": 0.0, "status": status}

    min_bathrooms = hard_filters.get("min_bathrooms")
    bathrooms = listing.get("bathrooms")

    if min_bathrooms:
        if bathrooms is None:
            status["bathrooms"] = "unknown"
            score -= 0.10
        elif bathrooms >= min_bathrooms:
            status["bathrooms"] = "pass"
        else:
            status["bathrooms"] = "fail"
            score -= 0.25

    areas = hard_filters.get("areas") or []
    if areas:
        listing_area_text = " ".join(
            [
                _normalise_text(listing.get("suburb")),
                _normalise_text(listing.get("location")),
                _normalise_text(listing.get("title")),
            ]
        )

        area_match = any(_normalise_text(area) in listing_area_text for area in areas)

        if area_match:
            status["area"] = "pass"
        else:
            status["area"] = "weak_match"
            score -= 0.30

    return {"score": max(score, 0.0), "status": status}


def score_soft_features(
    listing_features: list[str],
    soft_preferences: dict[str, float],
    has_description: bool = True,
) -> dict[str, Any]:
    """Score soft lifestyle preferences against extracted listing features."""
    if not soft_preferences:
        return {
            "score": 0.60,
            "matched_features": [],
            "missing_features": [],
            "uncertain_features": [],
        }

    feature_set = set(listing_features)

    total_weight = 0.0
    matched_weight = 0.0

    matched: list[str] = []
    missing: list[str] = []
    uncertain: list[str] = []

    for feature, weight in soft_preferences.items():
        total_weight += weight

        if feature in feature_set:
            matched_weight += weight
            matched.append(feature)
        else:
            if has_description:
                missing.append(feature)
            else:
                uncertain.append(feature)

    score = matched_weight / total_weight if total_weight else 0.60

    # If description is missing, avoid overly punishing the listing
    if uncertain and not missing:
        score = max(score, 0.45)

    return {
        "score": round(score, 4),
        "matched_features": matched,
        "missing_features": missing,
        "uncertain_features": uncertain,
    }


def score_price_fit(listing: dict[str, Any], hard_filters: dict[str, Any]) -> float:
    """Reward listings comfortably within budget."""
    max_price = hard_filters.get("max_price")
    listing_price = listing.get("price_amount")

    if not max_price:
        return 0.70

    if listing_price is None:
        return 0.50

    ratio = listing_price / max_price

    if ratio <= 0.85:
        return 1.00
    if ratio <= 1.00:
        return 0.85
    if ratio <= 1.10:
        return 0.55
    return 0.10


def score_location_fit(listing: dict[str, Any], hard_filters: dict[str, Any]) -> float:
    areas = hard_filters.get("areas") or []

    if not areas:
        return 0.70

    listing_area_text = " ".join(
        [
            _normalise_text(listing.get("suburb")),
            _normalise_text(listing.get("location")),
            _normalise_text(listing.get("title")),
        ]
    )

    if any(_normalise_text(area) in listing_area_text for area in areas):
        return 1.00

    return 0.35


def rank_listing(
    listing: dict[str, Any],
    user_preferences: dict[str, Any],
    semantic_score: float | None = None,
) -> dict[str, Any]:
    """Rank one listing and return a SearchResult-compatible dict."""
    hard_filters = user_preferences.get("hard_filters", {})
    soft_preferences = user_preferences.get("soft_preferences", {})

    description = listing.get("description")
    amenities = listing.get("amenities") or []

    listing_features = extract_features(description, amenities)

    hard = score_hard_filters(listing, hard_filters)

    if hard["score"] == 0:
        final_score = 0
    else:
        soft = score_soft_features(
            listing_features=listing_features,
            soft_preferences=soft_preferences,
            has_description=bool(description),
        )
        price_score = score_price_fit(listing, hard_filters)
        location_score = score_location_fit(listing, hard_filters)

        semantic_score = semantic_score if semantic_score is not None else 0.50

        final_score_float = (
            0.35 * soft["score"]
            + 0.25 * hard["score"]
            + 0.20 * price_score
            + 0.10 * location_score
            + 0.10 * semantic_score
        )

        final_score = int(round(final_score_float * 100))

    soft = score_soft_features(
        listing_features=listing_features,
        soft_preferences=soft_preferences,
        has_description=bool(description),
    )

    price_score = score_price_fit(listing, hard_filters)
    location_score = score_location_fit(listing, hard_filters)

    matched_features = [_humanise_feature(f) for f in soft["matched_features"]]
    missing_features = [_humanise_feature(f) for f in soft["missing_features"]]
    uncertain_features = [_humanise_feature(f) for f in soft["uncertain_features"]]

    matched = matched_features[:4]
    not_matched = missing_features[:3]

    if uncertain_features:
        not_matched += [f"uncertain: {f}" for f in uncertain_features[:2]]

    if matched:
        reason = f"Strongest matches: {', '.join(matched[:3])}."
        if not_matched:
            reason += f" Weak or missing signals: {', '.join(not_matched[:2])}."
    else:
        reason = "Matched mainly on hard filters such as price, bedrooms, or location."
        if not_matched:
            reason += f" Missing soft-preference signals: {', '.join(not_matched[:2])}."

    score_breakdown = {
        "hard_filter_score": round(hard["score"], 4),
        "soft_feature_score": round(soft["score"], 4),
        "price_score": round(price_score, 4),
        "location_score": round(location_score, 4),
        "hard_filter_status": hard["status"],
        "listing_features": listing_features,
        "semantic_score": round(semantic_score, 4),
    }

    return {
        "title": listing.get("title", "Rental"),
        "location": listing.get("location"),
        "price": listing.get("price_display"),
        "beds": listing.get("bedrooms"),
        "baths": listing.get("bathrooms"),
        "size": f"{listing['size_sqm']} m²" if listing.get("size_sqm") else None,
        "furnished": listing.get("furnished"),
        "pets": listing.get("pets_allowed"),
        "lease": None,
        "amenities": listing.get("amenities", []),
        "match_score": final_score,
        "matched": matched,
        "not_matched": not_matched,
        "match_reason": reason,
        "url": listing.get("source_url"),
        "source": listing.get("source"),
        "image_url": listing.get("image_url"),
        "availability": listing.get("available_from", "now"),
        "score_breakdown": score_breakdown,
    }


def rank_listings(
    listings: list[dict[str, Any]],
    user_preferences: dict[str, Any],
    max_results: int = 10,
    semantic_scores: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    """Rank multiple listings and return the best results."""
    ranked = []

    for listing in listings:
        listing_key = str(listing.get("id") or listing.get("source_url") or listing.get("title"))
        semantic_score = (semantic_scores or {}).get(listing_key)

        result = rank_listing(
            listing=listing,
            user_preferences=user_preferences,
            semantic_score=semantic_score,
        )

        # Exclude clear hard-filter failures
        if result["match_score"] <= 0:
            continue

        ranked.append(result)

    ranked.sort(key=lambda r: r.get("match_score", 0), reverse=True)

    return ranked[:max_results]