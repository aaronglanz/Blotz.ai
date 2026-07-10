import asyncio
import logging
import re
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.database import get_db, async_session
from app.models import CachedListing, Search, SearchResult
from app.schemas import SearchHistoryItem, SearchRequest, SearchResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/search", tags=["search"])

def _build_ranking_hard_filters(
    hard_filters: dict | None,
    location: dict | None = None,
) -> dict:
    """Convert request hard filters into the shape expected by ranking.py.

    The database query is the source of truth for hard filtering.
    This is only kept for scoring/explanation consistency.
    """
    hard_filters = hard_filters or {}

    areas = []

    if hard_filters.get("suburb"):
        areas.append(hard_filters["suburb"])
    elif location and location.get("name"):
        areas.append(location["name"])

    return {
        "max_price": hard_filters.get("max_price"),
        "min_bedrooms": hard_filters.get("bedrooms"),
        "min_bathrooms": hard_filters.get("bathrooms"),
        "areas": areas,
    }
    
async def _fetch_candidate_listings(
    db: AsyncSession,
    hard_filters: dict | None = None,
    location: dict | None = None,
    limit: int = 120,
) -> list[dict]:
    """Fetch candidate listings using explicit hard filters.

    Hard filters are deterministic and should be applied in SQL:
    - suburb
    - bedrooms
    - bathrooms
    - price
    - property type
    - furnished
    - pets allowed

    Natural language should not decide these filters anymore.
    """
    hard_filters = hard_filters or {}

    query = select(CachedListing).where(CachedListing.is_active == True)

    suburb = hard_filters.get("suburb")
    if not suburb and location and location.get("name"):
        suburb = location["name"]

    if suburb:
        query = query.where(CachedListing.suburb.ilike(f"%{suburb}%"))

    bedrooms = hard_filters.get("bedrooms")
    if bedrooms is not None:
        # For selected hard filters, "2 bedrooms" should mean exactly 2.
        query = query.where(CachedListing.bedrooms == int(bedrooms))

    bathrooms = hard_filters.get("bathrooms")
    if bathrooms is not None:
        # Bathrooms are usually better treated as minimums.
        query = query.where(CachedListing.bathrooms >= int(bathrooms))

    min_price = hard_filters.get("min_price")
    if min_price is not None:
        query = query.where(CachedListing.price_amount >= int(min_price))

    max_price = hard_filters.get("max_price")
    if max_price is not None:
        query = query.where(CachedListing.price_amount <= int(max_price))

    property_type = hard_filters.get("property_type")
    if property_type:
        ptype = property_type.lower().strip()

        if ptype in {"apartment", "flat"}:
            query = query.where(
                or_(
                    CachedListing.property_type.ilike("%apartment%"),
                    CachedListing.property_type.ilike("%flat%"),
                    CachedListing.title.ilike("%apartment%"),
                    CachedListing.title.ilike("%flat%"),
                )
            )
        elif ptype in {"studio"}:
            query = query.where(
                or_(
                    CachedListing.property_type.ilike("%studio%"),
                    CachedListing.title.ilike("%studio%"),
                )
            )
        elif ptype in {"house"}:
            query = query.where(
                or_(
                    CachedListing.property_type.ilike("%house%"),
                    CachedListing.title.ilike("%house%"),
                )
            )
        else:
            query = query.where(
                or_(
                    CachedListing.property_type.ilike(f"%{property_type}%"),
                    CachedListing.title.ilike(f"%{property_type}%"),
                )
            )

    furnished = hard_filters.get("furnished")
    if furnished is not None:
        query = query.where(CachedListing.furnished == bool(furnished))

    pets_allowed = hard_filters.get("pets_allowed")
    if pets_allowed is not None:
        query = query.where(CachedListing.pets_allowed == bool(pets_allowed))

    query = query.order_by(
        CachedListing.description.isnot(None).desc(),
        CachedListing.first_seen_at.desc(),
    ).limit(limit)

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
    hard_filters: dict | None = None,
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
    hard_filters=hard_filters,
    location=location,
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
                # Hard filters come from the frontend controls, not the natural-language query.
                user_preferences["hard_filters"] = _build_ranking_hard_filters(
                    hard_filters=hard_filters,
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
    hard_filters = req.hard_filters.model_dump() if req.hard_filters else None

    search = Search(
        id=uuid.uuid4(),
        query_text=req.query_text,
        status="pending",
        interpreted_intent={
            "location": req.location.model_dump() if req.location else None,
            "hard_filters": hard_filters,
        },
    )

    db.add(search)
    await db.commit()

    search_id = search.id

    location = None
    if search.interpreted_intent and "location" in search.interpreted_intent:
        location = search.interpreted_intent["location"]

    # Fire and forget — the frontend polls GET /search/{id} for updates
    asyncio.create_task(
    _run_search_background(
        search_id=search_id,
        query_text=req.query_text,
        location=location,
        hard_filters=hard_filters,
    )
)

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