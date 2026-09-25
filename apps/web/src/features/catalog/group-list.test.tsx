import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { ApiError, apiFetch } from "@/lib/api-client";
import { clearSession, saveSession } from "@/lib/session";
import { GroupList } from "./group-list";

const mockFetch = apiFetch as unknown as ReturnType<typeof vi.fn>;

describe("GroupList", () => {
  beforeEach(() => {
    mockFetch.mockReset();
    saveSession({ token: "t", role: "MANAGER", username: "quanly" });
  });

  afterEach(() => clearSession());

  it("surfaces the API's message inline when a delete is rejected", async () => {
    mockFetch.mockImplementation((path: string, opts?: { method?: string }) => {
      if (path === "/catalog/groups" && (!opts || opts.method === undefined)) {
        return Promise.resolve([{ MaNhomMon: 1, TenNhom: "Khai vị" }]);
      }
      if (opts?.method === "DELETE") {
        return Promise.reject(
          new ApiError(409, "GROUP_IN_USE", "Nhóm đang có món, không thể xóa."),
        );
      }
      return Promise.resolve([]);
    });
    render(<GroupList />);

    fireEvent.click(await screen.findByRole("button", { name: "Xóa nhóm" }));
    fireEvent.click(screen.getByRole("button", { name: "Xóa" }));

    expect(
      await screen.findByText("Nhóm đang có món, không thể xóa."),
    ).toBeInTheDocument();
  });
});
