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

const previewItems = [
  {
    MaNguyenLieu: 1,
    TenNguyenLieu: "Gạo",
    TonTruocDieuChinh: 10,
    TonSauDieuChinh: 9,
    ChenhLech: -1,
    LyDoChenhLech: "Rơi vỡ",
  },
  {
    MaNguyenLieu: 2,
    TenNguyenLieu: "Muối",
    TonTruocDieuChinh: 5,
    TonSauDieuChinh: 4,
    ChenhLech: -1,
    LyDoChenhLech: "Hao hụt",
  },
];

async function fillCounts() {
  fireEvent.change(await screen.findByLabelText("Tồn thực tế Gạo"), {
    target: { value: "9" },
  });
  fireEvent.change(screen.getByLabelText("Tồn thực tế Muối"), {
    target: { value: "4" },
  });
  fireEvent.change(screen.getByLabelText("Lý do chênh lệch Gạo"), {
    target: { value: "Rơi vỡ" },
  });
  fireEvent.change(screen.getByLabelText("Lý do chênh lệch Muối"), {
    target: { value: "Hao hụt" },
  });
}

function wrote(path: string) {
  return fetchMock.mock.calls.some(([called]) => called === path);
}

function route() {
  fetchMock.mockImplementation(
    (path: string, options: { method?: string } = {}) => {
      const method = options.method ?? "GET";
      if (path === "/inventory/stocktakes" && method === "POST") {
        return Promise.resolve({ MaPhieuKiemKe: 1 });
      }
      if (path === "/inventory/stocktakes/1/preview") {
        return Promise.resolve({ items: previewItems });
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

  it("keeps the preview button disabled until every ingredient has a count", async () => {
    render(<StocktakePanel />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Tạo phiếu kiểm kê" }),
    );

    const confirmButton = await screen.findByRole("button", {
      name: "Xem trước",
    });
    expect(confirmButton).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Tồn thực tế Gạo"), {
      target: { value: "9" },
    });
    expect(confirmButton).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Tồn thực tế Muối"), {
      target: { value: "4" },
    });
    expect(confirmButton).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Lý do chênh lệch Gạo"), {
      target: { value: "Rơi vỡ" },
    });
    fireEvent.change(screen.getByLabelText("Lý do chênh lệch Muối"), {
      target: { value: "Hao hụt" },
    });
    expect(confirmButton).toBeEnabled();
  });

  it("shows stock before and after and writes nothing until the preview is confirmed", async () => {
    render(<StocktakePanel />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Tạo phiếu kiểm kê" }),
    );
    await fillCounts();
    fireEvent.click(screen.getByRole("button", { name: "Xem trước" }));

    expect(
      await screen.findByRole("columnheader", { name: "Tồn trước điều chỉnh" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("columnheader", { name: "Tồn sau điều chỉnh" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("row", { name: /Gạo 10 9 -1 Rơi vỡ/ }),
    ).toBeVisible();
    expect(fetchMock).toHaveBeenCalledWith(
      "/inventory/stocktakes/1/preview",
      expect.objectContaining({
        method: "POST",
        body: [
          { ingredient_id: 1, actual_qty: 9, reason: "Rơi vỡ" },
          { ingredient_id: 2, actual_qty: 4, reason: "Hao hụt" },
        ],
      }),
    );
    expect(wrote("/inventory/stocktakes/1/counts")).toBe(false);
    expect(wrote("/inventory/stocktakes/1/confirm")).toBe(false);
  });

  it("records counts then confirms once the preview is accepted", async () => {
    render(<StocktakePanel />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Tạo phiếu kiểm kê" }),
    );
    await fillCounts();
    fireEvent.click(screen.getByRole("button", { name: "Xem trước" }));
    fireEvent.click(await screen.findByRole("button", { name: "Xác nhận" }));

    await screen.findByRole("button", { name: "Tạo phiếu kiểm kê" });
    expect(fetchMock).toHaveBeenCalledWith(
      "/inventory/stocktakes/1/counts",
      expect.objectContaining({
        method: "POST",
        body: [
          { ingredient_id: 1, actual_qty: 9, reason: "Rơi vỡ" },
          { ingredient_id: 2, actual_qty: 4, reason: "Hao hụt" },
        ],
      }),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "/inventory/stocktakes/1/confirm",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("goes back to the entry sheet with the typed counts kept and nothing written", async () => {
    render(<StocktakePanel />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Tạo phiếu kiểm kê" }),
    );
    await fillCounts();
    fireEvent.click(screen.getByRole("button", { name: "Xem trước" }));
    fireEvent.click(
      await screen.findByRole("button", { name: "Quay lại sửa" }),
    );

    expect(await screen.findByLabelText("Tồn thực tế Gạo")).toHaveValue(9);
    expect(screen.getByLabelText("Lý do chênh lệch Muối")).toHaveValue(
      "Hao hụt",
    );
    expect(screen.getByRole("button", { name: "Xem trước" })).toBeEnabled();
    expect(wrote("/inventory/stocktakes/1/counts")).toBe(false);
    expect(wrote("/inventory/stocktakes/1/confirm")).toBe(false);
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

  it("lets the user cancel a draft left open after a reload", async () => {
    let cancelled = false;
    fetchMock.mockImplementation((path: string) => {
      if (path === "/inventory/stocktakes/7/cancel") {
        cancelled = true;
        return Promise.resolve({ ok: true });
      }
      if (path.startsWith("/inventory/stocktakes")) {
        return Promise.resolve({
          items: cancelled
            ? []
            : [{ MaPhieuKiemKe: 7, TrangThai: "Đang kiểm kê" }],
          total: cancelled ? 0 : 1,
        });
      }
      if (path.startsWith("/inventory/stock")) {
        return Promise.resolve({ items: stockItems });
      }
      return Promise.resolve({});
    });
    vi.spyOn(window, "confirm").mockReturnValue(true);

    render(<StocktakePanel />);

    expect(
      await screen.findByText(/Đang có phiên kiểm kê/),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Hủy phiên" }));

    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/inventory/stocktakes/7/cancel",
        expect.objectContaining({ method: "POST" }),
      ),
    );
  });
});
