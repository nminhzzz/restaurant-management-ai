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

  it("narrows rows by search, pages through the rest, and resets to page 1 on a new filter", async () => {
    const groups = Array.from({ length: 25 }, (_, i) => ({
      MaNhomMon: i + 1,
      TenNhom: `Nhóm ${i + 1}`,
    }));
    mockFetch.mockImplementation((path: string, opts?: { method?: string }) => {
      if (path === "/catalog/groups" && (!opts || opts.method === undefined)) {
        return Promise.resolve(groups);
      }
      return Promise.resolve([]);
    });
    render(<GroupList />);

    await screen.findByText("Nhóm 1");
    expect(screen.getByText("Hiển thị 1–20 trên 25")).toBeInTheDocument();
    expect(screen.queryByText("Nhóm 21")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Trang 2" }));
    expect(await screen.findByText("Nhóm 21")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Tìm nhóm"), {
      target: { value: "Nhóm 1" },
    });
    expect(screen.getByText("Hiển thị 1–11 trên 11")).toBeInTheDocument();
    expect(screen.getByText("Nhóm 1")).toBeInTheDocument();
    expect(screen.queryByText("Nhóm 2")).not.toBeInTheDocument();
  });

  it("sends the new order as the object the API expects when a group moves up", async () => {
    mockFetch.mockImplementation((path: string, opts?: { method?: string }) => {
      if (path === "/catalog/groups" && (!opts || opts.method === undefined)) {
        return Promise.resolve([
          { MaNhomMon: 1, TenNhom: "A" },
          { MaNhomMon: 2, TenNhom: "B" },
          { MaNhomMon: 3, TenNhom: "C" },
        ]);
      }
      return Promise.resolve([]);
    });
    render(<GroupList />);
    await screen.findByText("C");

    const up = screen.getAllByRole("button", { name: "Di chuyển lên" });
    fireEvent.click(up[up.length - 1]);

    await vi.waitFor(() =>
      expect(mockFetch).toHaveBeenCalledWith("/catalog/groups/order", {
        method: "PUT",
        body: { MaNhomMon: [1, 3, 2] },
      }),
    );
  });

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
