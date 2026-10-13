import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { apiFetch } from "@/lib/api-client";

import { InventoryWorkspace } from "./inventory-workspace";
import { LotExpiryTable } from "./lot-expiry-table";

vi.mock("@/lib/api-client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api-client")>()),
  apiFetch: vi.fn(),
}));

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;
const lots = [
  {
    MaLoNguyenLieu: 1,
    MaNguyenLieu: 10,
    TenNguyenLieu: "Gạo",
    SoLuongConLai: 2,
    HanSuDung: "2026-10-10",
    TrangThaiHanSuDung: "Hết hạn",
  },
  {
    MaLoNguyenLieu: 2,
    MaNguyenLieu: 10,
    TenNguyenLieu: "Gạo",
    SoLuongConLai: 3,
    HanSuDung: "2026-10-12",
    TrangThaiHanSuDung: "Sắp hết hạn",
  },
  {
    MaLoNguyenLieu: 3,
    MaNguyenLieu: 10,
    TenNguyenLieu: "Gạo",
    SoLuongConLai: 4,
    HanSuDung: null,
    TrangThaiHanSuDung: "Còn hạn",
  },
];

afterEach(cleanup);
beforeEach(() => {
  vi.resetAllMocks();
  fetchMock.mockImplementation((path: string) =>
    Promise.resolve(
      path.startsWith("/inventory/lots")
        ? { items: lots, total: 3, page: 1, page_size: 20 }
        : { items: [], total: 0, page: 1, page_size: 20 },
    ),
  );
});

describe("lot expiry table", () => {
  it("shows a separate inventory tab and all expiry statuses", async () => {
    render(<InventoryWorkspace />);
    fireEvent.keyDown(screen.getByRole("tab", { name: "Hạn sử dụng" }), {
      key: "Enter",
    });
    expect(
      await screen.findByRole("table", { name: "Hạn sử dụng theo lô" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Hết hạn")).toBeInTheDocument();
    expect(screen.getByText("Sắp hết hạn")).toBeInTheDocument();
    expect(screen.getByText("Còn hạn")).toBeInTheDocument();
    expect(screen.queryByText("Sắp hết")).not.toBeInTheDocument();
  });

  it("shows loading, then paginates using the API total", async () => {
    fetchMock.mockResolvedValue({
      items: lots,
      total: 41,
      page: 1,
      page_size: 20,
    });
    render(<LotExpiryTable />);
    expect(screen.getByText("Đang tải…")).toBeInTheDocument();
    await screen.findByText("Hiển thị 1–20 trên 41");
    fireEvent.click(screen.getByRole("button", { name: "Trang 2" }));
    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenLastCalledWith(
        "/inventory/lots?page=2&page_size=20",
      ),
    );
  });

  it("hides the previous page while the next page request is pending", async () => {
    let resolveSecond!: (value: unknown) => void;
    const secondPage = new Promise((resolve) => {
      resolveSecond = resolve;
    });
    fetchMock.mockImplementation((path: string) =>
      path.includes("page=2")
        ? secondPage
        : Promise.resolve({ items: lots, total: 41, page: 1, page_size: 20 }),
    );
    render(<LotExpiryTable />);
    await screen.findByRole("table", { name: "Hạn sử dụng theo lô" });
    fireEvent.click(screen.getByRole("button", { name: "Trang 2" }));
    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenLastCalledWith(
        "/inventory/lots?page=2&page_size=20",
      ),
    );
    expect(screen.getByText("Đang tải…")).toBeInTheDocument();
    expect(
      screen.queryByRole("table", { name: "Hạn sử dụng theo lô" }),
    ).not.toBeInTheDocument();
    expect(screen.queryAllByText("Gạo")).toHaveLength(0);
    resolveSecond({
      items: [{ ...lots[0], MaLoNguyenLieu: 21, TenNguyenLieu: "Muối" }],
      total: 41,
      page: 2,
      page_size: 20,
    });
    expect(await screen.findByText("Muối")).toBeInTheDocument();
  });

  it("shows an empty state", async () => {
    fetchMock.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
    });
    render(<LotExpiryTable />);
    expect(
      await screen.findByText("Chưa có lô nguyên liệu"),
    ).toBeInTheDocument();
  });

  it("shows an error and can retry", async () => {
    fetchMock.mockRejectedValueOnce(new Error("Không thể tải dữ liệu"));
    render(<LotExpiryTable />);
    await screen.findByText(
      "Không tải được dữ liệu. Kiểm tra kết nối rồi thử lại.",
    );
    fireEvent.click(screen.getByRole("button", { name: /Thử lại/ }));
    expect(
      await screen.findByRole("table", { name: "Hạn sử dụng theo lô" }),
    ).toBeInTheDocument();
  });

  it("shows days left and the used-up status", async () => {
    fetchMock.mockResolvedValue({
      items: [
        { ...lots[1], SoNgayConLai: 2 },
        { ...lots[0], SoNgayConLai: -3 },
        {
          ...lots[2],
          MaLoNguyenLieu: 4,
          SoLuongConLai: 0,
          SoNgayConLai: 40,
          TrangThaiHanSuDung: "Đã dùng hết",
        },
      ],
      total: 3,
      page: 1,
      page_size: 20,
    });
    render(<LotExpiryTable />);

    expect(await screen.findByText("Còn 2 ngày")).toBeInTheDocument();
    expect(screen.getByText("Quá hạn 3 ngày")).toBeInTheDocument();
    expect(screen.getByText("Đã dùng hết")).toBeInTheDocument();
    expect(screen.queryByText("Còn 40 ngày")).not.toBeInTheDocument();
  });
});
