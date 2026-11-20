"use client";

import { useEffect, useRef } from "react";

/**
 * Call `callback` every `ms` while the browser tab is visible, and once more when
 * the tab becomes visible again. Meant for silent background refreshes.
 */
export function useVisibleInterval(
  callback: () => void,
  ms: number,
  enabled = true,
): void {
  const latest = useRef(callback);
  useEffect(() => {
    latest.current = callback;
  }, [callback]);

  useEffect(() => {
    if (!enabled) return;
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") latest.current();
    }, ms);
    const onVisibility = () => {
      if (document.visibilityState === "visible") latest.current();
    };
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [ms, enabled]);
}
