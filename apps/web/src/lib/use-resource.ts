"use client";

import { useCallback, useEffect, useState } from "react";

import { ApiError } from "@/lib/api-client";

export type Resource<T> =
  | { status: "loading" }
  | { status: "ready"; data: T }
  | { status: "error"; message: string };

const FALLBACK = "Không tải được dữ liệu. Kiểm tra kết nối rồi thử lại.";

/**
 * Load data for a screen. `fetcher` must be stable (module-level or `useCallback`);
 * a new identity refetches, which is how callers express "reload when X changes".
 */
export function useResource<T>(
  fetcher: () => Promise<T>,
): Resource<T> & { reload: () => void } {
  const [state, setState] = useState<Resource<T>>({ status: "loading" });
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let active = true;
    fetcher().then(
      (data) => active && setState({ status: "ready", data }),
      (error: unknown) =>
        active &&
        setState({
          status: "error",
          message: error instanceof ApiError ? error.message : FALLBACK,
        }),
    );
    return () => {
      active = false;
    };
  }, [fetcher, version]);

  const reload = useCallback(() => {
    setState({ status: "loading" });
    setVersion((value) => value + 1);
  }, []);

  return { ...state, reload };
}
