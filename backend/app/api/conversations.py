import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Conversation, ConversationMessage, PropertyListing, RenterProfile, User
from app.schemas import (
    ConversationDetailResponse,
    ConversationEnsureRequest,
    ConversationMessageCreate,
    ConversationMessageResponse,
    ConversationSummaryResponse,
)
from app.services.auth import get_user_id_flexible as get_user_id, require_agent

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def get_conversation_for_user(
    conversation_id: str,
    user_id: str,
    db: AsyncSession,
) -> Conversation:
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            or_(
                Conversation.renter_user_id == user_id,
                Conversation.agent_user_id == user_id,
            ),
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(404, "Conversation not found")
    return conversation


async def build_summary(
    conversation: Conversation,
    user_id: str,
    db: AsyncSession,
) -> ConversationSummaryResponse:
    # Use pre-loaded listing if available, otherwise query
    listing = conversation.listing

    last_message_result = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation.id)
        .order_by(ConversationMessage.created_at.desc())
        .limit(1)
    )
    last_message = last_message_result.scalar_one_or_none()

    unread_stmt: Select[tuple[int]] = select(func.count(ConversationMessage.id)).where(
        ConversationMessage.conversation_id == conversation.id,
        ConversationMessage.sender_user_id != user_id,
        ConversationMessage.read_at.is_(None),
    )
    unread_result = await db.execute(unread_stmt)
    unread_count = unread_result.scalar_one()

    counterpart_user_id = (
        conversation.agent_user_id
        if conversation.renter_user_id == user_id
        else conversation.renter_user_id
    )
    counterpart_name = listing.contact_name if listing else "Agent"
    if conversation.renter_user_id != user_id:
        profile_result = await db.execute(
            select(RenterProfile).where(RenterProfile.user_id == counterpart_user_id)
        )
        profile = profile_result.scalar_one_or_none()
        counterpart_name = profile.full_name if profile and profile.full_name else "Renter"

    return ConversationSummaryResponse(
        id=conversation.id,
        listing_id=conversation.listing_id,
        listing_title=listing.title if listing else "Listing",
        listing_location=listing.location if listing else "Cape Town",
        listing_price=listing.price if listing else "Price on request",
        listing_image_url=listing.image_url if listing else None,
        counterpart_name=counterpart_name,
        last_message_preview=last_message.body[:120] if last_message else None,
        last_message_at=conversation.last_message_at,
        unread_count=unread_count,
    )


@router.get("/mine", response_model=list[ConversationSummaryResponse])
async def list_my_conversations(
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.listing))
        .where(Conversation.renter_user_id == user_id)
        .order_by(Conversation.last_message_at.desc())
    )
    conversations = result.scalars().all()
    return [await build_summary(conversation, user_id, db) for conversation in conversations]


@router.get("/agent", response_model=list[ConversationSummaryResponse])
async def list_agent_conversations(
    user: User = Depends(require_agent),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.listing))
        .where(Conversation.agent_user_id == user.id)
        .order_by(Conversation.last_message_at.desc())
    )
    conversations = result.scalars().all()
    return [await build_summary(conversation, user.id, db) for conversation in conversations]


@router.post("/ensure", response_model=ConversationDetailResponse)
async def ensure_conversation(
    req: ConversationEnsureRequest,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    listing_result = await db.execute(
        select(PropertyListing).where(PropertyListing.id == req.listing_id)
    )
    listing = listing_result.scalar_one_or_none()
    if not listing:
        raise HTTPException(404, "Listing not found")
    if not listing.user_id:
        raise HTTPException(400, "This listing cannot receive messages yet")

    result = await db.execute(
        select(Conversation).where(
            Conversation.renter_user_id == user_id,
            Conversation.listing_id == req.listing_id,
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        conversation = Conversation(
            id=uuid.uuid4(),
            renter_user_id=user_id,
            agent_user_id=listing.user_id,
            listing_id=req.listing_id,
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)

    messages_result = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation.id)
        .order_by(ConversationMessage.created_at.asc())
    )
    messages = messages_result.scalars().all()
    summary = await build_summary(conversation, user_id, db)
    return ConversationDetailResponse(
        **summary.model_dump(),
        counterpart_user_id=conversation.agent_user_id,
        messages=[ConversationMessageResponse.model_validate(message) for message in messages],
    )


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    conversation = await get_conversation_for_user(conversation_id, user_id, db)
    messages_result = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation.id)
        .order_by(ConversationMessage.created_at.asc())
    )
    messages = messages_result.scalars().all()

    updated = False
    for message in messages:
        if message.sender_user_id != user_id and message.read_at is None:
            message.read_at = utcnow()
            updated = True
    if updated:
        await db.commit()

    summary = await build_summary(conversation, user_id, db)
    counterpart_user_id = (
        conversation.agent_user_id
        if conversation.renter_user_id == user_id
        else conversation.renter_user_id
    )
    return ConversationDetailResponse(
        **summary.model_dump(),
        counterpart_user_id=counterpart_user_id,
        messages=[ConversationMessageResponse.model_validate(message) for message in messages],
    )


@router.post("/{conversation_id}/messages", response_model=ConversationMessageResponse)
async def send_message(
    conversation_id: str,
    req: ConversationMessageCreate,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    conversation = await get_conversation_for_user(conversation_id, user_id, db)
    body = req.body.strip()
    if not body:
        raise HTTPException(400, "Message body is required")

    message = ConversationMessage(
        id=uuid.uuid4(),
        conversation_id=conversation.id,
        sender_user_id=user_id,
        body=body,
    )
    db.add(message)
    conversation.last_message_at = utcnow()
    await db.commit()
    await db.refresh(message)
    return message
