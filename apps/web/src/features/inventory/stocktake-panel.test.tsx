import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { StocktakePanel } from "./stocktake-panel";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

const stockItems = [
  { MaNguyenLieu: 1, TenNguyenLieu: "Gạo", SoLuongTon: 10 },
  { MaNguyenLieu: 2, TenNguyenLieu: "Muối", SoLuongTon: 5 },
];

function route() {
  fetchMock.mockImplementation(
    (path: string, options: { method?: string } = {}) => {
      const method = options.method ?? "GET";
      if (path === "/inventory/stocktakes" && method === "POST") {
        return Promise.resolve({ MaPhieuKiemKe: 1 });
      }
      if (path === "/inventory/stocktakes/1/counts") {
        return Promise.resolve({ ok: true });
      }
      if (path === "/inventory/stocktakes/1/confirm") {
        return Promise.resolve({ ok: true });
      }
      if (path.startsWith("/inventory/stocktakes")) {
        return Promise.resolve({ items: [], total: 0 });
      }
      if (path.startsWith("/inventory/stock")) {
        return Promise.resolve({ items: stockItems });
      }
      return Promise.resolve({});
    },
  );
}

describe("StocktakePanel", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    route();
  });

  it("keeps the confirm button disabled until every ingredient has a count", async () => {
    render(<StocktakePanel />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Tạo phiếu kiểm kê" }),
    );

    const confirmButton = await screen.findByRole("button", {
      name: "Xác nhận kiểm kê",
    });
    expect(confirmButton).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Tồn thực tế Gạo"), {
      target: { value: "9" },
    });
    expect(confirmButton).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Tồn thực tế Muối"), {
      target: { value: "4" },
    });
    expect(confirmButton).toBeEnabled();
  });

  it("records counts then confirms when every row is filled", async () => {
    render(<StocktakePanel />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Tạo phiếu kiểm kê" }),
    );
    fireEvent.change(await screen.findByLabelText("Tồn thực tế Gạo"), {
      target: { value: "9" },
    });
    fireEvent.change(screen.getByLabelText("Tồn thực tế Muối"), {
      target: { value: "4" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận kiểm kê" }));

    await screen.findByRole("button", { name: "Tạo phiếu kiểm kê" });
    expect(fetchMock).toHaveBeenCalledWith(
      "/inventory/stocktakes/1/counts",
      expect.objectContaining({
        method: "POST",
        body: [
          { ingredient_id: 1, actual_qty: 9 },
          { ingredient_id: 2, actual_qty: 4 },
        ],
      }),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "/inventory/stocktakes/1/confirm",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("requests history page 1 with the default page size and shows the real total", async () => {
    fetchMock.mockImplementation(
      (path: string, options: { method?: string } = {}) => {
        if (
          path === "/inventory/stocktakes" &&
          (options.method ?? "GET") === "POST"
        ) {
          return Promise.resolve({ MaPhieuKiemKe: 1 });
        }
        if (path.startsWith("/inventory/stocktakes")) {
          return Promise.resolve({
            items: [{ MaPhieuKiemKe: 5, TrangThai: "Đã xác nhận" }],
            total: 26,
          });
        }
        if (path.startsWith("/inventory/stock")) {
          return Promise.resolve({ items: stockItems });
        }
        return Promise.resolve({});
      },
    );

    render(<StocktakePanel />);
    await screen.findByText("#5");

    expect(fetchMock).toHaveBeenCalledWith(
      "/inventory/stocktakes?page=1&page_size=20",
    );
    expect(screen.getByText("Hiển thị 1–20 trên 26")).toBeInTheDocument();
  });

  it("sends the status and date range filters and resets history paging to page 1", async () => {
    fetchMock.mockImplementation(
      (path: string, options: { method?: string } = {}) => {
        if (
          path === "/inventory/stocktakes" &&
          (options.method ?? "GET") === "POST"
        ) {
          return Promise.resolve({ MaPhieuKiemKe: 1 });
        }
        if (path.startsWith("/inventory/stocktakes")) {
          return Promise.resolve({
            items: [{ MaPhieuKiemKe: 5, TrangThai: "Đã xác nhận" }],
            total: 26,
          });
        }
        if (path.startsWith("/inventory/stock")) {
          return Promise.resolve({ items: stockItems });
        }
        return Promise.resolve({});
      },
    );

    render(<StocktakePanel />);
    await screen.findByText("#5");

    fireEvent.click(screen.getByRole("button", { name: "Trang 2" }));
    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenLastCalledWith(
        "/inventory/stocktakes?page=2&page_size=20",
      ),
    );

    fireEvent.change(screen.getByLabelText("Trạng thái"), {
      target: { value: "Đã xác nhận" },
    });
    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenLastCalledWith(
        "/inventory/stocktakes?status=%C4%90%C3%A3+x%C3%A1c+nh%E1%BA%ADn&page=1&page_size=20",
      ),
    );

    fireEvent.change(screen.getByLabelText("Từ ngày"), {
      target: { value: "2026-09-01" },
    });
    fireEvent.change(screen.getByLabelText("Đến ngày"), {
      target: { value: "2026-09-25" },
    });
    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenLastCalledWith(
        "/inventory/stocktakes?status=%C4%90%C3%A3+x%C3%A1c+nh%E1%BA%ADn&date_from=2026-09-01&date_to=2026-09-25&page=1&page_size=20",
      ),
    );
  });
});
