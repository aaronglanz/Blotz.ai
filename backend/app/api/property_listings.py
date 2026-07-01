import json
import os
import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models import PropertyListing, User
from app.schemas import PropertyListingCreate, PropertyListingResponse
from app.services.claude import _parse_json
from app.services.auth import require_agent

LISTING_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "listings")
os.makedirs(LISTING_UPLOAD_DIR, exist_ok=True)
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024

router = APIRouter(prefix="/api/property-listings", tags=["property-listings"])


class BuyerSearchRequest(BaseModel):
    query: str
    filters: list[str] = []


class RankedListing(BaseModel):
    id: str
    title: str
    location: str
    price: str
    bedrooms: int
    bathrooms: int
    size: str | None = None
    furnished: str
    pets_allowed: bool
    amenities: list[str] = []
    description: str | None = None
    image_url: str | None = None
    contact_name: str
    contact_phone: str | None = None
    match_pct: int
    match_reason: str


class BuyerSearchResponse(BaseModel):
    results: list[RankedListing]


@router.post("", response_model=PropertyListingResponse)
async def create_property_listing(
    req: PropertyListingCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_agent),
):
    listing = PropertyListing(
        id=uuid.uuid4(),
        user_id=user.id,
        title=req.title,
        location=req.location,
        price=req.price,
        bedrooms=req.bedrooms,
        bathrooms=req.bathrooms,
        size=req.size,
        furnished=req.furnished,
        pets_allowed=req.pets_allowed,
        lease_type=req.lease_type,
        amenities=req.amenities,
        description=req.description,
        contact_name=req.contact_name,
        contact_email=req.contact_email,
        contact_phone=req.contact_phone,
        image_url=req.image_url,
        available_from=req.available_from,
    )
    db.add(listing)
    await db.commit()
    await db.refresh(listing)
    return listing


@router.get("", response_model=list[PropertyListingResponse])
async def get_property_listings(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PropertyListing)
        .where(PropertyListing.status == "active")
        .order_by(PropertyListing.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()


@router.get("/{listing_id}", response_model=PropertyListingResponse)
async def get_property_listing(listing_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PropertyListing).where(PropertyListing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(404, "Listing not found")
    return listing


@router.put("/{listing_id}", response_model=PropertyListingResponse)
async def update_property_listing(
    listing_id: uuid.UUID,
    req: PropertyListingCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_agent),
):
    result = await db.execute(select(PropertyListing).where(PropertyListing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(404, "Listing not found")
    if listing.user_id != user.id:
        raise HTTPException(403, "You can only edit your own listings")

    for field in [
        "title", "location", "price", "bedrooms", "bathrooms", "size",
        "furnished", "pets_allowed", "lease_type", "amenities", "description",
        "contact_name", "contact_email", "contact_phone", "image_url", "available_from",
    ]:
        setattr(listing, field, getattr(req, field))
    await db.commit()
    await db.refresh(listing)
    return listing


@router.delete("/{listing_id}")
async def delete_property_listing(
    listing_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_agent),
):
    result = await db.execute(select(PropertyListing).where(PropertyListing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(404, "Listing not found")
    if listing.user_id != user.id:
        raise HTTPException(403, "You can only delete your own listings")

    listing.status = "inactive"
    await db.commit()
    return {"detail": "Listing deactivated"}


@router.post("/{listing_id}/images")
async def upload_listing_image(
    listing_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_agent),
):
    result = await db.execute(select(PropertyListing).where(PropertyListing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(404, "Listing not found")
    if listing.user_id != user.id:
        raise HTTPException(403, "You can only upload images to your own listings")

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(400, f"Only {', '.join(ALLOWED_IMAGE_EXTENSIONS)} files are allowed")

    contents = await file.read()
    if len(contents) > MAX_IMAGE_SIZE:
        raise HTTPException(400, "Image too large. Maximum 10MB")

    file_id = str(uuid.uuid4())
    file_path = os.path.join(LISTING_UPLOAD_DIR, f"{file_id}{ext}")
    with open(file_path, "wb") as f:
        f.write(contents)

    image_url = f"/api/uploads/listings/{file_id}{ext}"

    # Set as primary image if none exists
    if not listing.image_url:
        listing.image_url = image_url
        await db.commit()

    return {"url": image_url}


@router.post("/search", response_model=BuyerSearchResponse)
async def search_property_listings(req: BuyerSearchRequest, db: AsyncSession = Depends(get_db)):
    settings = get_settings()

    # Fetch all active listings
    result = await db.execute(
        select(PropertyListing)
        .where(PropertyListing.status == "active")
        .order_by(PropertyListing.created_at.desc())
    )
    listings = result.scalars().all()

    if not listings:
        return BuyerSearchResponse(results=[])

    # Build summarised listing data for Claude (keep tokens low)
    summaries = []
    listing_map = {}
    for ls in listings:
        lid = str(ls.id)
        listing_map[lid] = ls
        summaries.append({
            "id": lid,
            "title": ls.title,
            "suburb": ls.location,
            "beds": ls.bedrooms,
            "baths": ls.bathrooms,
            "price": ls.price,
            "size": ls.size,
            "furnished": ls.furnished,
            "pets": ls.pets_allowed,
            "amenities": ls.amenities,
            "description": (ls.description or "")[:300],
        })

    filters_text = ""
    if req.filters:
        filters_text = f"\nACTIVE FILTERS: {', '.join(req.filters)}"

    prompt = (
        f"You are a Cape Town property matching expert.\n"
        f'BUYER SEARCH: "{req.query}"{filters_text}\n\n'
        f"AVAILABLE LISTINGS:\n{json.dumps(summaries, indent=2)}\n\n"
        f"Rank ALL listings by how well they match the buyer's search. "
        f"For each listing return: id, match_pct (0-100), match_reason (one friendly sentence explaining why it matches or doesn't). "
        f"Sort by match_pct descending.\n\n"
        f'JSON only: {{"ranked":[{{"id":"uuid","match_pct":92,"match_reason":"string"}}]}}'
    )

    api_url = "https://api.anthropic.com/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": settings.ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
    }
    body = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 4000,
        "messages": [{"role": "user", "content": prompt}],
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(api_url, json=body, headers=headers)
        resp.raise_for_status()

    text = "".join(
        b["text"] for b in resp.json().get("content", []) if b.get("type") == "text"
    )
    ranked_data = _parse_json(text)

    results = []
    for item in ranked_data.get("ranked", []):
        ls = listing_map.get(item["id"])
        if not ls:
            continue
        results.append(RankedListing(
            id=str(ls.id),
            title=ls.title,
            location=ls.location,
            price=ls.price,
            bedrooms=ls.bedrooms,
            bathrooms=ls.bathrooms,
            size=ls.size,
            furnished=ls.furnished,
            pets_allowed=ls.pets_allowed,
            amenities=ls.amenities,
            description=ls.description,
            image_url=ls.image_url,
            contact_name=ls.contact_name,
            contact_phone=ls.contact_phone,
            match_pct=item.get("match_pct", 0),
            match_reason=item.get("match_reason", ""),
        ))

    return BuyerSearchResponse(results=results)
