import client from "./client";
import type { Search, SearchHistoryItem, SearchRequest } from "../types";

export async function submitSearch(req: SearchRequest): Promise<{ id: string; status: string }> {
  const { data } = await client.post("/search", req);
  return data;
}

export async function getSearch(searchId: string): Promise<Search> {
  const { data } = await client.get(`/search/${searchId}`);
  return data;
}

export async function getSearchHistory(): Promise<SearchHistoryItem[]> {
  const { data } = await client.get("/search/history");
  return data;
}
