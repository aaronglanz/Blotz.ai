import client from "./client";
import type { AutocompletePrediction, NearbyPlace } from "../types";

export async function autocomplete(input: string): Promise<AutocompletePrediction[]> {
  const { data } = await client.get("/locations/autocomplete", { params: { input } });
  return data.predictions;
}

export async function getNearby(placeId: string, lat: number, lng: number): Promise<NearbyPlace[]> {
  const { data } = await client.get(`/locations/${placeId}/nearby`, { params: { lat, lng } });
  return data.places;
}
