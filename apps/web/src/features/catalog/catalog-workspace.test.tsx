import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn().mockResolvedValue({ items: [] }) };
});
import { clearSession, saveSession } from "@/lib/session";
import { CatalogWorkspace } from "./catalog-workspace";

function tabNames(): string[] {
  return screen.getAllByRole("tab").map((tab) => tab.textContent ?? "");
}

describe("CatalogWorkspace (report Bảng 33)", () => {
  beforeEach(() => clearSession());
  afterEach(cleanup);

  it("gives the manager every catalogue tab", () => {
    saveSession({ token: "t", role: "MANAGER", username: "quanly" });
    render(<CatalogWorkspace />);

    expect(tabNames()).toEqual([
      "Món ăn",
      "Nhóm món",
      "Nguyên liệu",
      "Nhà cung cấp",
      "Bàn",
    ]);
  });

  it("lets the cashier read dishes and table status only", () => {
    saveSession({ token: "t", role: "CASHIER", username: "thungan" });
    render(<CatalogWorkspace />);

    expect(tabNames()).toEqual(["Món ăn", "Nhóm món", "Bàn"]);
  });

  it("limits the warehouse to ingredients and suppliers", () => {
    saveSession({ token: "t", role: "WAREHOUSE", username: "kho" });
    render(<CatalogWorkspace />);

    expect(tabNames()).toEqual(["Nguyên liệu", "Nhà cung cấp"]);
  });
});
