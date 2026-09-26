import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { ApiError, apiFetch } from "@/lib/api-client";
import { OrderStep } from "./order-step";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

const dishes = {
  items: [
    { MaMon: 5, TenMon: "Phở bò", TrangThai: "Hoạt động", GiaHienTai: 65000, MaNhomMon: 1 },
    { MaMon: 6, TenMon: "Nem rán", TrangThai: "Hoạt động", GiaHienTai: null, MaNhomMon: 1 },
    { MaMon: 7, TenMon: "Bún chả", TrangThai: "Hết nguyên liệu", GiaHienTai: 60000, MaNhomMon: 1 },
    { MaMon: 8, TenMon: "Gỏi cuốn", TrangThai: "Hoạt động", GiaHienTai: 30000, MaNhomMon: 1 },
  ],
};

function route(extra: Record<string, unknown> = {}) {
  const routes: Record<string, unknown> = {
    "/catalog/tables": [{ MaBan: 4, TenBan: "Bàn 04" }],
    "/catalog/dishes": dishes,
    "/catalog/groups": [{ MaNhomMon: 1, TenNhom: "Món chính" }],
    ...extra,
  };
  fetchMock.mockImplementation((path: string) =>
    Promise.resolve(Object.entries(routes).find(([p]) => path.startsWith(p))?.[1] ?? {}),
  );
}

describe("OrderStep", () => {
  beforeEach(() => vi.resetAllMocks());

  it("shows prices and keeps unpriced and unsellable dishes out of the cart", async () => {
    route();
    render(<OrderStep tableId={4} orderId={null} onBack={vi.fn()} onSent={vi.fn()} />);

    expect(await screen.findByText("65.000 ₫")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Nem rán/ })).toBeDisabled();
    expect(screen.getByText("Chưa có giá")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Bún chả/ })).not.toBeInTheDocument();
  });

  it("totals the cart as dishes are added", async () => {
    route();
    render(<OrderStep tableId={4} orderId={null} onBack={vi.fn()} onSent={vi.fn()} />);
    const tile = await screen.findByRole("button", { name: /Phở bò/ });
    fireEvent.click(tile);
    fireEvent.click(tile);
    expect(screen.getByTestId("cart-total")).toHaveTextContent("130.000 ₫");
  });

  it("creates a new dine-in order and moves on to payment", async () => {
    const onSent = vi.fn();
    route({ "/sales/orders": { MaOrder: 42, MaOrderHienThi: "ORD-42", rejected: [] } });
    render(<OrderStep tableId={4} orderId={null} onBack={vi.fn()} onSent={onSent} />);
    fireEvent.click(await screen.findByRole("button", { name: /Phở bò/ }));
    fireEvent.click(screen.getByRole("button", { name: "Gửi bếp & thanh toán" }));

    await vi.waitFor(() => expect(onSent).toHaveBeenCalledWith(42, "pay"));
    expect(fetchMock).toHaveBeenCalledWith("/sales/orders", expect.objectContaining({
      method: "POST",
      body: expect.objectContaining({ MaBan: 4, LoaiDon: "Tại chỗ" }),
    }));
  });

  it("adds lines to an open order instead of creating one", async () => {
    const onSent = vi.fn();
    route({
      "/sales/orders/142/lines": { MaChiTietOrder: 9 },
      "/sales/orders/142": {
        MaOrder: 142, MaOrderHienThi: "ORD-142", TrangThai: "Đang mở", ThoiDiemTao: "2026-09-26T14:32:00",
        lines: [{ MaChiTietOrder: 1, MaMon: 5, SoLuong: 2, DonGia: 65000, TrangThai: "Chờ" }],
      },
    });
    render(<OrderStep tableId={4} orderId={142} onBack={vi.fn()} onSent={onSent} />);

    expect(await screen.findByText("Đã gửi bếp")).toBeInTheDocument();
    expect(screen.getByText(/mở 14:32/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Phở bò/ }));
    fireEvent.click(screen.getByRole("button", { name: "Gửi bếp" }));

    await vi.waitFor(() => expect(onSent).toHaveBeenCalledWith(142, "floor"));
    expect(fetchMock).toHaveBeenCalledWith("/sales/orders/142/lines", expect.objectContaining({
      method: "POST",
      body: { MaMon: 5, SoLuong: 1, GhiChu: null },
    }));
  });

  it("keeps the sent total right after a partial add-more failure", async () => {
    const onSent = vi.fn();
    const routes: Record<string, unknown> = {
      "/catalog/tables": [{ MaBan: 4, TenBan: "Bàn 04" }],
      "/catalog/dishes": dishes,
      "/catalog/groups": [{ MaNhomMon: 1, TenNhom: "Món chính" }],
      "/sales/orders/142": {
        MaOrder: 142, MaOrderHienThi: "ORD-142", TrangThai: "Đang mở",
        lines: [{ MaChiTietOrder: 1, MaMon: 5, SoLuong: 2, DonGia: 65000, TrangThai: "Chờ" }],
      },
    };
    fetchMock.mockImplementation((path: string, options?: { body?: { MaMon: number } }) => {
      if (path === "/sales/orders/142/lines") {
        if (options?.body?.MaMon === 5) return Promise.resolve({ MaChiTietOrder: 9 });
        return Promise.reject(new ApiError(409, "OUT_OF_STOCK", "Hết nguyên liệu."));
      }
      return Promise.resolve(Object.entries(routes).find(([p]) => path.startsWith(p))?.[1] ?? {});
    });

    render(<OrderStep tableId={4} orderId={142} onBack={vi.fn()} onSent={onSent} />);
    fireEvent.click(await screen.findByRole("button", { name: /Phở bò/ }));
    fireEvent.click(screen.getByRole("button", { name: /Gỏi cuốn/ }));
    fireEvent.click(screen.getByRole("button", { name: "Gửi bếp" }));

    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(onSent).not.toHaveBeenCalled();
    // Phở bò was confirmed and left the cart; Gỏi cuốn failed and stayed.
    expect(screen.queryByLabelText("Số lượng Phở bò")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Số lượng Gỏi cuốn")).toBeInTheDocument();
    // sent (130.000) + confirmed Phở bò (65.000) + unsent Gỏi cuốn (30.000)
    expect(screen.getByTestId("cart-total")).toHaveTextContent("225.000 ₫");
  });

  it("creates a takeaway order when there is no table", async () => {
    route({ "/sales/orders": { MaOrder: 50, MaOrderHienThi: "ORD-50", rejected: [] } });
    render(<OrderStep tableId={null} orderId={null} onBack={vi.fn()} onSent={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: /Phở bò/ }));
    fireEvent.click(screen.getByRole("button", { name: "Gửi bếp" }));
    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith("/sales/orders", expect.objectContaining({
        body: expect.objectContaining({ MaBan: null, LoaiDon: "Mang về" }),
      })),
    );
  });
});
