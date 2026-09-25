import { env } from "@/lib/env";
import { authHeaders } from "@/lib/session";
import type { ApiErrorBody } from "@/types/api";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  token?: string;
  signal?: AbortSignal;
}

export async function apiFetch<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  // Every module screen calls the API; the token lives in the session, so attach it
  // here rather than repeating it at each call site.
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...authHeaders(),
  };
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  if (options.token !== undefined)
    headers.Authorization = `Bearer ${options.token}`;

  const response = await fetch(`${env.apiBaseUrl}${env.apiPrefix}${path}`, {
    method: options.method ?? "GET",
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
    signal: options.signal,
  });

  const payload: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    const error = (payload as ApiErrorBody | null)?.error;
    throw new ApiError(
      response.status,
      error?.code ?? "UNKNOWN",
      error?.message ?? "Yêu cầu không thực hiện được.",
    );
  }

  return payload as T;
}
