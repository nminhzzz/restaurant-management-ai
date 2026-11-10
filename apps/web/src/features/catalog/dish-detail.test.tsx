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
    if (path === "/catalog/dishes/1/cost") {
      return Promise.resolve(overrides.cost ?? noRecipe);
    }
    if (path.startsWith("/catalog/ingredients")) {
      return Promise.resolve({ items: [] });
    }
    return Promise.resolve({});
  });
}

const noRecipe = {
  MaMon: 1,
  TinhTrang: "Chưa có công thức",
  GiaBan: null,
  GiaVonUocTinh: null,
  TyLeGiaVon: null,
  LaiGop: null,
  CanhBao: false,
  NguongCanhBao: 40,
  NguyenLieuThieuGia: [],
  ChiTiet: [],
};

const beefStirFry = {
  MaMon: 1,
  TinhTrang: "Đủ dữ liệu",
  GiaBan: 80000,
  GiaVonUocTinh: 36500,
  TyLeGiaVon: 45.63,
  LaiGop: 43500,
  CanhBao: true,
  NguongCanhBao: 40,
  NguyenLieuThieuGia: [],
  ChiTiet: [
    {
      MaNguyenLieu: 1,
      TenNguyenLieu: "Bò",
      DonViTinh: "kg",
      DinhLuong: 0.15,
      DonGiaBinhQuan: 230000,
      ThanhTien: 34500,
    },
    {
      MaNguyenLieu: 2,
      TenNguyenLieu: "Hành",
      DonViTinh: "kg",
      DinhLuong: 0.05,
      DonGiaBinhQuan: 40000,
      ThanhTien: 2000,
    },
  ],
};

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
          TrangThai: "Chờ áp dụng",
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
          TrangThai: "Đang áp dụng",
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

  it("breaks the estimated cost down by ingredient and flags a ratio over the threshold", async () => {
    stubRoutes({ cost: beefStirFry });

    render(
      <DishDetail dish={dish} onOpenChange={vi.fn()} onChanged={vi.fn()} />,
    );

    expect(
      await screen.findByRole("row", {
        name: /Bò 0,15 kg 230\.000 ₫ 34\.500 ₫/,
      }),
    ).toBeVisible();
    expect(
      screen.getByRole("row", { name: /Hành 0,05 kg 40\.000 ₫ 2\.000 ₫/ }),
    ).toBeVisible();
    const summary = screen.getByText(/Giá vốn ước tính/, { selector: "p" });
    expect(summary).toHaveTextContent("36.500 ₫");
    expect(summary).toHaveTextContent("45,6%");
    expect(summary).toHaveTextContent("43.500 ₫");
    expect(summary).toHaveTextContent("vượt ngưỡng 40,0%");
  });

  it("names the ingredient without a unit cost instead of counting it as zero", async () => {
    stubRoutes({
      cost: {
        ...beefStirFry,
        TinhTrang: "Chưa đủ dữ liệu",
        GiaVonUocTinh: null,
        TyLeGiaVon: null,
        LaiGop: null,
        CanhBao: false,
        NguyenLieuThieuGia: ["Hành"],
        ChiTiet: [
          beefStirFry.ChiTiet[0],
          { ...beefStirFry.ChiTiet[1], DonGiaBinhQuan: null, ThanhTien: null },
        ],
      },
    });

    render(
      <DishDetail dish={dish} onOpenChange={vi.fn()} onChanged={vi.fn()} />,
    );

    expect(
      await screen.findByRole("row", {
        name: /Hành 0,05 kg Chưa xác định Chưa xác định/,
      }),
    ).toBeVisible();
    expect(screen.getByText(/Chưa đủ dữ liệu: Hành/)).toBeVisible();
    expect(screen.queryByText(/tỷ lệ giá vốn/)).not.toBeInTheDocument();
  });

  it("shows the cost ratio of the price being typed before it is saved", async () => {
    stubRoutes({ cost: beefStirFry });

    render(
      <DishDetail dish={dish} onOpenChange={vi.fn()} onChanged={vi.fn()} />,
    );
    await screen.findByRole("row", { name: /Bò 0,15 kg/ });

    fireEvent.change(screen.getByLabelText("Giá mới"), {
      target: { value: "100000" },
    });
    expect(
      screen.getByText(/tỷ lệ giá vốn 36,5%$/, { selector: "p" }),
    ).toBeVisible();

    fireEvent.change(screen.getByLabelText("Áp dụng giá ngay"), {
      target: { value: "73000" },
    });
    expect(
      screen.getByText(/tỷ lệ giá vốn 50,0% · vượt ngưỡng 40,0%/),
    ).toBeVisible();
    expect(
      mockFetch.mock.calls.some(([, options]) => options?.method === "POST"),
    ).toBe(false);
  });

  it("does not request the cost estimate for a role other than the manager", async () => {
    clearSession();
    saveSession({ token: "t", role: "CASHIER", username: "thungan" });
    stubRoutes({ cost: beefStirFry });

    render(
      <DishDetail dish={dish} onOpenChange={vi.fn()} onChanged={vi.fn()} />,
    );
    await screen.findByText("Giá bán");

    expect(screen.queryByText("Giá vốn ước tính")).not.toBeInTheDocument();
    expect(
      mockFetch.mock.calls.some(([path]) => path === "/catalog/dishes/1/cost"),
    ).toBe(false);
  });
});
