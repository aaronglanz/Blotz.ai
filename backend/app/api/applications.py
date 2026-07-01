import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Application, PropertyListing, RenterProfile, RenterDocument, User
from app.schemas import (
    ApplicationCreate,
    EligibilityResponse,
    ApplicationResponse,
    ApplicationWithListing,
    ApplicationForAgent,
    ApplicationStatusUpdate,
)
from app.services.renter_readiness import (
    REQUIRED_DOC_TYPES,
    get_profile_and_doc_gaps,
)
from app.services.auth import get_user_id_flexible as get_user_id, require_agent

router = APIRouter(prefix="/api/applications", tags=["applications"])


def mask_id_number(id_number: str | None) -> str | None:
    if not id_number or len(id_number) < 6:
        return id_number
    return id_number[:6] + "*" * (len(id_number) - 6)


@router.get("/check-eligible", response_model=EligibilityResponse)
async def check_eligible(user_id: str = Depends(get_user_id), db: AsyncSession = Depends(get_db)):
    missing_profile_fields, missing_documents = await get_profile_and_doc_gaps(user_id, db)
    return EligibilityResponse(
        eligible=not missing_profile_fields and not missing_documents,
        missing_profile_fields=missing_profile_fields,
        missing_documents=missing_documents,
    )


@router.post("", response_model=ApplicationResponse)
async def create_application(req: ApplicationCreate, user_id: str = Depends(get_user_id), db: AsyncSession = Depends(get_db)):
    # Check profile completeness
    missing_profile_fields, missing_documents = await get_profile_and_doc_gaps(user_id, db)
    if missing_profile_fields or missing_documents:
        missing_parts = []
        if missing_profile_fields:
            missing_parts.append(f"profile fields: {', '.join(missing_profile_fields)}")
        if missing_documents:
            missing_parts.append(f"documents: {', '.join(missing_documents)}")
        raise HTTPException(
            400,
            f"Profile incomplete. Missing {'; '.join(missing_parts)}.",
        )

    # Check listing exists
    listing_result = await db.execute(
        select(PropertyListing).where(PropertyListing.id == req.listing_id)
    )
    listing = listing_result.scalar_one_or_none()
    if not listing:
        raise HTTPException(404, "Listing not found")

    # Check not already applied
    existing = await db.execute(
        select(Application)
        .where(Application.user_id == user_id, Application.listing_id == req.listing_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "You have already applied to this listing")

    app = Application(
        id=uuid.uuid4(),
        user_id=user_id,
        listing_id=uuid.UUID(req.listing_id),
        agent_user_id=listing.user_id,
    )
    db.add(app)
    await db.commit()
    await db.refresh(app)
    return app


@router.get("/mine", response_model=list[ApplicationWithListing])
async def my_applications(user_id: str = Depends(get_user_id), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.listing))
        .where(Application.user_id == user_id)
        .order_by(Application.applied_at.desc())
    )
    apps = result.scalars().all()

    return [
        ApplicationWithListing(
            id=app.id,
            user_id=app.user_id,
            listing_id=app.listing_id,
            agent_user_id=app.agent_user_id,
            status=app.status,
            applied_at=app.applied_at,
            updated_at=app.updated_at,
            listing_title=app.listing.title if app.listing else None,
            listing_location=app.listing.location if app.listing else None,
            listing_price=app.listing.price if app.listing else None,
            listing_image_url=app.listing.image_url if app.listing else None,
            agent_name=app.listing.contact_name if app.listing else None,
        )
        for app in apps
    ]


@router.put("/{app_id}/withdraw", response_model=ApplicationResponse)
async def withdraw_application(app_id: str, user_id: str = Depends(get_user_id), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Application)
        .where(Application.id == app_id, Application.user_id == user_id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(404, "Application not found")
    if app.status != "Applied":
        raise HTTPException(400, "Can only withdraw applications with 'Applied' status")

    app.status = "Withdrawn"
    await db.commit()
    await db.refresh(app)
    return app


# ── Agent endpoints ──

@router.get("/agent", response_model=list[ApplicationForAgent])
async def agent_applications(user: User = Depends(require_agent), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.listing))
        .where(Application.agent_user_id == user.id)
        .order_by(Application.applied_at.desc())
    )
    apps = result.scalars().all()

    if not apps:
        return []

    # Batch-load profiles and docs for all renter user_ids
    renter_ids = list({app.user_id for app in apps})

    profiles_result = await db.execute(
        select(RenterProfile).where(RenterProfile.user_id.in_(renter_ids))
    )
    profiles_map = {p.user_id: p for p in profiles_result.scalars().all()}

    docs_result = await db.execute(
        select(RenterDocument.user_id, RenterDocument.document_type)
        .where(RenterDocument.user_id.in_(renter_ids))
    )
    docs_map: dict[str, set[str]] = {}
    for user_id, doc_type in docs_result.all():
        docs_map.setdefault(user_id, set()).add(doc_type)

    response = []
    for app in apps:
        profile = profiles_map.get(app.user_id)
        doc_types = docs_map.get(app.user_id, set())
        is_verified = set(REQUIRED_DOC_TYPES).issubset(doc_types)

        renter_phone = None
        renter_email = None
        if app.status == "Shortlisted" and profile:
            renter_phone = profile.phone
            renter_email = profile.email

        response.append(ApplicationForAgent(
            id=app.id,
            user_id=app.user_id,
            listing_id=app.listing_id,
            status=app.status,
            applied_at=app.applied_at,
            renter_name=profile.full_name if profile else None,
            renter_employment=profile.employment_status if profile else None,
            renter_income=profile.monthly_income if profile else None,
            renter_id_masked=mask_id_number(profile.id_number) if profile else None,
            is_verified=is_verified,
            renter_phone=renter_phone,
            renter_email=renter_email,
            listing_title=app.listing.title if app.listing else None,
            listing_location=app.listing.location if app.listing else None,
        ))
    return response


@router.get("/agent/{app_id}/documents")
async def agent_get_renter_documents(
    app_id: str,
    user: User = Depends(require_agent),
    db: AsyncSession = Depends(get_db),
):
    # Verify this agent owns the application
    result = await db.execute(
        select(Application)
        .where(Application.id == app_id, Application.agent_user_id == user.id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(404, "Application not found")

    docs_result = await db.execute(
        select(RenterDocument).where(RenterDocument.user_id == app.user_id)
    )
    docs = docs_result.scalars().all()
    return [
        {"id": str(d.id), "document_type": d.document_type, "file_name": d.file_name}
        for d in docs
    ]


@router.put("/{app_id}/status", response_model=ApplicationResponse)
async def update_application_status(
    app_id: str,
    req: ApplicationStatusUpdate,
    user: User = Depends(require_agent),
    db: AsyncSession = Depends(get_db),
):
    if req.status not in {"Viewed", "Shortlisted", "Rejected"}:
        raise HTTPException(400, "Invalid status")

    result = await db.execute(
        select(Application)
        .where(Application.id == app_id, Application.agent_user_id == user.id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(404, "Application not found")

    app.status = req.status
    await db.commit()
    await db.refresh(app)
    return app
