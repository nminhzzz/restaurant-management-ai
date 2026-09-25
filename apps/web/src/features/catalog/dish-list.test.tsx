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

function stubFetch(data: unknown) {
  mockFetch.mockResolvedValue(data);
}

describe("catalog screens", () => {
  beforeEach(() => {
    mockFetch.mockReset();
    saveSession({ token: "t", role: "MANAGER", username: "quanly" });
  });

  afterEach(() => clearSession());

  it("shows the four display states of the screen", async () => {
    let resolve!: (v: unknown) => void;
    mockFetch.mockReturnValue(new Promise((r) => (resolve = r)));
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

  it("hides write actions on the dishes tab for the warehouse role", async () => {
    saveSession({ token: "t", role: "WAREHOUSE", username: "thukho" });
    mockFetch.mockImplementation((path: string) => {
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
