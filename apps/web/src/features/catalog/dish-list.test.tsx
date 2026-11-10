import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { clearSession, saveSession } from "@/lib/session";
import { DishList } from "./dish-list";
import { PriceScheduler } from "./price-scheduler";

const mockFetch = apiFetch as unknown as ReturnType<typeof vi.fn>;

const COSTS = "/catalog/dishes/costs";

function stubFetch(data: unknown) {
  mockFetch.mockImplementation((path: string) =>
    Promise.resolve(path === COSTS ? { items: [] } : data),
  );
}

describe("catalog screens", () => {
  beforeEach(() => {
    mockFetch.mockReset();
    saveSession({ token: "t", role: "MANAGER", username: "quanly" });
  });

  afterEach(() => clearSession());

  it("shows the four display states of the screen", async () => {
    let resolve!: (v: unknown) => void;
    const pending = new Promise((r) => (resolve = r));
    mockFetch.mockImplementation((path: string) =>
      path === COSTS ? Promise.resolve({ items: [] }) : pending,
    );
    render(<DishList />);
    expect(screen.getByText("Đang tải…")).toBeInTheDocument();
    resolve({
      items: [{ MaMon: 1, TenMon: "Phở bò", TrangThai: "Hoạt động" }],
    });
    expect(await screen.findByText("Phở bò")).toBeInTheDocument();
  });

  it("shows an empty state with a next step when there are no dishes", async () => {
    stubFetch({ items: [], total: 0 });
    render(<DishList />);
    expect(await screen.findByText(/Chưa có món nào/)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Thêm món" }),
    ).toBeInTheDocument();
  });

  it("rejects a scheduled date in the past before calling the API", async () => {
    render(<PriceScheduler dishId={1} />);
    fireEvent.change(screen.getByLabelText("Business Date áp dụng"), {
      target: { value: "2020-01-01" },
    });
    expect(
      screen.getByText(/phải là một Business Date trong tương lai/),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Lưu" })).toBeDisabled();
  });

  it("creates a dish with the form's values", async () => {
    mockFetch.mockImplementation((path: string) => {
      if (path === COSTS) return Promise.resolve({ items: [] });
      if (path.startsWith("/catalog/dishes")) {
        return Promise.resolve({
          items: [{ MaMon: 1, TenMon: "Phở bò", TrangThai: "Hoạt động" }],
        });
      }
      if (path.startsWith("/catalog/groups")) {
        return Promise.resolve([{ MaNhomMon: 5, TenNhom: "Món chính" }]);
      }
      return Promise.resolve({});
    });
    render(<DishList />);

    fireEvent.click(await screen.findByRole("button", { name: "Thêm món" }));
    fireEvent.change(screen.getByLabelText("Tên món"), {
      target: { value: "Bún chả" },
    });
    fireEvent.change(screen.getByLabelText("Nhóm món"), {
      target: { value: "5" },
    });
    fireEvent.change(screen.getByLabelText("Giá bán"), {
      target: { value: "45000" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Lưu" }));

    await waitFor(() =>
      expect(mockFetch).toHaveBeenCalledWith(
        "/catalog/dishes",
        expect.objectContaining({
          method: "POST",
          body: { TenMon: "Bún chả", MaNhomMon: 5, GiaHienTai: 45000 },
        }),
      ),
    );
  });

  it("requires confirmation before deleting a dish", async () => {
    mockFetch.mockImplementation((path: string) => {
      if (path === COSTS) return Promise.resolve({ items: [] });
      if (path.startsWith("/catalog/dishes")) {
        return Promise.resolve({
          items: [{ MaMon: 1, TenMon: "Phở bò", TrangThai: "Hoạt động" }],
        });
      }
      return Promise.resolve([]);
    });
    render(<DishList />);

    fireEvent.click(await screen.findByRole("button", { name: "Xóa món" }));
    expect(
      mockFetch.mock.calls.some(([, opts]) => opts?.method === "DELETE"),
    ).toBe(false);

    fireEvent.click(screen.getByRole("button", { name: "Xóa" }));
    await waitFor(() =>
      expect(mockFetch).toHaveBeenCalledWith(
        "/catalog/dishes/1",
        expect.objectContaining({ method: "DELETE" }),
      ),
    );
  });

  it("sends HinhAnh when creating a dish with an image URL", async () => {
    mockFetch.mockImplementation((path: string) => {
      if (path === COSTS) return Promise.resolve({ items: [] });
      if (path.startsWith("/catalog/dishes")) {
        return Promise.resolve({
          items: [{ MaMon: 1, TenMon: "Phở bò", TrangThai: "Hoạt động" }],
        });
      }
      if (path.startsWith("/catalog/groups")) {
        return Promise.resolve([{ MaNhomMon: 5, TenNhom: "Món chính" }]);
      }
      return Promise.resolve({});
    });
    render(<DishList />);

    fireEvent.click(await screen.findByRole("button", { name: "Thêm món" }));
    fireEvent.change(screen.getByLabelText("Tên món"), {
      target: { value: "Bún chả" },
    });
    fireEvent.change(screen.getByLabelText("Nhóm món"), {
      target: { value: "5" },
    });
    fireEvent.change(screen.getByLabelText("Giá bán"), {
      target: { value: "45000" },
    });
    fireEvent.change(screen.getByLabelText("Ảnh món (URL)"), {
      target: { value: "https://example.com/bun-cha.jpg" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Lưu" }));

    await waitFor(() =>
      expect(mockFetch).toHaveBeenCalledWith(
        "/catalog/dishes",
        expect.objectContaining({
          method: "POST",
          body: {
            TenMon: "Bún chả",
            MaNhomMon: 5,
            GiaHienTai: 45000,
            HinhAnh: "https://example.com/bun-cha.jpg",
          },
        }),
      ),
    );
  });

  it("narrows rows by search and pages through the rest", async () => {
    const dishes = Array.from({ length: 25 }, (_, i) => ({
      MaMon: i + 1,
      TenMon: `Món ${i + 1}`,
      TrangThai: "Hoạt động",
    }));
    mockFetch.mockImplementation((path: string) => {
      if (path === COSTS) return Promise.resolve({ items: [] });
      if (path.startsWith("/catalog/dishes")) {
        return Promise.resolve({ items: dishes });
      }
      return Promise.resolve([]);
    });
    render(<DishList />);

    await screen.findByText("Món 1");
    expect(screen.getByText("Hiển thị 1–20 trên 25")).toBeInTheDocument();
    expect(screen.queryByText("Món 21")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Trang 2" }));
    expect(await screen.findByText("Món 21")).toBeInTheDocument();
    expect(screen.queryByText("Món 1")).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Tìm món"), {
      target: { value: "Món 1" },
    });
    expect(screen.getByText("Hiển thị 1–11 trên 11")).toBeInTheDocument();
    expect(screen.getByText("Món 1")).toBeInTheDocument();
    expect(screen.queryByText("Món 2")).not.toBeInTheDocument();
  });

  it("shows an empty-result row and clears filters on reset", async () => {
    mockFetch.mockImplementation((path: string) => {
      if (path === COSTS) return Promise.resolve({ items: [] });
      if (path.startsWith("/catalog/dishes")) {
        return Promise.resolve({
          items: [{ MaMon: 1, TenMon: "Phở bò", TrangThai: "Hoạt động" }],
        });
      }
      return Promise.resolve([]);
    });
    render(<DishList />);

    await screen.findByText("Phở bò");
    fireEvent.change(screen.getByLabelText("Tìm món"), {
      target: { value: "không tồn tại" },
    });
    expect(
      screen.getByText("Không có món nào khớp bộ lọc."),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Xóa bộ lọc" }));
    expect(await screen.findByText("Phở bò")).toBeInTheDocument();
  });

  it("shows the manager cost, cost ratio, margin and the over-threshold warning", async () => {
    mockFetch.mockImplementation((path: string) => {
      if (path === COSTS) {
        return Promise.resolve({
          items: [
            {
              MaMon: 1,
              TinhTrang: "Đủ dữ liệu",
              GiaBan: 80000,
              GiaVonUocTinh: 36500,
              TyLeGiaVon: 45.63,
              LaiGop: 43500,
              CanhBao: true,
              NguongCanhBao: 40,
              NguyenLieuThieuGia: [],
            },
            {
              MaMon: 2,
              TinhTrang: "Chưa đủ dữ liệu",
              GiaBan: 65000,
              GiaVonUocTinh: null,
              TyLeGiaVon: null,
              LaiGop: null,
              CanhBao: false,
              NguongCanhBao: 40,
              NguyenLieuThieuGia: ["Sả"],
            },
            {
              MaMon: 3,
              TinhTrang: "Chưa có công thức",
              GiaBan: 50000,
              GiaVonUocTinh: null,
              TyLeGiaVon: null,
              LaiGop: null,
              CanhBao: false,
              NguongCanhBao: 40,
              NguyenLieuThieuGia: [],
            },
          ],
        });
      }
      if (path.startsWith("/catalog/dishes")) {
        return Promise.resolve({
          items: [
            {
              MaMon: 1,
              TenMon: "Bò xào",
              TrangThai: "Hoạt động",
              GiaHienTai: 80000,
            },
            {
              MaMon: 2,
              TenMon: "Gỏi gà",
              TrangThai: "Hoạt động",
              GiaHienTai: 65000,
            },
            {
              MaMon: 3,
              TenMon: "Món mới",
              TrangThai: "Nháp",
              GiaHienTai: 50000,
            },
          ],
        });
      }
      return Promise.resolve([]);
    });

    render(<DishList />);

    const beef = (await screen.findByText("Bò xào")).closest("tr")!;
    await waitFor(() => expect(beef).toHaveTextContent("36.500 ₫"));
    expect(
      screen.getByRole("columnheader", { name: "Giá vốn ước tính" }),
    ).toBeInTheDocument();
    expect(beef).toHaveTextContent("45,6%");
    expect(beef).toHaveTextContent("43.500 ₫");
    expect(beef).toHaveTextContent("Vượt 40,0%");
    const chicken = screen.getByText("Gỏi gà").closest("tr")!;
    expect(chicken).toHaveTextContent("Chưa đủ dữ liệu: Sả");
    expect(chicken).not.toHaveTextContent("%");
    expect(chicken).not.toHaveTextContent("Vượt");
    expect(screen.getByText("Món mới").closest("tr")).toHaveTextContent(
      "Chưa có công thức",
    );
  });

  it("neither requests nor shows cost figures for a role other than the manager", async () => {
    clearSession();
    saveSession({ token: "t", role: "CASHIER", username: "thungan" });
    stubFetch({
      items: [{ MaMon: 1, TenMon: "Bò xào", TrangThai: "Hoạt động" }],
    });

    render(<DishList />);
    await screen.findByText("Bò xào");

    expect(
      screen.queryByRole("columnheader", { name: "Giá vốn ước tính" }),
    ).not.toBeInTheDocument();
    expect(mockFetch.mock.calls.some(([path]) => path === COSTS)).toBe(false);
  });

  it("hides write actions on the dishes tab for the warehouse role", async () => {
    saveSession({ token: "t", role: "WAREHOUSE", username: "thukho" });
    mockFetch.mockImplementation((path: string) => {
      if (path === COSTS) return Promise.resolve({ items: [] });
      if (path.startsWith("/catalog/dishes")) {
        return Promise.resolve({
          items: [{ MaMon: 1, TenMon: "Phở bò", TrangThai: "Hoạt động" }],
        });
      }
      return Promise.resolve([]);
    });
    render(<DishList />);

    await screen.findByText("Phở bò");
    expect(
      screen.queryByRole("button", { name: "Thêm món" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Sửa món" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Xóa món" }),
    ).not.toBeInTheDocument();
  });
});
