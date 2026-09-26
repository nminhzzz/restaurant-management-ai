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

async function chooseQr() {
  fireEvent.click(await screen.findByRole("radio", { name: /QR chuyển khoản/ }));
  fireEvent.click(screen.getByRole("button", { name: "Tạo mã QR" }));
}

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

    await chooseQr();

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

      // Plain (non-`findBy`) queries here: Testing Library's `findBy*`/`waitFor`
      // drain a microtask via a real `setTimeout(0)` that never fires under
      // Vitest's fake timers (RTL only special-cases Jest's), so it would hang.
      // The radio and button are already rendered by this point (order loaded above).
      await act(async () => {
        fireEvent.click(screen.getByRole("radio", { name: /QR chuyển khoản/ }));
        fireEvent.click(screen.getByRole("button", { name: "Tạo mã QR" }));
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

describe("PaymentPanel cash and SePay", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    clearSession();
  });

  const priced = {
    ...openOrder,
    lines: [{ MaChiTietOrder: 1, MaMon: 5, SoLuong: 2, DonGia: 170000, TrangThai: "Chờ" }],
  };

  it("computes change and only confirms once enough cash is given", async () => {
    const onPaid = vi.fn();
    stubByPath({ "/sales/orders/1/pay/cash": { MaHoaDon: 9 }, "/sales/orders/1": priced });
    render(<PaymentPanel orderId={1} onPaid={onPaid} />);

    const given = await screen.findByLabelText("Tiền khách đưa");
    fireEvent.change(given, { target: { value: "300000" } });
    expect(screen.getByRole("button", { name: /Xác nhận đã thu/ })).toBeDisabled();

    fireEvent.change(given, { target: { value: "500000" } });
    expect(screen.getByTestId("cash-change")).toHaveTextContent("160.000 ₫");
    fireEvent.click(screen.getByRole("button", { name: /Xác nhận đã thu/ }));

    await vi.waitFor(() => expect(onPaid).toHaveBeenCalledWith({ change: 160000 }));
  });

  it("offers exact and rounded quick amounts", async () => {
    const { quickAmounts } = await import("./payment-panel");
    expect(quickAmounts(340000)).toEqual([340000, 350000, 400000, 500000]);
    expect(quickAmounts(500000)).toEqual([500000]);
  });

  it("shows the VietQR image, bank details and transfer code", async () => {
    stubByPath({
      "/sales/orders/1/pay/qr": qr({
        qr_image_url: "https://qr.sepay.vn/img?acc=1&bank=MBBank&amount=340000&des=TT1",
        payment_code: "TT1",
        bank_code: "MBBank",
        bank_account: "0123499999",
        account_name: "NHA HANG DEMO",
      }),
      "/sales/orders/1": priced,
    });
    render(<PaymentPanel orderId={1} />);
    await chooseQr();

    expect(await screen.findByRole("img", { name: /Mã VietQR/ })).toHaveAttribute(
      "src",
      expect.stringContaining("qr.sepay.vn"),
    );
    expect(screen.getByText("TT1")).toBeInTheDocument();
    expect(screen.getByText("0123499999")).toBeInTheDocument();
  });

  it("reports the payment once polling sees it succeed", async () => {
    vi.useFakeTimers();
    try {
      const onPaid = vi.fn();
      const live = qr();
      let succeeded = false;
      fetchMock.mockImplementation((path: string) => {
        if (path.startsWith("/sales/orders/1/payments"))
          return Promise.resolve({ items: [succeeded ? { ...live, TrangThai: "Thành công" } : live] });
        if (path.startsWith("/sales/orders/1")) return Promise.resolve(priced);
        return Promise.resolve({});
      });
      render(<PaymentPanel orderId={1} onPaid={onPaid} />);
      await act(async () => {});
      succeeded = true;
      await act(async () => {
        vi.advanceTimersByTime(3000);
      });
      expect(onPaid).toHaveBeenCalledWith({ change: null });
    } finally {
      vi.useRealTimers();
    }
  });
});
