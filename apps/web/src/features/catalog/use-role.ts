"use client";

import { useMemo, useSyncExternalStore } from "react";

import {
  parseSession,
  serverSessionSnapshot,
  sessionSnapshot,
  subscribeSession,
} from "@/lib/session";

/** Mirrors the session-reading pattern in features/assistant/assistant-screen.tsx. */
export function useRole(): string | null {
  const stored = useSyncExternalStore(
    subscribeSession,
    sessionSnapshot,
    serverSessionSnapshot,
  );
  return useMemo(() => parseSession(stored)?.role ?? null, [stored]);
}

/**
 * UX-only gate: the API still enforces role checks server-side. Used to hide (not
 * disable) write actions for roles that the permission matrix does not allow.
 */
export function useCanWrite(allowedRoles: string[]): boolean {
  const role = useRole();
  return role !== null && allowedRoles.includes(role);
}
