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
