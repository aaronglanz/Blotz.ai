import client from "./client";
import type { AgentSession } from "../agentPortal";
import type { RenterSession } from "../renterAuth";

export async function signUpAgent(input: {
  full_name: string;
  email: string;
  password: string;
  phone: string;
  agency_name: string;
}): Promise<AgentSession> {
  const { data } = await client.post("/auth/agent/signup", input);
  return data;
}

export async function loginAgent(input: {
  email: string;
  password: string;
}): Promise<AgentSession> {
  const { data } = await client.post("/auth/login", input);
  return data;
}

export async function getCurrentAgent(): Promise<AgentSession["user"]> {
  const { data } = await client.get("/auth/me");
  return data;
}

export async function signUpRenter(input: {
  full_name: string;
  email: string;
  password: string;
}): Promise<RenterSession> {
  const { data } = await client.post("/auth/renter/signup", input);
  return data;
}

export async function loginRenter(input: {
  email: string;
  password: string;
}): Promise<RenterSession> {
  const { data } = await client.post("/auth/login", input);
  return data;
}
