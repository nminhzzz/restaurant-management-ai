import { afterEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "./api-client";
import { loadSession, saveSession } from "./session";

const original = { token: "old", role: "CASHIER", username: "cashier" };
const unauthorized = () =>
  new Response(
    JSON.stringify({ error: { code: "UNAUTHENTICATED", message: "expired" } }),
    { status: 401 },
  );

afterEach(() => {
  sessionStorage.clear();
  localStorage.clear();
  vi.unstubAllGlobals();
});

describe("session expiry at the API boundary", () => {
  it("ends the current session when its token is rejected", async () => {
    saveSession(original);
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(unauthorized()));
    await expect(apiFetch("/sales/floor")).rejects.toMatchObject({
      status: 401,
    });
    expect(loadSession()).toBeNull();
  });

  it("does not end a newer session when an old request returns late", async () => {
    saveSession(original);
    let finish!: (value: Response) => void;
    vi.stubGlobal(
      "fetch",
      () =>
        new Promise<Response>((resolve) => {
          finish = resolve;
        }),
    );
    const pending = apiFetch("/sales/floor");
    saveSession({ ...original, token: "new" });
    finish(unauthorized());
    await expect(pending).rejects.toMatchObject({ status: 401 });
    expect(loadSession()?.token).toBe("new");
  });

  it("preserves a session when a role guard returns forbidden", async () => {
    saveSession(original);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("{}", { status: 403 })),
    );
    await expect(apiFetch("/reports/revenue")).rejects.toMatchObject({
      status: 403,
    });
    expect(loadSession()?.token).toBe("old");
  });
});
