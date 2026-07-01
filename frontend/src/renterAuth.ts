export interface RenterAccount {
  id: string;
  full_name: string;
  email: string;
  role: string;
}

export interface RenterSession {
  access_token: string;
  user: RenterAccount;
}

const STORAGE_KEY = "nestly_renter_session";

function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.exp * 1000 < Date.now();
  } catch {
    return true;
  }
}

export function getRenterSession(): RenterSession | null {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;

  try {
    const session = JSON.parse(raw) as RenterSession;
    if (isTokenExpired(session.access_token)) {
      localStorage.removeItem(STORAGE_KEY);
      return null;
    }
    return session;
  } catch {
    return null;
  }
}

export function getRenterAccount(): RenterAccount | null {
  return getRenterSession()?.user || null;
}

export function saveRenterSession(session: RenterSession) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
}

export function clearRenterSession() {
  localStorage.removeItem(STORAGE_KEY);
}

export function isRenterLoggedIn(): boolean {
  return !!getRenterSession()?.access_token;
}
