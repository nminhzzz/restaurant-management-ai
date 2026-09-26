import { fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { FloorStep } from "./floor-step";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

const board = {
  tables: [
    { MaBan: 1, TenBan: "Bàn 01", TrangThai: "Trống", order: null },
    {
      MaBan: 4,
      TenBan: "Bàn 04",
      TrangThai: "Đang phục vụ",
      order: { MaOrder: 142, MaOrderHienThi: "ORD-142", MoLuc: "2026-09-26T14:32:00", SoMon: 4, TamTinh: 248000 },
    },
  ],
  takeaway: [{ MaOrder: 139, MaOrderHienThi: "ORD-139", MoLuc: null, SoMon: 2, TamTinh: 120000 }],
};

function setup() {
  const handlers = { onNewOrder: vi.fn(), onAddMore: vi.fn(), onPay: vi.fn() };
  render(<FloorStep {...handlers} />);
  return handlers;
}

describe("FloorStep", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    fetchMock.mockImplementation((path: string) =>
      Promise.resolve(path.startsWith("/sales/floor") ? board : { items: [] }),
    );
  });

  it("opens a new order on a free table", async () => {
    const h = setup();
    fireEvent.click(await screen.findByRole("button", { name: /Bàn 01/ }));
    expect(h.onNewOrder).toHaveBeenCalledWith(1);
  });

  it("offers add-more and pay for a busy table with its running total", async () => {
    const h = setup();
    fireEvent.click(await screen.findByRole("button", { name: /Bàn 04/ }));
    expect(screen.getAllByText("248.000 ₫").length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: "Gọi thêm" }));
    expect(h.onAddMore).toHaveBeenCalledWith(142, 4);
    fireEvent.click(screen.getByRole("button", { name: "Thanh toán" }));
    expect(h.onPay).toHaveBeenCalledWith(142, 4);
  });

  it("starts and resumes takeaway orders", async () => {
    const h = setup();
    fireEvent.click(await screen.findByRole("button", { name: "Đơn mang về mới" }));
    expect(h.onNewOrder).toHaveBeenCalledWith(null);
    fireEvent.click(screen.getByRole("button", { name: /ORD-139/ }));
    expect(h.onPay).toHaveBeenCalledWith(139, null);
  });

  it("filters tables by status", async () => {
    setup();
    await screen.findByRole("button", { name: /Bàn 04/ });
    const filters = screen.getByRole("group", { name: "Lọc bàn" });
    fireEvent.click(within(filters).getByRole("button", { name: /Trống/ }));
    expect(screen.queryByRole("button", { name: /Bàn 04/ })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Bàn 01/ })).toBeInTheDocument();
  });

  it("looks up an order by code and opens its payment", async () => {
    const h = setup();
    fetchMock.mockImplementation((path: string) =>
      Promise.resolve(
        path.startsWith("/sales/orders?code=")
          ? { items: [{ MaOrder: 77, MaBan: 3 }] }
          : board,
      ),
    );
    fireEvent.change(await screen.findByLabelText("Tra mã order"), { target: { value: "ORD-77" } });
    fireEvent.submit(screen.getByRole("search"));
    await vi.waitFor(() => expect(h.onPay).toHaveBeenCalledWith(77, 3));
  });
});
