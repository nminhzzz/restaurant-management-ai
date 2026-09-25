"use client";

import { useCallback, useState } from "react";
import { toast } from "sonner";

import { ApiError } from "@/lib/api-client";

const FALLBACK = "Không thực hiện được. Kiểm tra kết nối rồi thử lại.";

/**
 * Run one write call (POST/PATCH/DELETE) with a pending flag and a toast either way.
 * Returns the call's result, or `undefined` when it failed — the toast already told
 * the user why, and `error` keeps the message for inline display.
 */
export function useAction() {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(
    async <T>(
      call: () => Promise<T>,
      success?: string | ((result: T) => string),
    ): Promise<T | undefined> => {
      setPending(true);
      setError(null);
      try {
        const result = await call();
        if (success) {
          toast.success(
            typeof success === "string" ? success : success(result),
          );
        }
        return result;
      } catch (cause) {
        const message = cause instanceof ApiError ? cause.message : FALLBACK;
        setError(message);
        toast.error(message);
        return undefined;
      } finally {
        setPending(false);
      }
    },
    [],
  );

  return { run, pending, error, clearError: () => setError(null) };
}
