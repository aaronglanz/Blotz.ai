from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RenterDocument, RenterProfile

REQUIRED_PROFILE_FIELDS = [
    "full_name",
    "id_number",
    "phone",
    "email",
    "employment_status",
    "monthly_income",
]
REQUIRED_DOC_TYPES = [
    "id_document",
    "bank_statement_1",
    "bank_statement_2",
    "bank_statement_3",
    "payslip",
]


async def get_profile_and_doc_gaps(user_id: str, db: AsyncSession) -> tuple[list[str], list[str]]:
    result = await db.execute(select(RenterProfile).where(RenterProfile.user_id == user_id))
    profile = result.scalar_one_or_none()

    missing_profile_fields: list[str] = []
    if not profile:
        missing_profile_fields = REQUIRED_PROFILE_FIELDS.copy()
    else:
        missing_profile_fields = [
            field for field in REQUIRED_PROFILE_FIELDS if not getattr(profile, field, None)
        ]

    docs_result = await db.execute(
        select(RenterDocument.document_type).where(RenterDocument.user_id == user_id)
    )
    doc_types = {row[0] for row in docs_result.all()}
    missing_documents = [doc_type for doc_type in REQUIRED_DOC_TYPES if doc_type not in doc_types]

    return missing_profile_fields, missing_documents


async def is_profile_complete(user_id: str, db: AsyncSession) -> bool:
    missing_profile_fields, missing_documents = await get_profile_and_doc_gaps(user_id, db)
    return not missing_profile_fields and not missing_documents
