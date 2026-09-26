"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError, apiFetch } from "@/lib/api-client";
import type { ChatResponse, SessionDetail, TurnOut } from "@/types/api";

export type Turn = {
  id: string;
  question: string;
  status: "pending" | "done" | "failed";
  result: ChatResponse | null;
  error: string | null;
  restored: TurnOut | null;
};

export function useConversation(
  options: { onSessionCreated?: (id: number) => void } = {},
) {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [sessionId, setSessionId] = useState<number | null>(null);
  // Refs keep `ask` stable and let two quick questions see the same session id.
  const sessionRef = useRef<number | null>(null);
  const counter = useRef(0);
  // Spec §4.2: block a second send while a turn is still in flight. A ref (not
  // `pending` state) is checked so the guard sees the in-flight turn immediately,
  // without waiting for a re-render.
  const pendingRef = useRef(false);
  const onCreated = useRef(options.onSessionCreated);
  useEffect(() => {
    onCreated.current = options.onSessionCreated;
  }, [options.onSessionCreated]);
  const pending = turns.some((t) => t.status === "pending");

  const ask = useCallback(async (text: string) => {
    if (pendingRef.current) return;
    const question = text.trim();
    if (!question) return;
    pendingRef.current = true;
    const id = `t${counter.current++}`;
    setTurns((prev) => [
      ...prev,
      {
        id,
        question,
        status: "pending",
        result: null,
        error: null,
        restored: null,
      },
    ]);
    try {
      const current = sessionRef.current;
      const result = await apiFetch<ChatResponse>("/assistant/chat", {
        method: "POST",
        body:
          current === null ? { question } : { question, session_id: current },
      });
      if (current === null && result.session_id != null) {
        sessionRef.current = result.session_id;
        setSessionId(result.session_id);
        onCreated.current?.(result.session_id);
      }
      setTurns((prev) =>
        prev.map((t) => (t.id === id ? { ...t, status: "done", result } : t)),
      );
    } catch (cause) {
      const error =
        cause instanceof ApiError
          ? cause.message
          : "Không kết nối được máy chủ API.";
      setTurns((prev) =>
        prev.map((t) => (t.id === id ? { ...t, status: "failed", error } : t)),
      );
    } finally {
      pendingRef.current = false;
    }
  }, []);

  const reset = useCallback(() => {
    sessionRef.current = null;
    setSessionId(null);
    setTurns([]);
  }, []);

  const load = useCallback((detail: SessionDetail) => {
    sessionRef.current = detail.id;
    setSessionId(detail.id);
    setTurns(
      detail.turns.map((t) => ({
        id: `h${t.id}`,
        question: t.question,
        status: "done",
        result: null,
        error: null,
        restored: t,
      })),
    );
  }, []);

  return { turns, sessionId, pending, ask, reset, load };
}
