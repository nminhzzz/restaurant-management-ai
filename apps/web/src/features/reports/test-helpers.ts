import { apiFetch } from "@/lib/api-client";

/** Sample payload for the revenue screen; mirrors the API's Decimal-as-string shape. */
export const revenueResponse = {
  total: "1000000",
  provisional: "0",
  SoDon: 2,
  items: [
    { key: "2026-09-10", DoanhThu: "400000", SoDon: 1 },
    { key: "2026-09-11", DoanhThu: "600000", SoDon: 1 },
  ],
  period: { start: "2026-09-01", end: "2026-09-30", granularity: "month" },
};

/** Make the next call to `apiFetch` resolve with `body`. */
export function stubFetch(body: unknown): void {
  (
    apiFetch as unknown as { mockResolvedValue: (value: unknown) => void }
  ).mockResolvedValue(body);
}

/** Route `apiFetch` responses by a substring of the requested path. */
export function stubFetchByPath(routes: Record<string, unknown>): void {
  (
    apiFetch as unknown as {
      mockImplementation: (impl: (path: string) => Promise<unknown>) => void;
    }
  ).mockImplementation((path: string) => {
    const match = Object.entries(routes).find(([key]) => path.includes(key));
    if (!match) throw new Error(`No stub for ${path}`);
    return Promise.resolve(match[1]);
  });
}
