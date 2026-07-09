export interface LocationInput {
  name: string;
  address: string;
  lat?: number;
  lng?: number;
  place_id?: string;
}

export interface SearchHardFilters {
  suburb?: string;
  bedrooms?: number;
  bathrooms?: number;
  min_price?: number;
  max_price?: number;
  property_type?: string;
  furnished?: boolean;
  pets_allowed?: boolean;
}

export interface SearchRequest {
  query_text: string;
  location?: LocationInput;
  preferences?: string[];
  hard_filters?: SearchHardFilters;
}

export interface SearchResult {
  id: string;
  title: string;
  location: string | null;
  price: string | null;
  beds: number | null;
  baths: number | null;
  size: string | null;
  furnished: boolean | null;
  pets: boolean | null;
  lease: string | null;
  amenities: string[];
  match_score: number | null;
  matched: string[];
  not_matched: string[];
  match_reason: string | null;
  url: string | null;
  source: string | null;
  image_url: string | null;
  availability: string | null;
  rank: number;
}

export interface InterpretedTag {
  label: string;
  category: string;
}

export interface Search {
  id: string;
  query_text: string;
  status: "pending" | "interpreting" | "searching" | "complete" | "failed";
  interpreted_intent: {
    location?: LocationInput;
    intent?: {
      interpreted_tags: InterpretedTag[];
      missing: { icon: string; label: string; detail: string }[];
      improved_prompt: string;
      rank_guidance: string;
    };
  } | null;
  error_message: string | null;
  created_at: string;
  results: SearchResult[];
}

export interface SearchHistoryItem {
  id: string;
  query_text: string;
  status: string;
  created_at: string;
}

export interface SavedListing {
  id: string;
  user_id: string;
  listing_id: string | null;
  url: string | null;
  title: string;
  location: string | null;
  price: string | null;
  source: string | null;
  image_url: string | null;
  saved_at: string;
}

export interface AutocompletePrediction {
  place_id: string;
  main_text: string;
  secondary_text: string;
  description: string;
}

export interface NearbyPlace {
  name: string;
  icon: string;
  category: string;
  distance: string;
}

export interface DemoPlace {
  main: string;
  sec: string;
  type: string;
  icon: string;
  lat: number;
  lng: number;
}

export interface PropertyListingCreate {
  title: string;
  location: string;
  price: string;
  bedrooms: number;
  bathrooms: number;
  size?: string;
  furnished: "yes" | "no" | "partially";
  pets_allowed: boolean;
  lease_type?: string;
  amenities: string[];
  description?: string;
  contact_name: string;
  contact_email: string;
  contact_phone?: string;
  image_url?: string;
  available_from?: string;
}

export interface PropertyListingResponse extends PropertyListingCreate {
  id: string;
  status: string;
  created_at: string;
}

export interface BuyerSearchRequest {
  query: string;
  filters: string[];
}

export interface RankedListing {
  id: string;
  title: string;
  location: string;
  price: string;
  bedrooms: number;
  bathrooms: number;
  size: string | null;
  furnished: string;
  pets_allowed: boolean;
  amenities: string[];
  description: string | null;
  image_url: string | null;
  contact_name: string;
  contact_phone: string | null;
  match_pct: number;
  match_reason: string;
}

export interface BuyerSearchResponse {
  results: RankedListing[];
}

export interface RenterProfile {
  user_id: string;
  full_name: string | null;
  id_number: string | null;
  phone: string | null;
  email: string | null;
  employment_status: string | null;
  monthly_income: string | null;
  employer_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface RenterDocument {
  id: string;
  user_id: string;
  document_type: string;
  file_name: string;
  uploaded_at: string;
}

export interface ApplicationWithListing {
  id: string;
  user_id: string;
  listing_id: string;
  agent_user_id: string | null;
  status: string;
  applied_at: string;
  updated_at: string;
  listing_title: string | null;
  listing_location: string | null;
  listing_price: string | null;
  listing_image_url: string | null;
  agent_name: string | null;
}

export interface ApplicationForAgent {
  id: string;
  user_id: string;
  listing_id: string;
  status: string;
  applied_at: string;
  renter_name: string | null;
  renter_employment: string | null;
  renter_income: string | null;
  renter_id_masked: string | null;
  is_verified: boolean;
  renter_phone: string | null;
  renter_email: string | null;
  listing_title: string | null;
  listing_location: string | null;
}

export interface EligibilityCheck {
  eligible: boolean;
  missing_profile_fields: string[];
  missing_documents: string[];
}

export interface ConversationMessage {
  id: string;
  conversation_id: string;
  sender_user_id: string;
  body: string;
  created_at: string;
  read_at: string | null;
}

export interface ConversationSummary {
  id: string;
  listing_id: string;
  listing_title: string;
  listing_location: string;
  listing_price: string;
  listing_image_url: string | null;
  counterpart_name: string | null;
  last_message_preview: string | null;
  last_message_at: string;
  unread_count: number;
}

export interface ConversationDetail extends ConversationSummary {
  counterpart_user_id: string;
  messages: ConversationMessage[];
}
