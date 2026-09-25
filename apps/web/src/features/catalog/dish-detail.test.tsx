import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { clearSession, saveSession } from "@/lib/session";
import { DishDetail } from "./dish-detail";
import type { Dish } from "./types";

const mockFetch = apiFetch as unknown as ReturnType<typeof vi.fn>;

const dish: Dish = {
  MaMon: 1,
  TenMon: "Phở bò",
  TrangThai: "Hoạt động",
  MaNhomMon: 5,
  GiaHienTai: null,
};

function stubRoutes(overrides: Record<string, unknown> = {}) {
  mockFetch.mockImplementation((path: string) => {
    if (path.startsWith("/catalog/dishes/1/prices")) {
      return Promise.resolve(overrides.prices ?? []);
    }
    if (path.startsWith("/catalog/dishes/1/recipes")) {
      return Promise.resolve(overrides.recipes ?? []);
    }
    if (path.startsWith("/catalog/ingredients")) {
      return Promise.resolve({ items: [] });
    }
    return Promise.resolve({});
  });
}

describe("DishDetail", () => {
  beforeEach(() => {
    mockFetch.mockReset();
    saveSession({ token: "t", role: "MANAGER", username: "quanly" });
  });

  afterEach(() => clearSession());

  it("shows a pending price change loaded from the API and lets the user cancel it", async () => {
    stubRoutes({
      prices: [
        {
          MaLichSuGia: 42,
          MaMon: 1,
          Gia: 60000,
          BusinessDateApDung: "2026-09-26",
          TrangThai: "Nháp",
          LoaiThayDoi: "Tạo mới",
        },
      ],
    });

    render(
      <DishDetail dish={dish} onOpenChange={vi.fn()} onChanged={vi.fn()} />,
    );

    expect(await screen.findByText(/Đang chờ áp dụng/)).toBeInTheDocument();
    expect(screen.getByText(/60.000/)).toBeInTheDocument();
    expect(screen.getByText(/26\/09\/2026/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Hủy lịch" }));
    const dialogConfirm = screen
      .getAllByRole("button", { name: "Hủy lịch" })
      .at(-1);
    if (!dialogConfirm) throw new Error("confirm button not found");
    fireEvent.click(dialogConfirm);

    await waitFor(() =>
      expect(mockFetch).toHaveBeenCalledWith(
        "/catalog/prices/42",
        expect.objectContaining({ method: "DELETE" }),
      ),
    );
  });

  it("shows the current recipe lines from the API", async () => {
    stubRoutes({
      recipes: [
        {
          MaCongThuc: 7,
          MaMon: 1,
          BusinessDateApDung: "2026-09-20",
          TrangThai: "Hiệu lực",
          LoaiThayDoi: "Tạo mới",
          items: [
            {
              MaNguyenLieu: 1,
              TenNguyenLieu: "Bột mì",
              SoLuong: 0.2,
              DonViTinh: "kg",
            },
          ],
        },
      ],
    });

    render(
      <DishDetail dish={dish} onOpenChange={vi.fn()} onChanged={vi.fn()} />,
    );

    expect(await screen.findByText("Công thức hiện tại")).toBeInTheDocument();
    expect(screen.getByText(/Bột mì \(0\.2 kg\)/)).toBeInTheDocument();
  });
});
