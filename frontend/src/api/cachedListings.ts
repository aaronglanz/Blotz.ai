import client from "./client";

export interface CachedListing {
  id: string;
  source: string;
  source_url: string;
  source_id: string | null;
  title: string;
  location: string;
  suburb: string | null;
  city: string;
  price_amount: number | null;
  price_display: string;
  bedrooms: number | null;
  bathrooms: number | null;
  size_sqm: number | null;
  property_type: string | null;
  furnished: boolean | null;
  pets_allowed: boolean | null;
  description: string | null;
  amenities: string[];
  image_url: string | null;
  image_urls: string[];
  contact_name: string | null;
  contact_phone: string | null;
  available_from: string | null;
  first_seen_at: string;
  last_seen_at: string;
}

export interface BrowseListingsResponse {
  listings: CachedListing[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface BrowseFilters {
  q?: string;
  suburb?: string;
  min_price?: number;
  max_price?: number;
  bedrooms?: number;
  min_bedrooms?: number;
  bathrooms?: number;
  property_type?: string;
  furnished?: boolean;
  pets_allowed?: boolean;
  sort_by?: "newest" | "price_asc" | "price_desc" | "bedrooms";
  page?: number;
  per_page?: number;
}

export interface SuburbInfo {
  name: string;
  count: number;
}

export interface ListingStats {
  total_active: number;
  avg_price: number | null;
  last_updated: string | null;
}

export async function browseListings(
  filters: BrowseFilters = {}
): Promise<BrowseListingsResponse> {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  }
  const { data } = await client.get(
    `/api/cached-listings?${params.toString()}`
  );
  return data;
}

export async function getListingById(id: string): Promise<CachedListing> {
  const { data } = await client.get(`/api/cached-listings/${id}`);
  return data;
}

export async function getSuburbs(): Promise<SuburbInfo[]> {
  const { data } = await client.get("/api/cached-listings/suburbs");
  return data;
}

export async function getListingStats(): Promise<ListingStats> {
  const { data } = await client.get("/api/cached-listings/stats");
  return data;
}

export async function triggerScrape(
  maxPages = 5
): Promise<{ task_id: string; status: string }> {
  const { data } = await client.post(
    `/api/cached-listings/scrape?max_pages=${maxPages}`
  );
  return data;
}
