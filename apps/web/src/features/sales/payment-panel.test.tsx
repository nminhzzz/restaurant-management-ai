import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { clearSession, saveSession } from "@/lib/session";
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
