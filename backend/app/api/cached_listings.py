"""API endpoints for browsing cached/scraped property listings.

These endpoints serve data from the local DB — no Claude tokens needed.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
import sqlalchemy as sa
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import CachedListing
from app.schemas import CachedListingResponse, CachedListingFilters

router = APIRouter(prefix="/api/cached-listings", tags=["cached-listings"])


@router.get("", response_model=dict)
async def browse_listings(
    q: str | None = Query(None, description="Free-text search in title/location"),
    suburb: str | None = Query(None),
    min_price: int | None = Query(None, description="Minimum monthly rent in rands"),
    max_price: int | None = Query(None, description="Maximum monthly rent in rands"),
    bedrooms: int | None = Query(None),
    min_bedrooms: int | None = Query(None),
    bathrooms: int | None = Query(None),
    property_type: str | None = Query(None),
    furnished: bool | None = Query(None),
    pets_allowed: bool | None = Query(None),
    features: str | None = Query(None, description="Comma-separated feature tags e.g. sea_views,pool,parking"),
    sort_by: str = Query("newest", pattern="^(newest|price_asc|price_desc|bedrooms)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Browse cached listings with filters. No Claude tokens used."""
    query = select(CachedListing).where(CachedListing.is_active == True)

    if q:
        search_term = f"%{q}%"
        query = query.where(
            CachedListing.title.ilike(search_term)
            | CachedListing.location.ilike(search_term)
            | CachedListing.suburb.ilike(search_term)
        )
    if suburb:
        query = query.where(CachedListing.suburb.ilike(f"%{suburb}%"))
    if min_price is not None:
        query = query.where(CachedListing.price_amount >= min_price)
    if max_price is not None:
        query = query.where(CachedListing.price_amount <= max_price)
    if bedrooms is not None:
        query = query.where(CachedListing.bedrooms == bedrooms)
    if min_bedrooms is not None:
        query = query.where(CachedListing.bedrooms >= min_bedrooms)
    if bathrooms is not None:
        query = query.where(CachedListing.bathrooms >= bathrooms)
    if property_type:
        query = query.where(CachedListing.property_type.ilike(property_type))
    if furnished is not None:
        query = query.where(CachedListing.furnished == furnished)
    if pets_allowed is not None:
        query = query.where(CachedListing.pets_allowed == pets_allowed)
    if features:
        # Filter listings whose amenities JSON array contains ALL requested tags
        for tag in features.split(","):
            tag = tag.strip()
            if tag:
                query = query.where(CachedListing.amenities.cast(sa.String).ilike(f"%{tag}%"))

    # Count total matches
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Sort
    if sort_by == "price_asc":
        query = query.order_by(CachedListing.price_amount.asc().nullslast())
    elif sort_by == "price_desc":
        query = query.order_by(CachedListing.price_amount.desc().nullslast())
    elif sort_by == "bedrooms":
        query = query.order_by(CachedListing.bedrooms.desc().nullslast())
    else:  # newest
        query = query.order_by(CachedListing.first_seen_at.desc())

    # Paginate
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    result = await db.execute(query)
    listings = result.scalars().all()

    return {
        "listings": [CachedListingResponse.model_validate(l) for l in listings],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.get("/suburbs", response_model=list[dict])
async def list_suburbs(db: AsyncSession = Depends(get_db)):
    """List all suburbs with listing counts."""
    result = await db.execute(
        select(CachedListing.suburb, func.count(CachedListing.id))
        .where(CachedListing.is_active == True, CachedListing.suburb.isnot(None))
        .group_by(CachedListing.suburb)
        .order_by(func.count(CachedListing.id).desc())
    )
    return [{"name": row[0], "count": row[1]} for row in result.all()]


@router.get("/stats", response_model=dict)
async def listing_stats(db: AsyncSession = Depends(get_db)):
    """Get summary stats about cached listings."""
    active_count = (await db.execute(
        select(func.count()).where(CachedListing.is_active == True)
    )).scalar() or 0

    avg_price = (await db.execute(
        select(func.avg(CachedListing.price_amount))
        .where(CachedListing.is_active == True, CachedListing.price_amount.isnot(None))
    )).scalar()

    latest = (await db.execute(
        select(func.max(CachedListing.last_seen_at))
        .where(CachedListing.is_active == True)
    )).scalar()

    return {
        "total_active": active_count,
        "avg_price": int(avg_price) if avg_price else None,
        "last_updated": latest.isoformat() if latest else None,
    }


@router.get("/{listing_id}", response_model=CachedListingResponse)
async def get_listing(listing_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get a single cached listing by ID."""
    result = await db.execute(
        select(CachedListing).where(CachedListing.id == listing_id)
    )
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


@router.post("/scrape", response_model=dict)
async def trigger_scrape(max_pages: int = Query(50, ge=1, le=100)):
    """Manually trigger a Property24 scrape. Returns the Celery task ID."""
    from app.tasks.scrape import run_property24_scrape
    task = run_property24_scrape.delay(max_pages=max_pages)
    return {"task_id": task.id, "status": "started"}


@router.post("/enrich", response_model=dict)
async def trigger_enrich(batch_size: int = Query(50, ge=1, le=200)):
    """Enrich cached listings with descriptions and amenities from detail pages."""
    from app.tasks.scrape import enrich_listings
    task = enrich_listings.delay(batch_size=batch_size)
    return {"task_id": task.id, "status": "started"}
