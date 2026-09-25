import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { clearSession, saveSession } from "@/lib/session";
import { OrderScreen } from "./order-screen";
import { PaymentPanel } from "./payment-panel";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

/** Route the mocked apiFetch by path prefix; the first matching prefix wins. */
function stubByPath(routes: Record<string, unknown>) {
  const entries = Object.entries(routes);
  fetchMock.mockImplementation((path: string) =>
    Promise.resolve(
      entries.find(([prefix]) => path.startsWith(prefix))?.[1] ?? {},
    ),
  );
}

function qr(overrides: Record<string, unknown> = {}) {
  const now = new Date();
  const end = new Date(now.getTime() + 10 * 60 * 1000);
  return {
    MaGiaoDich: 1,
    PhuongThuc: "QR",
    TrangThai: "Chờ xác nhận",
    ThoiDiemTaoQR: now.toISOString(),
    ThoiDiemHetHan: end.toISOString(),
    ...overrides,
  };
}

const openOrder = {
  MaOrder: 1,
  MaOrderHienThi: "ORD-1",
  TrangThai: "Đang mở",
  lines: [],
};

describe("PaymentPanel", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    clearSession();
  });

  it("disables creating a new QR while one is still live", async () => {
    stubByPath({
      "/sales/orders/1/pay/qr": qr(),
      "/sales/orders/1": openOrder,
    });
    render(<PaymentPanel orderId={1} />);

    fireEvent.click(await screen.findByText("Thanh toán QR"));

    await screen.findByText("Chờ xác nhận");
    expect(screen.getByText("Tạo mã QR mới")).toBeDisabled();
  });

  it("counts the QR deadline down and shows an expiry state", async () => {
    vi.useFakeTimers();
    try {
      const end = new Date(Date.now() + 10 * 60 * 1000).toISOString();
      stubByPath({
        "/sales/orders/1/pay/qr": qr({ ThoiDiemHetHan: end }),
        "/sales/orders/1": openOrder,
      });
      render(<PaymentPanel orderId={1} />);
      // The pay buttons appear only once the order has loaded.
      await act(async () => {});

      await act(async () => {
        fireEvent.click(screen.getByText("Thanh toán QR"));
      });
      expect(screen.getByText("10:00")).toBeInTheDocument();

      await act(async () => {
        vi.advanceTimersByTime(600_000);
      });
      expect(screen.getByText("Hết hạn")).toBeInTheDocument();
    } finally {
      vi.useRealTimers();
    }
  });

  it("only offers the full-order cancellation to a manager", async () => {
    saveSession({ token: "t", role: "CASHIER", username: "thungan01" });
    stubByPath({ "/sales/orders/1": openOrder });
    render(<PaymentPanel orderId={1} />);

    await screen.findByText("ORD-1");
    expect(screen.queryByText("Hủy toàn bộ order")).not.toBeInTheDocument();
  });

  it("shows the full-order cancellation to a manager", async () => {
    saveSession({ token: "t", role: "MANAGER", username: "quanly" });
    stubByPath({ "/sales/orders/1": openOrder });
    render(<PaymentPanel orderId={1} />);

    expect(await screen.findByText("Hủy toàn bộ order")).toBeInTheDocument();
  });

  it("hides the full-order cancellation while a QR transaction is live", async () => {
    saveSession({ token: "t", role: "MANAGER", username: "quanly" });
    stubByPath({
      "/sales/orders/1/payments": { items: [qr()] },
      "/sales/orders/1": openOrder,
    });
    render(<PaymentPanel orderId={1} />);

    await screen.findByText("ORD-1");
    expect(screen.queryByText("Hủy toàn bộ order")).not.toBeInTheDocument();
  });

  it("offers reconciliation once an order is waiting for it", async () => {
    saveSession({ token: "t", role: "MANAGER", username: "quanly" });
    stubByPath({
      "/sales/orders/1/payments": {
        items: [qr({ TrangThai: "Chờ đối soát" })],
      },
      "/sales/orders/1": { ...openOrder, TrangThai: "Chờ đối soát" },
    });
    render(<PaymentPanel orderId={1} />);

    await screen.findByText("ORD-1");
    expect(
      screen.getByLabelText("Mã tham chiếu ngân hàng"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Xác nhận đã nhận tiền" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Không có giao dịch" }),
    ).toBeInTheDocument();
  });
});

