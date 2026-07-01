import client from "./client";
import type { ConversationDetail, ConversationMessage, ConversationSummary } from "../types";

export async function getMyConversations(): Promise<ConversationSummary[]> {
  const { data } = await client.get("/conversations/mine");
  return data;
}

export async function getAgentConversations(): Promise<ConversationSummary[]> {
  const { data } = await client.get("/conversations/agent");
  return data;
}

export async function ensureConversation(listingId: string): Promise<ConversationDetail> {
  const { data } = await client.post("/conversations/ensure", { listing_id: listingId });
  return data;
}

export async function getConversation(conversationId: string): Promise<ConversationDetail> {
  const { data } = await client.get(`/conversations/${conversationId}`);
  return data;
}

export async function sendConversationMessage(
  conversationId: string,
  body: string,
): Promise<ConversationMessage> {
  const { data } = await client.post(`/conversations/${conversationId}/messages`, { body });
  return data;
}
