"""Embedding utilities for semantic rental search.

This is intentionally simple for the first version:
- Generate OpenAI embeddings for user queries and listing text.
- Compute cosine similarity in Python.
- Later, this can be replaced with pgvector for scalable DB search.
"""

from __future__ import annotations

import math
import os
from typing import Any

from openai import AsyncOpenAI


EMBEDDING_MODEL = "text-embedding-3-small"


def build_listing_embedding_text(listing: dict[str, Any]) -> str:
    """Create the text representation of a listing used for embeddings."""
    parts = [
        f"Title: {listing.get('title') or ''}",
        f"Location: {listing.get('location') or ''}",
        f"Suburb: {listing.get('suburb') or ''}",
        f"Property type: {listing.get('property_type') or ''}",
        f"Description: {listing.get('description') or ''}",
        f"Amenities: {', '.join(listing.get('amenities') or [])}",
    ]

    return "\n".join(parts).strip()


def build_query_embedding_text(user_preferences: dict[str, Any]) -> str:
    """Create enriched text for embedding the user's search intent."""
    hard_filters = user_preferences.get("hard_filters", {})
    soft_preferences = user_preferences.get("soft_preferences", {})

    areas = hard_filters.get("areas") or []
    soft_features = [
        feature.replace("_", " ")
        for feature, weight in soft_preferences.items()
        if weight and weight > 0
    ]

    parts = [
        f"Original query: {user_preferences.get('raw_query') or ''}",
        f"Improved query: {user_preferences.get('improved_prompt') or ''}",
        f"Preferred areas: {', '.join(areas)}",
        f"Desired lifestyle features: {', '.join(soft_features)}",
    ]

    return "\n".join(parts).strip()


async def embed_text(text: str, api_key: str | None = None) -> list[float] | None:
    """Return an embedding vector for text.

    Returns None if no API key is available or if text is empty.
    """
    api_key = api_key or os.getenv("OPENAI_API_KEY")

    if not api_key:
        return None

    if not text.strip():
        return None

    client = AsyncOpenAI(api_key=api_key)

    response = await client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text[:8000],
    )

    return response.data[0].embedding


def cosine_similarity(a: list[float] | None, b: list[float] | None) -> float:
    """Compute cosine similarity between two vectors."""
    if not a or not b:
        return 0.0

    if len(a) != len(b):
        return 0.0

    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


async def compute_semantic_scores(
    listings: list[dict[str, Any]],
    user_preferences: dict[str, Any],
    api_key: str | None = None,
) -> dict[str, float]:
    """Compute semantic similarity scores for candidate listings.

    For now this calculates embeddings at search time. This is okay for a prototype
    but not ideal long term. Later, listing embeddings should be generated once and
    stored in the database.
    """
    query_text = build_query_embedding_text(user_preferences)
    query_embedding = await embed_text(query_text, api_key=api_key)

    if not query_embedding:
        return {}

    scores: dict[str, float] = {}

    for listing in listings:
        listing_text = build_listing_embedding_text(listing)
        listing_embedding = await embed_text(listing_text, api_key=api_key)

        if not listing_embedding:
            continue

        listing_key = str(listing.get("id") or listing.get("source_url") or listing.get("title"))
        scores[listing_key] = round(cosine_similarity(query_embedding, listing_embedding), 4)

    return scores