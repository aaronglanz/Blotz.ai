import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import RenterProfile, RenterDocument, DocumentAccessLog
from app.schemas import RenterProfileUpdate, RenterProfileResponse, RenterDocumentResponse
from app.services.auth import get_user_id_flexible as get_user_id

router = APIRouter(prefix="/api/renter", tags=["renter"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_DOC_TYPES = {"id_document", "bank_statement_1", "bank_statement_2", "bank_statement_3", "payslip", "reference_letter"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.get("/profile", response_model=RenterProfileResponse)
async def get_profile(user_id: str = Depends(get_user_id), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RenterProfile).where(RenterProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = RenterProfile(user_id=user_id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile


@router.put("/profile", response_model=RenterProfileResponse)
async def update_profile(req: RenterProfileUpdate, user_id: str = Depends(get_user_id), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RenterProfile).where(RenterProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = RenterProfile(user_id=user_id)
        db.add(profile)

    for key, val in req.model_dump(exclude_unset=True).items():
        setattr(profile, key, val)

    await db.commit()
    await db.refresh(profile)
    return profile


@router.get("/documents", response_model=list[RenterDocumentResponse])
async def get_documents(user_id: str = Depends(get_user_id), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RenterDocument)
        .where(RenterDocument.user_id == user_id)
        .order_by(RenterDocument.uploaded_at.desc())
    )
    return result.scalars().all()


@router.post("/documents", response_model=RenterDocumentResponse)
async def upload_document(
    document_type: str = Form(...),
    file: UploadFile = File(...),
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    if document_type not in ALLOWED_DOC_TYPES:
        raise HTTPException(400, f"Invalid document type. Must be one of: {', '.join(ALLOWED_DOC_TYPES)}")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large. Maximum 10MB.")

    ext = os.path.splitext(file.filename or "file")[1].lower()
    if ext not in {".pdf", ".jpg", ".jpeg", ".png"}:
        raise HTTPException(400, "Only PDF and image files (JPG, PNG) are accepted.")

    # Delete existing document of same type for this user
    existing = await db.execute(
        select(RenterDocument)
        .where(RenterDocument.user_id == user_id, RenterDocument.document_type == document_type)
    )
    for old_doc in existing.scalars().all():
        if os.path.exists(old_doc.file_path):
            os.remove(old_doc.file_path)
        await db.delete(old_doc)

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")

    with open(file_path, "wb") as f:
        f.write(content)

    doc = RenterDocument(
        id=uuid.uuid4(),
        user_id=user_id,
        document_type=document_type,
        file_path=file_path,
        file_name=file.filename or "document",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, user_id: str = Depends(get_user_id), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RenterDocument)
        .where(RenterDocument.id == doc_id, RenterDocument.user_id == user_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")

    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    await db.delete(doc)
    await db.commit()
    return {"ok": True}


@router.get("/documents/{doc_id}/download")
async def download_document(
    doc_id: str,
    user_id: str = Depends(get_user_id),
    agent_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(RenterDocument).where(RenterDocument.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")

    # If requester is the owner, allow
    if doc.user_id != user_id and not agent_id:
        raise HTTPException(403, "Not authorised")

    # Log agent access
    if agent_id and doc.user_id != user_id:
        log = DocumentAccessLog(agent_id=agent_id, document_id=doc.id)
        db.add(log)
        await db.commit()

    if not os.path.exists(doc.file_path):
        raise HTTPException(404, "File not found on disk")

    return FileResponse(doc.file_path, filename=doc.file_name)
