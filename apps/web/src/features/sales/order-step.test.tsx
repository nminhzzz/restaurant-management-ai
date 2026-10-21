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
    {
      MaMon: 5,
      TenMon: "Phở bò",
      TrangThai: "Hoạt động",
      GiaHienTai: 65000,
      SoSuatKhaDung: 10,
      MaNhomMon: 1,
    },
    {
      MaMon: 6,
      TenMon: "Nem rán",
      TrangThai: "Hoạt động",
      GiaHienTai: null,
      MaNhomMon: 1,
    },
    {
      MaMon: 7,
      TenMon: "Bún chả",
      TrangThai: "Hết nguyên liệu",
      GiaHienTai: 60000,
      MaNhomMon: 1,
    },
    {
      MaMon: 8,
      TenMon: "Gỏi cuốn",
      TrangThai: "Hoạt động",
      GiaHienTai: 30000,
      MaNhomMon: 1,
    },
  ],
};

function route(extra: Record<string, unknown> = {}) {
  const routes: Record<string, unknown> = {
    "/catalog/tables": [{ MaBan: 4, TenBan: "Bàn 04" }],
    "/catalog/dishes": dishes,
    "/catalog/groups": [{ MaNhomMon: 1, TenNhom: "Món chính" }],
    "/sales/holds": { MaGiuCho: 99, SoLuong: 1, DonGia: 65000 },
    ...extra,
  };
  fetchMock.mockImplementation(
    (
      path: string,
      options?: { method?: string; body?: { quantity?: number } },
    ) => {
      if (path.startsWith("/sales/holds")) {
        if (options?.method === "DELETE") return Promise.resolve({});
        return Promise.resolve({
          MaGiuCho: 99,
          SoLuong: options?.body?.quantity ?? 1,
          DonGia: 65000,
        });
      }
      return Promise.resolve(
        Object.entries(routes).find(([p]) => path.startsWith(p))?.[1] ?? {},
      );
    },
  );
}

