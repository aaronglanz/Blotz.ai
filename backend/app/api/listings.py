import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import SavedListing
from app.schemas import SavedListingResponse, SaveListingRequest

router = APIRouter(prefix="/api/listings", tags=["listings"])


def get_user_id(x_user_id: str = Header(...)) -> str:
    return x_user_id


@router.post("/save", response_model=SavedListingResponse)
async def save_listing(
    req: SaveListingRequest,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    if not req.listing_id and not req.url:
        raise HTTPException(status_code=400, detail="Either listing_id or url is required")

    filters = [SavedListing.user_id == user_id]
    matches = []
    if req.listing_id:
        matches.append(SavedListing.listing_id == req.listing_id)
    if req.url:
        matches.append(SavedListing.url == req.url)

    result = await db.execute(select(SavedListing).where(*filters, or_(*matches)))
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    listing = SavedListing(
        id=uuid.uuid4(),
        user_id=user_id,
        listing_id=req.listing_id,
        url=req.url,
        title=req.title,
        location=req.location,
        price=req.price,
        source=req.source,
        image_url=req.image_url,
    )
    db.add(listing)
    await db.commit()
    await db.refresh(listing)
    return listing


@router.delete("/saved/{listing_id}")
async def unsave_listing(
    listing_id: uuid.UUID,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SavedListing).where(
            SavedListing.id == listing_id,
            SavedListing.user_id == user_id,
        )
    )
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    await db.delete(listing)
    await db.commit()
    return {"ok": True}


@router.get("/saved", response_model=list[SavedListingResponse])
async def get_saved_listings(
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SavedListing)
        .where(SavedListing.user_id == user_id)
        .order_by(SavedListing.saved_at.desc())
    )
    return result.scalars().all()
