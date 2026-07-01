export interface AgentAccount {
  id: string;
  full_name: string;
  email: string;
  role: string;
  phone: string;
  agency_name: string;
}

export interface AgentSession {
  access_token: string;
  user: AgentAccount;
}

const STORAGE_KEY = "nestly_agent_session";

function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.exp * 1000 < Date.now();
  } catch {
    return true;
  }
}

export function getAgentSession(): AgentSession | null {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;

  try {
    const session = JSON.parse(raw) as AgentSession;
    if (isTokenExpired(session.access_token)) {
      localStorage.removeItem(STORAGE_KEY);
      return null;
    }
    return session;
  } catch {
    return null;
  }
}

export function getAgentAccount(): AgentAccount | null {
  return getAgentSession()?.user || null;
}

export function saveAgentSession(session: AgentSession) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
}

export function clearAgentSession() {
  localStorage.removeItem(STORAGE_KEY);
}

export function hasAgentAccount(): boolean {
  return !!getAgentSession()?.access_token;
}
