import client from "./client";
import type { RenterProfile, RenterDocument } from "../types";

export async function getProfile(): Promise<RenterProfile> {
  const { data } = await client.get("/renter/profile");
  return data;
}

export async function updateProfile(profile: Partial<RenterProfile>): Promise<RenterProfile> {
  const { data } = await client.put("/renter/profile", profile);
  return data;
}

export async function getDocuments(): Promise<RenterDocument[]> {
  const { data } = await client.get("/renter/documents");
  return data;
}

export async function uploadDocument(documentType: string, file: File): Promise<RenterDocument> {
  const form = new FormData();
  form.append("document_type", documentType);
  form.append("file", file);
  const { data } = await client.post("/renter/documents", form);
  return data;
}

export async function deleteDocument(docId: string): Promise<void> {
  await client.delete(`/renter/documents/${docId}`);
}
