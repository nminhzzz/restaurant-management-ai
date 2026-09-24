export interface Session {
  token: string;
  role: string;
  username: string;
}

const KEY = "session";

export function saveSession(s: Session): void {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(KEY, JSON.stringify(s));
}

export function loadSession(): Session | null {
  if (typeof window === "undefined") return null;
  const raw = sessionStorage.getItem(KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as Session;
  } catch {
    return null;
  }
}

export function clearSession(): void {
  if (typeof window === "undefined") return;
  sessionStorage.removeItem(KEY);
}

export function authHeaders(): Record<string, string> {
  const s = loadSession();
  if (!s) return {};
  return { Authorization: `Bearer ${s.token}` };
}
