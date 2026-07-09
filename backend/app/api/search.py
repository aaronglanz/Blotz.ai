import asyncio
import logging
import re
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.database import get_db, async_session
from app.models import CachedListing, Search, SearchResult
from app.schemas import SearchHistoryItem, SearchRequest, SearchResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/search", tags=["search"])


async def _fetch_candidate_listings(
    db: AsyncSession,
    intent: dict,
    location: dict | None = None,
    query_text: str | None = None,
    limit: int = 80,
) -> list[dict]:
    """Pre-filter cached listings based on structured criteria from the intent.

    Returns up to `limit` listings as dicts for ranking.
    """
    query = select(CachedListing).where(CachedListing.is_active == True)

    # Apply structured filters if the intent extracted them
    tags = intent.get("interpreted_tags", [])
    tag_labels = [t.get("label", "").lower() for t in tags]

    KNOWN_CAPE_TOWN_SUBURBS = [
        "Sea Point",
        "Green Point",
        "Mouille Point",
        "Camps Bay",
        "Clifton",
        "Bantry Bay",
        "Fresnaye",
        "Gardens",
        "Tamboerskloof",
        "Vredehoek",
        "Oranjezicht",
        "Observatory",
        "Woodstock",
        "Claremont",
        "Rondebosch",
        "Newlands",
        "Waterfront",
        "De Waterkant",
        "City Bowl",
    ]

    query_for_location = " ".join(
        [
            query_text or "",
            intent.get("improved_prompt", "") or "",
            " ".join(tag_labels),
        ]
    ).lower()

    detected_suburb = None
    for suburb in KNOWN_CAPE_TOWN_SUBURBS:
        if suburb.lower() in query_for_location:
            detected_suburb = suburb
            break

    # Location filter — prioritize the explicit location from the frontend,
    # then deterministic suburb extraction from the text,
    # then fall back to any location tag from intent interpretation.
    location_applied = False

    if location and location.get("name"):
        query = query.where(CachedListing.suburb.ilike(f"%{location['name']}%"))
        location_applied = True

    if not location_applied and detected_suburb:
        query = query.where(CachedListing.suburb.ilike(f"%{detected_suburb}%"))
        location_applied = True

    if not location_applied:
        for tag in tags:
            if tag.get("category") == "location":
                suburb = tag.get("label", "")
                if suburb:
                    query = query.where(CachedListing.suburb.ilike(f"%{suburb}%"))
                    location_applied = True
                    break

    # Budget filter — extract price range from budget tags
    for tag in tags:
        if tag.get("category") == "budget":
            label = tag.get("label", "")

            amounts = [
                int(m.replace(" ", "").replace(",", ""))
                for m in re.findall(r"(\d[\d\s,]+)", label)
            ]

            if amounts:
                max_budget = max(amounts)

                # Allow 20% over stated max for flexibility
                query = query.where(CachedListing.price_amount <= int(max_budget * 1.2))

                if len(amounts) >= 2:
                    min_budget = min(amounts)
                    query = query.where(CachedListing.price_amount >= int(min_budget * 0.8))

                break

    # Bedroom filter
    for label in tag_labels:
        bed_match = re.search(r"(\d+)\s*bed", label)
        if bed_match:
            query = query.where(CachedListing.bedrooms >= int(bed_match.group(1)))
            break

    # Prefer listings with descriptions because they score better
    query = query.order_by(
        CachedListing.description.isnot(None).desc(),
        CachedListing.first_seen_at.desc(),
    )

    query = query.limit(limit)

    result = await db.execute(query)
    listings = result.scalars().all()

    return [
        {
            "id": str(l.id),
            "title": l.title,
            "location": l.location,
            "suburb": l.suburb,
            "price_display": l.price_display,
            "price_amount": l.price_amount,
            "bedrooms": l.bedrooms,
            "bathrooms": l.bathrooms,
            "size_sqm": l.size_sqm,
            "property_type": l.property_type,
            "furnished": l.furnished,
            "pets_allowed": l.pets_allowed,
            "description": l.description,
            "amenities": l.amenities,
            "source": l.source,
            "source_url": l.source_url,
            "image_url": l.image_url,
            "available_from": l.available_from,
        }
        for l in listings
    ]


