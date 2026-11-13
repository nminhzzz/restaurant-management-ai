import { cleanup, render, screen, fireEvent } from "@testing-library/react";
import { afterEach, beforeEach, describe, it, expect, vi } from "vitest";
import { StockTable } from "./stock-table";

vi.mock("@/lib/api-client", () => ({ apiFetch: vi.fn() }));
import { apiFetch } from "@/lib/api-client";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

const baseItems = [
  {
    MaNguyenLieu: 1,
    TenNguyenLieu: "Bột mì",
    CanhBaoTonThap: false,
  },
  {
    MaNguyenLieu: 2,
    TenNguyenLieu: "Đường",
    CanhBaoTonThap: true,
  },
];

afterEach(cleanup);

describe("stock table", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    fetchMock.mockResolvedValue({ items: baseItems, total: 2 });
  });

  it("shows all stock quantities and their unit and calculation time", async () => {
    fetchMock.mockResolvedValue({
      items: [
        {
          ...baseItems[0],
          DonViTinh: "kg",
          SoLuongTon: 100,
          SoLuongDuDieuKien: 80,
          SoLuongGiu: 25,
          SoLuongKhaDung: 55,
          ThoiDiemTinh: "2026-10-23T09:30:00+07:00",
        },
      ],
      total: 1,
    });
    render(<StockTable />);
    await screen.findByText("Bột mì");
    for (const label of [
      "Tồn sổ sách",
      "Đủ điều kiện",
      "Đang giữ",
      "Khả dụng",
      "Đơn vị",
    ]) {
      expect(
        screen.getByRole("columnheader", { name: label }),
      ).toBeInTheDocument();
    }
    expect(screen.getByText("55")).toBeInTheDocument();
    expect(screen.getByText("kg")).toBeInTheDocument();
    const stamp = screen.getByText(/Dữ liệu lúc/);
    // PH-06: the snapshot time is shown as dd/mm/yyyy hh:mm, never as a raw ISO string.
    expect(stamp).toHaveTextContent(/23\/10\/2026/);
    expect(stamp).not.toHaveTextContent(/2026-10-23T/);
    expect(
      screen.getByRole("button", { name: "Xem lô và lịch sử Bột mì" }),
    ).toBeInTheDocument();
  });

  it("shows the average unit cost and the stock value, and 'Chưa xác định' when unknown", async () => {
    fetchMock.mockResolvedValue({
      items: [
        {
          MaNguyenLieu: 1,
          TenNguyenLieu: "Bò",
          DonViTinh: "kg",
          SoLuongTon: 20,
          DonGiaBinhQuan: 230000,
          GiaTriTon: 4600000,
          CanhBaoTonThap: false,
        },
        {
          MaNguyenLieu: 2,
          TenNguyenLieu: "Sả",
          DonViTinh: "g",
          SoLuongTon: 200,
          DonGiaBinhQuan: null,
          GiaTriTon: null,
          CanhBaoTonThap: false,
        },
      ],
      total: 2,
    });

    render(<StockTable />);

    const beef = (await screen.findByText("Bò")).closest("tr")!;
    expect(
      screen.getByRole("columnheader", { name: "Đơn giá bình quân" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("columnheader", { name: "Giá trị tồn" }),
    ).toBeInTheDocument();
    expect(beef).toHaveTextContent("230.000 ₫");
    expect(beef).toHaveTextContent("4.600.000 ₫");
    const lemongrass = screen.getByText("Sả").closest("tr")!;
    expect(lemongrass.textContent?.match(/Chưa xác định/g)).toHaveLength(2);
    expect(lemongrass).not.toHaveTextContent("0 ₫");
  });

  it("opens the cost history of the chosen ingredient", async () => {
    fetchMock.mockImplementation((path: string) => {
      if (path.startsWith("/inventory/stock/1/cost-history")) {
        return Promise.resolve({
          items: [
            {
              ThoiDiemHieuLuc: "2026-10-02T08:00:00",
              DonGiaBinhQuan: 230000,
              SoLuongTon: 20,
              MaGiaoDichKho: 2,
              ChungTu: "Phiếu nhập #2",
            },
            {
              ThoiDiemHieuLuc: "2026-10-01T08:00:00",
              DonGiaBinhQuan: 200000,
              SoLuongTon: 10,
              MaGiaoDichKho: 1,
              ChungTu: "Phiếu nhập #1",
            },
          ],
          total: 2,
        });
      }
      if (path.startsWith("/inventory/stock")) {
        return Promise.resolve({
          items: [{ ...baseItems[0], DonViTinh: "kg" }],
          total: 1,
        });
      }
      return Promise.resolve({ items: [], total: 0 });
    });

    render(<StockTable />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Xem lô và lịch sử Bột mì" }),
    );

    expect(
      await screen.findByRole("row", {
        name: /Phiếu nhập #2 230\.000 ₫\/kg 20/,
      }),
    ).toBeVisible();
    expect(
      screen.getByRole("row", { name: /Phiếu nhập #1 200\.000 ₫\/kg 10/ }),
    ).toBeVisible();
  });

  it("shows loading then table", async () => {
    render(<StockTable />);
    expect(screen.getByText("Đang tải…")).toBeInTheDocument();
    expect(await screen.findByText("Bột mì")).toBeInTheDocument();
  });

  it("marks low-stock rows with a worded warning badge", async () => {
    render(<StockTable />);
    await screen.findByText("Đường");
    const alertRows = screen.getAllByTestId("alert-row");
    expect(alertRows.length).toBe(1);
    expect(alertRows[0].textContent).toContain("Sắp hết");
    const okRows = screen.getAllByTestId("ok-row");
    expect(okRows[0].textContent).not.toContain("Sắp hết");
  });

  it("requests page 1 with the default page size and shows the real total", async () => {
    fetchMock.mockResolvedValue({ items: baseItems, total: 47 });
    render(<StockTable />);
    await screen.findByText("Bột mì");

    expect(fetchMock).toHaveBeenCalledWith(
      "/inventory/stock?page=1&page_size=20",
    );
    expect(screen.getByText("Hiển thị 1–20 trên 47")).toBeInTheDocument();
  });

  it("sends the search text as a server-side filter and resets paging to page 1", async () => {
    fetchMock.mockResolvedValue({ items: baseItems, total: 47 });
    render(<StockTable />);
    await screen.findByText("Bột mì");

    fireEvent.click(screen.getByRole("button", { name: "Trang 2" }));
    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenLastCalledWith(
        "/inventory/stock?page=2&page_size=20",
      ),
    );

    fireEvent.change(screen.getByLabelText("Tìm nguyên liệu"), {
      target: { value: "đường" },
    });

    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenLastCalledWith(
        "/inventory/stock?search=%C4%91%C6%B0%E1%BB%9Dng&page=1&page_size=20",
      ),
    );
  });

  it("maps the 'Cần nhập thêm' tab to alerting=true and resets paging to page 1", async () => {
    fetchMock.mockResolvedValue({ items: baseItems, total: 47 });
    render(<StockTable />);
    await screen.findByText("Bột mì");

    fireEvent.click(screen.getByRole("button", { name: "Trang 2" }));
    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenLastCalledWith(
        "/inventory/stock?page=2&page_size=20",
      ),
    );

    fireEvent.click(screen.getByRole("tab", { name: "Cần nhập thêm" }));

    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenLastCalledWith(
        "/inventory/stock?alerting=true&page=1&page_size=20",
      ),
    );
  });
});
