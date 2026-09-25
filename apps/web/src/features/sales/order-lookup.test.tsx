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
      "/sales/orders?status=%C4%90ang+m%E1%BB%9F",
    );
  });

  it("searches by table and Business Date (FR-SALE-22)", async () => {
    render(<OrderLookup />);
    await screen.findByRole("option", { name: "Bàn 7" });

    fireEvent.change(screen.getByLabelText("Bàn"), { target: { value: "7" } });
    fireEvent.change(screen.getByLabelText("Trạng thái"), {
      target: { value: "" },
    });
    fireEvent.change(screen.getByLabelText("Business Date"), {
      target: { value: "2026-09-25" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Tìm" }));

    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/sales/orders?table_id=7&business_date=2026-09-25",
      ),
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
