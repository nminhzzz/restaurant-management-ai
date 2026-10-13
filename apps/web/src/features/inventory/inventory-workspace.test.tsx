import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { InventoryWorkspace } from "./inventory-workspace";

function signIn(role: string) {
  sessionStorage.setItem(
    "session",
    JSON.stringify({ token: "t", role, username: "u" }),
  );
}

describe("InventoryWorkspace dish write-off tab", () => {
  beforeEach(() => {
    (apiFetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      items: [],
      total: 0,
    });
  });
  afterEach(() => {
    sessionStorage.clear();
    vi.resetAllMocks();
  });

  it.each(["MANAGER", "WAREHOUSE"])("is visible to %s", (role) => {
    signIn(role);
    render(<InventoryWorkspace />);
    expect(screen.getByRole("tab", { name: "Hủy món" })).toBeInTheDocument();
  });

  it("is hidden from other roles and signed-out sessions", () => {
    signIn("CASHIER");
    const { unmount } = render(<InventoryWorkspace />);
    expect(screen.queryByRole("tab", { name: "Hủy món" })).toBeNull();
    unmount();

    sessionStorage.clear();
    render(<InventoryWorkspace />);
    expect(screen.queryByRole("tab", { name: "Hủy món" })).toBeNull();
  });
});
