import uuid
from datetime import datetime

from pydantic import BaseModel


class LocationInput(BaseModel):
    name: str
    address: str
    lat: float | None = None
    lng: float | None = None
    place_id: str | None = None


class SearchHardFilters(BaseModel):
    suburb: str | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
    min_price: int | None = None
    max_price: int | None = None
    property_type: str | None = None
    furnished: bool | None = None
    pets_allowed: bool | None = None


class SearchRequest(BaseModel):
    query_text: str
    location: LocationInput | None = None
    preferences: list[str] | None = None
    hard_filters: SearchHardFilters | None = None


class SearchResultSchema(BaseModel):
    id: uuid.UUID
    title: str
    location: str | None = None
    price: str | None = None
    beds: int | None = None
    baths: int | None = None
    size: str | None = None
    furnished: bool | None = None
    pets: bool | None = None
    lease: str | None = None
    amenities: list = []
    match_score: int | None = None
    matched: list = []
    not_matched: list = []
    match_reason: str | None = None
    url: str | None = None
    source: str | None = None
    image_url: str | None = None
    availability: str | None = None
    rank: int

    model_config = {"from_attributes": True}


class SearchResponse(BaseModel):
    id: uuid.UUID
    query_text: str
    status: str
    interpreted_intent: dict | None = None
    error_message: str | None = None
    created_at: datetime
    results: list[SearchResultSchema] = []

    model_config = {"from_attributes": True}


class SearchHistoryItem(BaseModel):
    id: uuid.UUID
    query_text: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    full_name: str
    phone: str | None = None
    agency_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentSignUpRequest(BaseModel):
    full_name: str
    email: str
    password: str
    phone: str
    agency_name: str


class RenterSignUpRequest(BaseModel):
    full_name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class SaveListingRequest(BaseModel):
    listing_id: uuid.UUID | None = None
    url: str | None = None
    title: str
    location: str | None = None
    price: str | None = None
    source: str | None = None
    image_url: str | None = None


class SavedListingResponse(BaseModel):
    id: uuid.UUID
    user_id: str
    listing_id: uuid.UUID | None = None
    url: str | None = None
    title: str
    location: str | None = None
    price: str | None = None
    source: str | None = None
    image_url: str | None = None
    saved_at: datetime

    model_config = {"from_attributes": True}


class AutocompletePrediction(BaseModel):
    place_id: str
    main_text: str
    secondary_text: str
    description: str


class NearbyPlace(BaseModel):
    name: str
    icon: str
    category: str
    distance: str


class RenterProfileUpdate(BaseModel):
    full_name: str | None = None
    id_number: str | None = None
    phone: str | None = None
    email: str | None = None
    employment_status: str | None = None
    monthly_income: str | None = None
    employer_name: str | None = None


class RenterProfileResponse(BaseModel):
    user_id: str
    full_name: str | None = None
    id_number: str | None = None
    phone: str | None = None
    email: str | None = None
    employment_status: str | None = None
    monthly_income: str | None = None
    employer_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RenterDocumentResponse(BaseModel):
    id: uuid.UUID
    user_id: str
    document_type: str
    file_name: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class ApplicationCreate(BaseModel):
    listing_id: str


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    user_id: str
    listing_id: uuid.UUID
    agent_user_id: str | None = None
    status: str
    applied_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApplicationWithListing(ApplicationResponse):
    listing_title: str | None = None
    listing_location: str | None = None
    listing_price: str | None = None
    listing_image_url: str | None = None
    agent_name: str | None = None


class ApplicationForAgent(BaseModel):
    id: uuid.UUID
    user_id: str
    listing_id: uuid.UUID
    status: str
    applied_at: datetime
    renter_name: str | None = None
    renter_employment: str | None = None
    renter_income: str | None = None
    renter_id_masked: str | None = None
    is_verified: bool = False
    renter_phone: str | None = None
    renter_email: str | None = None
    listing_title: str | None = None
    listing_location: str | None = None

    model_config = {"from_attributes": True}


class ApplicationStatusUpdate(BaseModel):
    status: str


class EligibilityResponse(BaseModel):
    eligible: bool
    missing_profile_fields: list[str] = []
    missing_documents: list[str] = []


class ConversationEnsureRequest(BaseModel):
    listing_id: uuid.UUID


class ConversationMessageCreate(BaseModel):
    body: str


class ConversationMessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_user_id: str
    body: str
    created_at: datetime
    read_at: datetime | None = None

    model_config = {"from_attributes": True}


class ConversationSummaryResponse(BaseModel):
    id: uuid.UUID
    listing_id: uuid.UUID
    listing_title: str
    listing_location: str
    listing_price: str
    listing_image_url: str | None = None
    counterpart_name: str | None = None
    last_message_preview: str | None = None
    last_message_at: datetime
    unread_count: int = 0


class ConversationDetailResponse(ConversationSummaryResponse):
    counterpart_user_id: str
    messages: list[ConversationMessageResponse] = []


class CachedListingResponse(BaseModel):
    id: uuid.UUID
    source: str
    source_url: str
    source_id: str | None = None
    title: str
    location: str
    suburb: str | None = None
    city: str = "Cape Town"
    price_amount: int | None = None
    price_display: str
    bedrooms: int | None = None
    bathrooms: int | None = None
    size_sqm: int | None = None
    property_type: str | None = None
    furnished: bool | None = None
    pets_allowed: bool | None = None
    description: str | None = None
    amenities: list = []
    image_url: str | None = None
    image_urls: list = []
    contact_name: str | None = None
    contact_phone: str | None = None
    available_from: str | None = None
    first_seen_at: datetime
    last_seen_at: datetime

    model_config = {"from_attributes": True}


class CachedListingFilters(BaseModel):
    q: str | None = None
    suburb: str | None = None
    min_price: int | None = None
    max_price: int | None = None
    bedrooms: int | None = None
    bathrooms: int | None = None
    property_type: str | None = None
    furnished: bool | None = None
    pets_allowed: bool | None = None


class PropertyListingCreate(BaseModel):
    title: str
    location: str
    price: str
    bedrooms: int
    bathrooms: int
    size: str | None = None
    furnished: str = "no"
    pets_allowed: bool = False
    lease_type: str | None = None
    amenities: list[str] = []
    description: str | None = None
    contact_name: str
    contact_email: str
    contact_phone: str | None = None
    image_url: str | None = None
    available_from: str | None = None


class PropertyListingResponse(BaseModel):
    id: uuid.UUID
    title: str
    location: str
    price: str
    bedrooms: int
    bathrooms: int
    size: str | None = None
    furnished: str
    pets_allowed: bool
    lease_type: str | None = None
    amenities: list[str] = []
    description: str | None = None
    contact_name: str
    contact_email: str
    contact_phone: str | None = None
    image_url: str | None = None
    available_from: str | None = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
