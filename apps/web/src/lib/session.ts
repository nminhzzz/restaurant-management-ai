export interface Session {
  token: string;
  role: string;
  username: string;
}

const KEY = "session";
const SESSION_EVENT = "session-change";

function notify(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(SESSION_EVENT));
}

export function saveSession(s: Session): void {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(KEY, JSON.stringify(s));
  notify();
}

export function parseSession(raw: string | null): Session | null {
  if (!raw) return null;
  try {
    return JSON.parse(raw) as Session;
  } catch {
    return null;
  }
}

/** Raw stored value — stable across renders, which `useSyncExternalStore` requires. */
export function sessionSnapshot(): string | null {
  if (typeof window === "undefined") return null;
  return window.sessionStorage.getItem(KEY);
}

export function serverSessionSnapshot(): string | null {
  return null;
}

export function subscribeSession(listener: () => void): () => void {
  if (typeof window === "undefined") return () => {};
  window.addEventListener(SESSION_EVENT, listener);
  window.addEventListener("storage", listener);
  return () => {
    window.removeEventListener(SESSION_EVENT, listener);
    window.removeEventListener("storage", listener);
  };
}

export function loadSession(): Session | null {
  return parseSession(sessionSnapshot());
}

export function clearSession(): void {
  if (typeof window === "undefined") return;
  sessionStorage.removeItem(KEY);
  notify();
}

export function authHeaders(): Record<string, string> {
  const s = loadSession();
  if (!s) return {};
  return { Authorization: `Bearer ${s.token}` };
}
