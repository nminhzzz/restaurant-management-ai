import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { clearSession, saveSession } from "@/lib/session";
import { TableList } from "./table-list";

const mockFetch = apiFetch as unknown as ReturnType<typeof vi.fn>;

describe("TableList", () => {
  beforeEach(() => {
    mockFetch.mockReset();
    saveSession({ token: "t", role: "MANAGER", username: "quanly" });
  });

  afterEach(() => clearSession());

  it("narrows tables by status and clears the filter on reset", async () => {
    mockFetch.mockResolvedValue([
      { MaBan: 1, TenBan: "Bàn 1", TrangThai: "Trống" },
      { MaBan: 2, TenBan: "Bàn 2", TrangThai: "Đang phục vụ" },
    ]);
    render(<TableList />);

    await screen.findByText("Bàn 1");
    expect(screen.getByText("Bàn 2")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Trạng thái"), {
      target: { value: "Trống" },
    });
    expect(screen.getByText("Bàn 1")).toBeInTheDocument();
    expect(screen.queryByText("Bàn 2")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Xóa bộ lọc" }));
    expect(await screen.findByText("Bàn 2")).toBeInTheDocument();
  });

  it("releases an occupied table for a cashier but gives no edit or delete", async () => {
    saveSession({ token: "t", role: "CASHIER", username: "thungan" });
    mockFetch.mockImplementation((path: string) =>
      Promise.resolve(
        path === "/catalog/tables"
          ? [
              {
                MaBan: 2,
                TenBan: "Bàn 2",
                TrangThai: "Đang phục vụ",
                SoChoNgoi: 4,
                MaOrderDangPhucVu: 55,
              },
            ]
          : {},
      ),
    );
    render(<TableList />);

    expect(await screen.findByText("4 chỗ ngồi")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Xóa bàn/ })).toBeNull();
    expect(screen.queryByRole("button", { name: /Sửa bàn/ })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Trả bàn Bàn 2" }));

    await vi.waitFor(() =>
      expect(mockFetch).toHaveBeenCalledWith(
        "/catalog/tables/2/release",
        expect.objectContaining({ method: "POST", body: { MaOrder: 55 } }),
      ),
    );
  });

  it("shows no release action on a free table", async () => {
    mockFetch.mockResolvedValue([
      { MaBan: 1, TenBan: "Bàn 1", TrangThai: "Trống" },
    ]);
    render(<TableList />);

    await screen.findByText("Bàn 1");
    expect(screen.queryByRole("button", { name: /Trả bàn/ })).toBeNull();
  });

  it("edits a table's name and seats with PATCH", async () => {
    mockFetch.mockImplementation((path: string) =>
      Promise.resolve(
        path === "/catalog/tables"
          ? [{ MaBan: 1, TenBan: "Bàn 1", TrangThai: "Trống", SoChoNgoi: 2 }]
          : {},
      ),
    );
    render(<TableList />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Sửa bàn Bàn 1" }),
    );
    fireEvent.change(screen.getByLabelText("Số chỗ ngồi"), {
      target: { value: "6" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Lưu" }));

    await vi.waitFor(() =>
      expect(mockFetch).toHaveBeenCalledWith(
        "/catalog/tables/1",
        expect.objectContaining({
          method: "PATCH",
          body: { TenBan: "Bàn 1", SoChoNgoi: 6 },
        }),
      ),
    );
  });

  it("rejects an out-of-range seat count before calling the API", async () => {
    mockFetch.mockResolvedValue([
      { MaBan: 1, TenBan: "Bàn 1", TrangThai: "Trống" },
    ]);
    render(<TableList />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Sửa bàn Bàn 1" }),
    );
    fireEvent.change(screen.getByLabelText("Số chỗ ngồi"), {
      target: { value: "0" },
    });

    expect(
      screen.getByText("Nhập số nguyên từ 1 đến 1000."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Lưu" })).toBeDisabled();
  });
});