describe("OrderStep", () => {
  beforeEach(() => vi.resetAllMocks());

  it("shows prices and keeps unpriced and unsellable dishes out of the cart", async () => {
    route();
    render(
      <OrderStep
        tableId={4}
        orderId={null}
        onBack={vi.fn()}
        onSent={vi.fn()}
      />,
    );

    expect(await screen.findByText("65.000 ₫")).toBeInTheDocument();
    expect(screen.getByText("Còn 10 suất")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Nem rán/ })).toBeDisabled();
    expect(screen.getByText("Chưa có giá")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Bún chả/ }),
    ).not.toBeInTheDocument();
  });

  it("totals the cart as dishes are added", async () => {
    route();
    render(
      <OrderStep
        tableId={4}
        orderId={null}
        onBack={vi.fn()}
        onSent={vi.fn()}
      />,
    );
    const tile = await screen.findByRole("button", { name: /Phở bò/ });
    fireEvent.click(tile);
    await vi.waitFor(() =>
      expect(screen.getByTestId("cart-total")).toHaveTextContent("65.000 ₫"),
    );
    fireEvent.click(tile);
    await vi.waitFor(() =>
      expect(screen.getByTestId("cart-total")).toHaveTextContent("130.000 ₫"),
    );
  });

  it("creates a new dine-in order and moves on to payment", async () => {
    const onSent = vi.fn();
    route({
      "/sales/orders": { MaOrder: 42, MaOrderHienThi: "ORD-42", rejected: [] },
    });
    render(
      <OrderStep tableId={4} orderId={null} onBack={vi.fn()} onSent={onSent} />,
    );
    fireEvent.click(await screen.findByRole("button", { name: /Phở bò/ }));
    await vi.waitFor(() =>
      expect(screen.getByTestId("cart-total")).toHaveTextContent("65.000 ₫"),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Gửi bếp & thanh toán" }),
    );

    await vi.waitFor(() => expect(onSent).toHaveBeenCalledWith(42, "pay"));
    expect(fetchMock).toHaveBeenCalledWith(
      "/sales/orders",
      expect.objectContaining({
        method: "POST",
        body: expect.objectContaining({ MaBan: 4, LoaiDon: "Tại chỗ" }),
      }),
    );
  });

  it("holds ingredients before sending an order", async () => {
    const onSent = vi.fn();
    route({
      "/sales/orders": { MaOrder: 43, MaOrderHienThi: "ORD-43", rejected: [] },
    });
    render(
      <OrderStep tableId={4} orderId={null} onBack={vi.fn()} onSent={onSent} />,
    );
    fireEvent.click(await screen.findByRole("button", { name: /Phở bò/ }));
    await vi.waitFor(() =>
      expect(screen.getByTestId("cart-total")).toHaveTextContent("65.000 ₫"),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Gửi bếp & thanh toán" }),
    );

    await vi.waitFor(() => expect(onSent).toHaveBeenCalledWith(43, "pay"));
    expect(fetchMock).toHaveBeenCalledWith(
      "/sales/holds",
      expect.objectContaining({
        method: "POST",
        body: expect.objectContaining({
          table_id: 4,
          dish_id: 5,
          quantity: 1,
        }),
      }),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "/sales/orders",
      expect.objectContaining({
        body: expect.objectContaining({
          lines: [expect.objectContaining({ MaMon: 5, hold_id: 99 })],
        }),
      }),
    );
  });

  it("adds lines to an open order instead of creating one", async () => {
    const onSent = vi.fn();
    route({
      "/sales/orders/142/lines": { MaChiTietOrder: 9 },
      "/sales/orders/142": {
        MaOrder: 142,
        MaOrderHienThi: "ORD-142",
        TrangThai: "Đang mở",
        ThoiDiemTao: "2026-09-26T14:32:00",
        lines: [
          {
            MaChiTietOrder: 1,
            MaMon: 5,
            SoLuong: 2,
            DonGia: 65000,
            TrangThai: "Chờ",
          },
        ],
      },
    });
    render(
      <OrderStep tableId={4} orderId={142} onBack={vi.fn()} onSent={onSent} />,
    );

    expect(await screen.findByText("Đã gửi bếp")).toBeInTheDocument();
    expect(screen.getByText(/mở 14:32/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Phở bò/ }));
    await vi.waitFor(() =>
      expect(screen.getByTestId("cart-total")).toHaveTextContent("195.000 ₫"),
    );
    fireEvent.click(screen.getByRole("button", { name: "Gửi bếp" }));

    await vi.waitFor(() => expect(onSent).toHaveBeenCalledWith(142, "floor"));
    expect(fetchMock).toHaveBeenCalledWith(
      "/sales/orders/142/lines/bulk",
      expect.objectContaining({
        method: "POST",
        body: {
          lines: [
            expect.objectContaining({
              dish_id: 5,
              quantity: 1,
              note: null,
              hold_id: 99,
              request_line_id: expect.any(String),
            }),
          ],
        },
      }),
    );
  });

  it("keeps the whole cart when a bulk add-more request fails", async () => {
    const onSent = vi.fn();
    const routes: Record<string, unknown> = {
      "/catalog/tables": [{ MaBan: 4, TenBan: "Bàn 04" }],
      "/catalog/dishes": dishes,
      "/catalog/groups": [{ MaNhomMon: 1, TenNhom: "Món chính" }],
      "/sales/orders/142": {
        MaOrder: 142,
        MaOrderHienThi: "ORD-142",
        TrangThai: "Đang mở",
        lines: [
          {
            MaChiTietOrder: 1,
            MaMon: 5,
            SoLuong: 2,
            DonGia: 65000,
            TrangThai: "Chờ",
          },
        ],
      },
    };
    fetchMock.mockImplementation((path: string) => {
      if (path === "/sales/orders/142/lines/bulk") {
        return Promise.reject(
          new ApiError(409, "OUT_OF_STOCK", "Hết nguyên liệu."),
        );
      }
      return Promise.resolve(
        Object.entries(routes).find(([p]) => path.startsWith(p))?.[1] ?? {},
      );
    });

    render(
      <OrderStep tableId={4} orderId={142} onBack={vi.fn()} onSent={onSent} />,
    );
    fireEvent.click(await screen.findByRole("button", { name: /Phở bò/ }));
    await vi.waitFor(() =>
      expect(screen.getByLabelText("Số lượng Phở bò")).toBeInTheDocument(),
    );
    fireEvent.click(screen.getByRole("button", { name: /Gỏi cuốn/ }));
    await vi.waitFor(() =>
      expect(screen.getByLabelText("Số lượng Gỏi cuốn")).toBeInTheDocument(),
    );
    fireEvent.click(screen.getByRole("button", { name: "Gửi bếp" }));

    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(onSent).not.toHaveBeenCalled();
    // FR-SALE-03: the whole batch fails, so both lines stay in the cart.
    expect(screen.getByLabelText("Số lượng Phở bò")).toBeInTheDocument();
    expect(screen.getByLabelText("Số lượng Gỏi cuốn")).toBeInTheDocument();
    // sent (130.000) + unsent Phở bò (65.000) + unsent Gỏi cuốn (30.000)
    expect(screen.getByTestId("cart-total")).toHaveTextContent("225.000 ₫");
  });

  it("creates a takeaway order when there is no table", async () => {
    route({
      "/sales/orders": { MaOrder: 50, MaOrderHienThi: "ORD-50", rejected: [] },
    });
    render(
      <OrderStep
        tableId={null}
        orderId={null}
        onBack={vi.fn()}
        onSent={vi.fn()}
      />,
    );
    fireEvent.click(await screen.findByRole("button", { name: /Phở bò/ }));
    await vi.waitFor(() =>
      expect(screen.getByTestId("cart-total")).toHaveTextContent("65.000 ₫"),
    );
    fireEvent.click(screen.getByRole("button", { name: "Gửi bếp" }));
    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/sales/orders",
        expect.objectContaining({
          body: expect.objectContaining({ MaBan: null, LoaiDon: "Mang về" }),
        }),
      ),
    );
  });
});