describe("OrderScreen", () => {
  beforeEach(() => vi.resetAllMocks());

  it("hides dishes that are out of stock", async () => {
    stubByPath({
      "/catalog/tables": [{ MaBan: 1, TenBan: "Bàn 1" }],
      "/catalog/dishes": {
        items: [
          {
            MaMon: 1,
            TenMon: "Phở bò",
            TrangThai: "Hoạt động",
            GiaHienTai: 65000,
          },
          {
            MaMon: 2,
            TenMon: "Bún chả",
            TrangThai: "Hết nguyên liệu",
            GiaHienTai: 40000,
          },
        ],
      },
    });
    render(<OrderScreen />);

    expect(
      await screen.findByRole("button", { name: /Phở bò/ }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Bún chả/ }),
    ).not.toBeInTheDocument();
  });

  it("submits the cart and reports the created order", async () => {
    const onCreated = vi.fn();
    stubByPath({
      "/catalog/tables": [{ MaBan: 7, TenBan: "Bàn 7" }],
      "/catalog/dishes": {
        items: [
          {
            MaMon: 5,
            TenMon: "Phở bò",
            TrangThai: "Hoạt động",
            GiaHienTai: 65000,
          },
        ],
      },
      "/sales/orders": { MaOrder: 42, MaOrderHienThi: "ORD-42", rejected: [] },
    });
    render(<OrderScreen onOrderCreated={onCreated} />);

    fireEvent.click(await screen.findByRole("button", { name: /Phở bò/ }));
    fireEvent.click(screen.getByRole("radio", { name: "Bàn 7" }));
    fireEvent.click(screen.getByRole("button", { name: "Gửi order" }));

    expect(await screen.findByText("Đã tạo ORD-42")).toBeInTheDocument();
    expect(onCreated).toHaveBeenCalledWith(42);
  });

  const menu = {
    "/catalog/tables": [{ MaBan: 7, TenBan: "Bàn 7" }],
    "/catalog/dishes": {
      items: [
        {
          MaMon: 5,
          TenMon: "Phở bò",
          TrangThai: "Hoạt động",
          GiaHienTai: 65000,
        },
      ],
    },
  };

  it("totals the cart and drops a line when its quantity reaches zero", async () => {
    stubByPath(menu);
    render(<OrderScreen />);

    const tile = await screen.findByRole("button", { name: /Phở bò/ });
    fireEvent.click(tile);
    fireEvent.click(tile);
    expect(screen.getByLabelText("Số lượng Phở bò")).toHaveValue(2);
    expect(
      screen.getByText("130.000 ₫", { selector: "span.text-2xl" }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Bớt một Phở bò" }));
    fireEvent.click(screen.getByRole("button", { name: "Bỏ Phở bò" }));

    expect(screen.queryByLabelText("Số lượng Phở bò")).not.toBeInTheDocument();
    expect(screen.getByText(/Chưa có món nào/)).toBeInTheDocument();
  });

  it("asks for a table before sending a dine-in order", async () => {
    stubByPath(menu);
    render(<OrderScreen />);

    fireEvent.click(await screen.findByRole("button", { name: /Phở bò/ }));
    fireEvent.click(screen.getByRole("button", { name: "Gửi order" }));

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Chọn bàn trước khi gửi order.",
    );
    expect(fetchMock).not.toHaveBeenCalledWith(
      "/sales/orders",
      expect.anything(),
    );
  });
});
