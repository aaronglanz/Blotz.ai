import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getSavedListings, saveListing, unsaveListing } from "../api/listings";
import type { RankedListing, SavedListing, SearchResult } from "../types";

type SaveableListing = SearchResult | RankedListing | SavedListing;

function getListingUrl(listing: SaveableListing): string | null {
  if ("url" in listing && listing.url) return listing.url;
  return null;
}

function getListingId(listing: SaveableListing): string | null {
  if ("listing_id" in listing) return listing.listing_id;
  if ("bedrooms" in listing) return listing.id;
  return null;
}

export function useSavedListings() {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["saved-listings"],
    queryFn: getSavedListings,
  });

  const saveMutation = useMutation({
    mutationFn: saveListing,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["saved-listings"] }),
  });

  const unsaveMutation = useMutation({
    mutationFn: unsaveListing,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["saved-listings"] }),
  });

  const savedByUrl = new Map(
    (query.data || [])
      .filter((listing) => listing.url)
      .map((listing) => [listing.url as string, listing]),
  );
  const savedByListingId = new Map(
    (query.data || [])
      .filter((listing) => listing.listing_id)
      .map((listing) => [listing.listing_id as string, listing]),
  );

  function isSaved(listing: SaveableListing): boolean {
    const listingId = getListingId(listing);
    const url = getListingUrl(listing);
    return (!!listingId && savedByListingId.has(listingId)) || (!!url && savedByUrl.has(url));
  }

  function getSavedEntry(listing: SaveableListing): SavedListing | undefined {
    const listingId = getListingId(listing);
    const url = getListingUrl(listing);
    return (listingId ? savedByListingId.get(listingId) : undefined) || (url ? savedByUrl.get(url) : undefined);
  }

  function toggleSaved(listing: SaveableListing) {
    const existing = getSavedEntry(listing);
    if (existing) {
      unsaveMutation.mutate(existing.id);
      return;
    }

    saveMutation.mutate({
      listing_id: getListingId(listing),
      url: getListingUrl(listing),
      title: listing.title,
      location: listing.location,
      price: listing.price,
      source: "source" in listing ? listing.source : "Nestly",
      image_url: listing.image_url,
    });
  }

  return {
    ...query,
    savedListings: query.data || [],
    isSaved,
    getSavedEntry,
    toggleSaved,
    isMutating: saveMutation.isPending || unsaveMutation.isPending,
  };
}
