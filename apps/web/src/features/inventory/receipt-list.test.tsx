import { cleanup, render, screen, fireEvent } from "@testing-library/react";
import { afterEach, beforeEach, describe, it, expect, vi } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { ReceiptList } from "./receipt-list";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

const receipts = [
  {
    MaPhieuNhap: 1,
    MaNhaCungCap: 9,
    NgayNhap: "2026-09-25T08:00:00",
    TrangThai: "Nháp",
  },
];
const suppliers = [{ MaNhaCungCap: 9, TenNhaCungCap: "NCC A" }];

function route(receiptsTotal = 1) {
  fetchMock.mockImplementation((path: string) => {
    if (path.startsWith("/inventory/receipts")) {
      return Promise.resolve({ items: receipts, total: receiptsTotal });
    }
    if (path.startsWith("/catalog/ingredients")) {
      return Promise.resolve({ items: [] });
    }
    if (path === "/catalog/suppliers") {
      return Promise.resolve(suppliers);
    }
    return Promise.resolve({});
  });
}

describe("ReceiptList", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    route();
  });
  afterEach(cleanup);

  it("requests page 1 with the default page size and shows the real total", async () => {
    route(38);
    render(<ReceiptList />);
    await screen.findByText("#1");

    expect(fetchMock).toHaveBeenCalledWith(
      "/inventory/receipts?page=1&page_size=20",
    );
    expect(screen.getByText("Hiển thị 1–20 trên 38")).toBeInTheDocument();
  });

  it("sends supplier, status and date range filters and resets paging to page 1", async () => {
    route(38);
    render(<ReceiptList />);
    await screen.findByText("#1");

    fireEvent.click(screen.getByRole("button", { name: "Trang 2" }));
    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenLastCalledWith(
        "/inventory/receipts?page=2&page_size=20",
      ),
    );

    fireEvent.change(screen.getByLabelText("Nhà cung cấp"), {
      target: { value: "9" },
    });
    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenLastCalledWith(
        "/inventory/receipts?supplier_id=9&page=1&page_size=20",
      ),
    );

    fireEvent.change(screen.getByLabelText("Trạng thái"), {
      target: { value: "Nháp" },
    });
    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenLastCalledWith(
        "/inventory/receipts?supplier_id=9&status=Nh%C3%A1p&page=1&page_size=20",
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
        "/inventory/receipts?supplier_id=9&status=Nh%C3%A1p&date_from=2026-09-01&date_to=2026-09-25&page=1&page_size=20",
      ),
    );
  });
});
