import client from "./client";
import type { SavedListing } from "../types";

export async function saveListing(listing: {
  listing_id?: string | null;
  url?: string | null;
  title: string;
  location?: string | null;
  price?: string | null;
  source?: string | null;
  image_url?: string | null;
}): Promise<SavedListing> {
  const { data } = await client.post("/listings/save", listing);
  return data;
}

export async function unsaveListing(listingId: string): Promise<void> {
  await client.delete(`/listings/saved/${listingId}`);
}

export async function getSavedListings(): Promise<SavedListing[]> {
  const { data } = await client.get("/listings/saved");
  return data;
}
