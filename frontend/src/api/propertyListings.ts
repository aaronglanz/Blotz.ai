import client from "./client";
import type {
  PropertyListingCreate,
  PropertyListingResponse,
  BuyerSearchRequest,
  BuyerSearchResponse,
} from "../types";

export async function createPropertyListing(
  listing: PropertyListingCreate,
): Promise<PropertyListingResponse> {
  const { data } = await client.post("/property-listings", listing);
  return data;
}

export async function getPropertyListings(): Promise<PropertyListingResponse[]> {
  const { data } = await client.get("/property-listings");
  return data;
}

export async function getPropertyListing(
  id: string,
): Promise<PropertyListingResponse> {
  const { data } = await client.get(`/property-listings/${id}`);
  return data;
}

export async function searchPropertyListings(
  req: BuyerSearchRequest,
): Promise<BuyerSearchResponse> {
  const { data } = await client.post("/property-listings/search", req);
  return data;
}
