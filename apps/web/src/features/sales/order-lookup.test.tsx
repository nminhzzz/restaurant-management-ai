import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { OrderLookup } from "./order-lookup";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

const openOrder = {
  MaOrder: 42,
  MaOrderHienThi: "ORD-250926-042",
  MaBan: 7,
  BusinessDate: "2026-09-25",
  TrangThai: "Đang mở",
};

describe("OrderLookup", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    fetchMock.mockImplementation((path: string) =>
      Promise.resolve(
        path.startsWith("/catalog/tables")
          ? [{ MaBan: 7, TenBan: "Bàn 7" }]
          : { items: [openOrder], total: 1 },
      ),
    );
  });
  afterEach(cleanup);

  it("lists the open orders as soon as it opens", async () => {
    render(<OrderLookup />);

    expect(
      await screen.findByRole("button", { name: "Chọn ORD-250926-042" }),
    ).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/sales/orders?status=%C4%90ang+m%E1%BB%9F&page=1&size=20",
    );
  });

  it("searches by table and Business Date range (FR-SALE-22)", async () => {
    render(<OrderLookup />);
    await screen.findByRole("option", { name: "Bàn 7" });

    fireEvent.change(screen.getByLabelText("Bàn"), { target: { value: "7" } });
    fireEvent.change(screen.getByLabelText("Trạng thái"), {
      target: { value: "" },
    });
    fireEvent.change(screen.getByLabelText("Từ ngày"), {
      target: { value: "2026-09-25" },
    });
    fireEvent.change(screen.getByLabelText("Đến ngày"), {
      target: { value: "2026-09-25" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Tìm" }));

    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/sales/orders?table_id=7&date_from=2026-09-25&date_to=2026-09-25&page=1&size=20",
      ),
    );
  });

  it("resets to page 1 and sends page/size when paging changes filters", async () => {
    fetchMock.mockImplementation((path: string) =>
      Promise.resolve(
        path.startsWith("/catalog/tables")
          ? [{ MaBan: 7, TenBan: "Bàn 7" }]
          : { items: [openOrder], total: 45 },
      ),
    );
    render(<OrderLookup />);
    await screen.findByRole("button", { name: "Chọn ORD-250926-042" });

    expect(screen.getByText("Hiển thị 1–20 trên 45")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Trang 2" }));
    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/sales/orders?status=%C4%90ang+m%E1%BB%9F&page=2&size=20",
      ),
    );

    fireEvent.change(screen.getByLabelText("Trạng thái"), {
      target: { value: "" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Tìm" }));
    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith("/sales/orders?page=1&size=20"),
    );
  });

  it("reports the selected order", async () => {
    const onSelect = vi.fn();
    render(<OrderLookup onSelect={onSelect} />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Chọn ORD-250926-042" }),
    );

    expect(onSelect).toHaveBeenCalledWith(42);
  });
});