async def _run_search_background(
    search_id: uuid.UUID,
    query_text: str,
    location: dict | None,
):
    """Run the search in the background using its own DB session.

    Flow:
    1. Use Claude/Haiku to interpret intent, or use fallback if no API key.
    2. Pre-filter cached listings from our DB.
    3. Build structured user preferences.
    4. Compute optional semantic embedding scores.
    5. Use transparent Python ranking to score listings.
    6. Fallback: return DB results directly if ranking fails.
    """
    settings = get_settings()

    async with async_session() as db:
        search = (
            await db.execute(select(Search).where(Search.id == search_id))
        ).scalar_one()

        try:
            search.status = "interpreting"
            await db.commit()

            # Stage 1: Interpret intent with Claude/Haiku if available
            intent = {
                "improved_prompt": query_text,
                "rank_guidance": "Match closely.",
                "interpreted_tags": [],
                "missing": [],
            }

            if settings.ANTHROPIC_API_KEY:
                from app.services.claude import ClaudeService

                claude = ClaudeService(settings.ANTHROPIC_API_KEY)

                try:
                    intent = await claude.interpret_intent(query_text, location)
                except Exception:
                    logger.warning(
                        "Intent interpretation failed, using fallback",
                        exc_info=True,
                    )

            search.interpreted_intent = {
                **(search.interpreted_intent or {}),
                "intent": intent,
            }
            await db.commit()

            # Stage 2: Fetch candidate listings from cached DB
            search.status = "searching"
            await db.commit()

            candidates = await _fetch_candidate_listings(
    db=db,
    intent=intent,
    location=location,
    query_text=query_text,
)

            logger.info(
                f"Search {search_id}: {len(candidates)} candidates from cache "
                f"(location={location})"
            )

            # Stage 3: Rank candidates with transparent Python scoring
            results = []

            if candidates:
                from app.services.ranking import build_user_preferences, rank_listings

                user_preferences = build_user_preferences(
                    query_text=query_text,
                    intent=intent,
                    location=location,
                )

                search.interpreted_intent = {
                    **(search.interpreted_intent or {}),
                    "intent": intent,
                    "user_preferences": user_preferences,
                }
                await db.commit()

                try:
                    semantic_scores = {}

                    if settings.OPENAI_API_KEY:
                        try:
                            from app.services.embeddings import compute_semantic_scores

                            semantic_scores = await compute_semantic_scores(
                                listings=candidates[:30],
                                user_preferences=user_preferences,
                                api_key=settings.OPENAI_API_KEY,
                            )

                            logger.info(
                                f"Search {search_id}: Computed semantic scores "
                                f"for {len(semantic_scores)} listings"
                            )

                        except Exception:
                            logger.exception(
                                f"Search {search_id}: Semantic scoring failed, "
                                "continuing without embeddings"
                            )

                    results = rank_listings(
                        listings=candidates,
                        user_preferences=user_preferences,
                        max_results=10,
                        semantic_scores=semantic_scores,
                    )

                    logger.info(
                        f"Search {search_id}: Python ranking returned "
                        f"{len(results)} results"
                    )

                except Exception:
                    logger.exception(
                        f"Search {search_id}: Python ranking failed, "
                        "returning candidates directly"
                    )

            # Fallback: if ranking returned nothing, return top candidates from DB
            if not results and candidates:
                logger.info(f"Search {search_id}: Using direct DB results as fallback")

                results = [
                    {
                        "title": c["title"],
                        "location": c["location"],
                        "price": c["price_display"],
                        "beds": c.get("bedrooms"),
                        "baths": c.get("bathrooms"),
                        "size": f"{c['size_sqm']} m²" if c.get("size_sqm") else None,
                        "furnished": c.get("furnished"),
                        "pets": c.get("pets_allowed"),
                        "lease": None,
                        "amenities": c.get("amenities", []),
                        "match_score": 50,
                        "matched": [],
                        "not_matched": [],
                        "match_reason": "Matched by location and basic filters",
                        "url": c["source_url"],
                        "source": c["source"],
                        "image_url": c.get("image_url"),
                        "availability": c.get("available_from", "now"),
                    }
                    for c in candidates[:10]
                ]

            results.sort(key=lambda r: r.get("match_score", 0), reverse=True)

            for i, r in enumerate(results):
                db.add(
                    SearchResult(
                        id=uuid.uuid4(),
                        search_id=search.id,
                        title=r.get("title", "Rental"),
                        location=r.get("location"),
                        price=r.get("price"),
                        beds=r.get("beds"),
                        baths=r.get("baths"),
                        size=r.get("size"),
                        furnished=r.get("furnished"),
                        pets=r.get("pets"),
                        lease=r.get("lease"),
                        amenities=r.get("amenities", []),
                        match_score=r.get("match_score"),
                        matched=r.get("matched", []),
                        not_matched=r.get("not_matched", []),
                        match_reason=r.get("match_reason"),
                        url=r.get("url"),
                        source=r.get("source"),
                        image_url=r.get("image_url"),
                        availability=r.get("availability"),
                        rank=i + 1,
                    )
                )

            search.status = "complete"
            await db.commit()

            logger.info(f"Search {search_id} complete with {len(results)} results")

        except Exception as e:
            logger.exception(f"Search {search_id} failed")
            search.status = "failed"
            search.error_message = str(e)
            await db.commit()


@router.post("", response_model=dict)
async def create_search(req: SearchRequest, db: AsyncSession = Depends(get_db)):
    search = Search(
        id=uuid.uuid4(),
        query_text=req.query_text,
        status="pending",
        interpreted_intent={
            "location": req.location.model_dump() if req.location else None
        },
    )

    db.add(search)
    await db.commit()

    search_id = search.id

    location = None
    if search.interpreted_intent and "location" in search.interpreted_intent:
        location = search.interpreted_intent["location"]

    # Fire and forget — the frontend polls GET /search/{id} for updates
    asyncio.create_task(_run_search_background(search_id, req.query_text, location))

    return {"id": str(search_id), "status": "pending"}


@router.get("/history", response_model=list[SearchHistoryItem])
async def get_search_history(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Search).order_by(Search.created_at.desc()).limit(10)
    )

    return result.scalars().all()


@router.get("/{search_id}", response_model=SearchResponse)
async def get_search(search_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Search)
        .options(selectinload(Search.results))
        .where(Search.id == search_id)
    )

    search = result.scalar_one_or_none()

    if not search:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Search not found")

    return search