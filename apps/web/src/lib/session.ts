export interface Session {
  token: string;
  role: string;
  username: string;
  /** Epoch ms; the JWT itself expires after 8 hours too. */
  expires_at?: number;
}

const KEY = "session";
const SESSION_EVENT = "session-change";
const NOTICE_KEY = "session-notice";
// Matches ACCESS_TOKEN_TTL_MINUTES (480) so the stored session and the JWT die together.
const SESSION_TTL_MS = 8 * 60 * 60 * 1000;

function notify(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(SESSION_EVENT));
}

function storage(): Storage | null {
  if (typeof window === "undefined") return null;
  return window.localStorage;
}

function readRaw(): string | null {
  const store = storage();
  if (store === null) return null;
  let raw = store.getItem(KEY);
  if (raw === null) {
    // Sessions used to live in sessionStorage (one tab, lost on close). Move the
    // current one over so the change does not force an extra login.
    const legacy = window.sessionStorage.getItem(KEY);
    if (legacy !== null) {
      store.setItem(KEY, legacy);
      window.sessionStorage.removeItem(KEY);
      raw = legacy;
    }
  }
  if (raw === null) return null;
  try {
    const parsed = JSON.parse(raw) as Session;
    if (
      typeof parsed.expires_at === "number" &&
      parsed.expires_at <= Date.now()
    ) {
      store.removeItem(KEY);
      return null;
    }
  } catch {
    store.removeItem(KEY);
    return null;
  }
  return raw;
}

export function saveSession(s: Session): void {
  const store = storage();
  if (store === null) return;
  const value: Session = { ...s, expires_at: Date.now() + SESSION_TTL_MS };
  store.setItem(KEY, JSON.stringify(value));
  window.sessionStorage.removeItem(NOTICE_KEY);
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
  return readRaw();
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
  const store = storage();
  store?.removeItem(KEY);
  window.sessionStorage.removeItem(KEY);
  notify();
}

export function expireSession(
  expectedToken: string,
  message = "Phiên đăng nhập đã hết hạn hoặc bị thu hồi. Vui lòng đăng nhập lại.",
): void {
  // An old request arriving after a fresh login must not log the new user out.
  if (loadSession()?.token !== expectedToken) return;
  window.sessionStorage.setItem(NOTICE_KEY, message);
  clearSession();
}

export function sessionNotice(): string | null {
  if (typeof window === "undefined") return null;
  return window.sessionStorage.getItem(NOTICE_KEY);
}

export function authHeaders(): Record<string, string> {
  const s = loadSession();
  if (!s) return {};
  return { Authorization: `Bearer ${s.token}` };
}
