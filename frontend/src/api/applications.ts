import client from "./client";
import type { ApplicationWithListing, ApplicationForAgent, EligibilityCheck } from "../types";

export async function checkEligible(): Promise<EligibilityCheck> {
  const { data } = await client.get("/applications/check-eligible");
  return data;
}

export async function createApplication(listingId: string): Promise<unknown> {
  const { data } = await client.post("/applications", { listing_id: listingId });
  return data;
}

export async function getMyApplications(): Promise<ApplicationWithListing[]> {
  const { data } = await client.get("/applications/mine");
  return data;
}

export async function withdrawApplication(appId: string): Promise<unknown> {
  const { data } = await client.put(`/applications/${appId}/withdraw`);
  return data;
}

export async function getAgentApplications(): Promise<ApplicationForAgent[]> {
  const { data } = await client.get("/applications/agent");
  return data;
}

export async function updateApplicationStatus(appId: string, status: string): Promise<unknown> {
  const { data } = await client.put(`/applications/${appId}/status`, { status });
  return data;
}

export async function getAgentDocuments(appId: string): Promise<{ id: string; document_type: string; file_name: string }[]> {
  const { data } = await client.get(`/applications/agent/${appId}/documents`);
  return data;
}
