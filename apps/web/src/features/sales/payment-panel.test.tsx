import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { ApiError, apiFetch } from "@/lib/api-client";
import { clearSession, saveSession } from "@/lib/session";
import { PaymentPanel } from "./payment-panel";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

type Handler = (path: string, options?: { body?: unknown }) => unknown;

/** Route the mocked apiFetch by path prefix; the first matching prefix wins. */
function stubByPath(routes: Record<string, unknown>) {
  const entries = Object.entries(routes);
  fetchMock.mockImplementation((path: string, options?: { body?: unknown }) => {
    const match = entries.find(([prefix]) => path.startsWith(prefix))?.[1];
    if (typeof match === "function")
      return Promise.resolve().then(() => (match as Handler)(path, options));
    return Promise.resolve(match ?? {});
  });
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
  DaKhoa: false,
  lines: [],
};

const waitingOrder = {
  ...openOrder,
  TrangThai: "Chờ xác nhận thanh toán",
  DaKhoa: true,
};

const verifyingOrder = {
  ...openOrder,
  TrangThai: "Chờ xác minh thanh toán",
  DaKhoa: true,
};

const verifyingPayment = qr({
  TrangThai: "Chờ xác minh thanh toán",
  MaGiaoDichNganHang: "FT123",
});

/** A server whose order and payment list change when the cashier starts a QR. */
function qrServer(order: Record<string, unknown>) {
  const state = { order, payments: [] as unknown[] };
  stubByPath({
    "/sales/orders/1/pay/qr": () => {
      state.order = waitingOrder;
      state.payments = [qr()];
      return qr();
    },
    "/sales/orders/1/payments": () => ({ items: state.payments }),
    "/sales/orders/1": () => state.order,
  });
  return state;
}

async function chooseQr() {
  fireEvent.click(
    await screen.findByRole("radio", { name: /QR chuyển khoản/ }),
  );
  fireEvent.click(screen.getByRole("button", { name: "Tạo mã QR" }));
}

describe("PaymentPanel", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    clearSession();
  });

  it("locks the order and blocks a second QR once a QR is live", async () => {
    const onOrderChanged = vi.fn();
    qrServer(openOrder);
    render(<PaymentPanel orderId={1} onOrderChanged={onOrderChanged} />);

    await chooseQr();

    await screen.findByText("Chờ xác nhận");
    expect(screen.getByText("Tạo mã QR mới")).toBeDisabled();
    expect(screen.getByText(/Order đã khóa/)).toBeInTheDocument();
    expect(onOrderChanged).toHaveBeenCalled();
  });

  it("counts the QR deadline down and shows an expiry state", async () => {
    vi.useFakeTimers();
    try {
      stubByPath({
        "/sales/orders/1/payments": { items: [qr()] },
        "/sales/orders/1": waitingOrder,
      });
      render(<PaymentPanel orderId={1} />);
      await act(async () => {});

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

  it("cancels the whole order with the reason and the guests-left flag", async () => {
    saveSession({ token: "t", role: "MANAGER", username: "quanly" });
    stubByPath({ "/sales/orders/1": openOrder });
    render(<PaymentPanel orderId={1} />);

    fireEvent.change(await screen.findByLabelText("Lý do hủy order"), {
      target: { value: "khách đổi ý" },
    });
    fireEvent.click(screen.getByLabelText("Khách đã rời đi"));
    fireEvent.click(screen.getByText("Hủy toàn bộ order"));

    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/sales/orders/1/cancel",
        expect.objectContaining({
          body: { LyDoHuy: "khách đổi ý", KhachDaRoiDi: true },
        }),
      ),
    );
  });

  it("hides the full-order cancellation while a QR transaction is live", async () => {
    saveSession({ token: "t", role: "MANAGER", username: "quanly" });
    stubByPath({
      "/sales/orders/1/payments": { items: [qr()] },
      "/sales/orders/1": waitingOrder,
    });
    render(<PaymentPanel orderId={1} />);

    await screen.findByText("ORD-1");
    expect(screen.queryByText("Hủy toàn bộ order")).not.toBeInTheDocument();
  });

  it("surfaces the server message when cash is refused while a QR is live", async () => {
    stubByPath({
      "/sales/orders/1/pay/cash": () =>
        Promise.reject(
          new ApiError(
            409,
            "BUSINESS_RULE",
            "Hãy hủy mã QR đang chờ trước khi thu tiền mặt.",
          ),
        ),
      "/sales/orders/1/payments": { items: [] },
      "/sales/orders/1": {
        ...openOrder,
        lines: [
          {
            MaChiTietOrder: 1,
            MaMon: 5,
            TenMon: "Phở bò",
            SoLuong: 1,
            DonGia: 65000,
            TrangThai: "Chờ làm",
          },
        ],
      },
    });
    render(<PaymentPanel orderId={1} />);

    fireEvent.change(await screen.findByLabelText("Tiền khách đưa"), {
      target: { value: "100000" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Xác nhận đã thu/ }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Hãy hủy mã QR đang chờ trước khi thu tiền mặt.",
    );
  });
});

describe("PaymentPanel verification (FR-SALE-19..23, 35)", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    clearSession();
  });

  it("requires a bank reference or a note before asking for verification", async () => {
    saveSession({ token: "t", role: "CASHIER", username: "thungan01" });
    stubByPath({
      "/sales/payments/1/verification": { MaGiaoDich: 1 },
      "/sales/orders/1/payments": { items: [qr()] },
      "/sales/orders/1": waitingOrder,
    });
    render(<PaymentPanel orderId={1} />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Yêu cầu xác minh" }),
    );
    const submit = screen.getByRole("button", {
      name: "Gửi yêu cầu xác minh",
    });
    expect(submit).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Mã giao dịch ngân hàng"), {
      target: { value: "FT123" },
    });
    expect(submit).not.toBeDisabled();
    fireEvent.click(submit);

    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/sales/payments/1/verification",
        expect.objectContaining({
          method: "POST",
          body: {
            MaGiaoDichNganHang: "FT123",
            AnhChungTu: undefined,
            GhiChu: undefined,
          },
        }),
      ),
    );
  });

  it("gives a cashier notes and checks but no manager decisions", async () => {
    saveSession({ token: "t", role: "CASHIER", username: "thungan01" });
    stubByPath({
      "/sales/orders/1/payments": { items: [verifyingPayment] },
      "/sales/orders/1": verifyingOrder,
    });
    render(<PaymentPanel orderId={1} />);

    expect(
      await screen.findByText("Đang chờ xác minh thanh toán"),
    ).toBeInTheDocument();
    expect(screen.getByText("FT123")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Thêm ghi chú xác minh" }),
    ).toBeInTheDocument();
    for (const name of [
      "Xác nhận đã nhận tiền",
      "Mở lại thanh toán",
      "Đóng order chưa thu được tiền",
    ]) {
      expect(screen.queryByRole("button", { name })).not.toBeInTheDocument();
    }
  });

  it("saves a verification note", async () => {
    saveSession({ token: "t", role: "CASHIER", username: "thungan01" });
    stubByPath({
      "/sales/payments/1/verification-notes": { MaGiaoDich: 1 },
      "/sales/orders/1/payments": { items: [verifyingPayment] },
      "/sales/orders/1": verifyingOrder,
    });
    render(<PaymentPanel orderId={1} />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Thêm ghi chú xác minh" }),
    );
    fireEvent.change(screen.getByLabelText("Kết quả kiểm tra"), {
      target: { value: "Đã gọi ngân hàng" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Lưu ghi chú" }));

    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/sales/payments/1/verification-notes",
        expect.objectContaining({
          body: expect.objectContaining({ GhiChu: "Đã gọi ngân hàng" }),
        }),
      ),
    );
  });

  it("lets a manager reopen the payment only with a reason and an outcome", async () => {
    saveSession({ token: "t", role: "MANAGER", username: "quanly" });
    stubByPath({
      "/sales/payments/1/reopen": { MaGiaoDich: 1 },
      "/sales/orders/1/payments": { items: [verifyingPayment] },
      "/sales/orders/1": verifyingOrder,
    });
    render(<PaymentPanel orderId={1} />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Mở lại thanh toán" }),
    );
    const submit = screen
      .getAllByRole("button", { name: "Mở lại thanh toán" })
      .at(-1)!;
    expect(submit).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Lý do"), {
      target: { value: "Khách trả lại" },
    });
    expect(submit).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Kết quả xử lý"), {
      target: { value: "Thu lại bằng tiền mặt" },
    });
    fireEvent.click(submit);

    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/sales/payments/1/reopen",
        expect.objectContaining({
          body: { LyDo: "Khách trả lại", KetQuaXuLy: "Thu lại bằng tiền mặt" },
        }),
      ),
    );
  });

  it("shows the server error inside the close-unpaid dialog and keeps it open", async () => {
    saveSession({ token: "t", role: "MANAGER", username: "quanly" });
    stubByPath({
      "/sales/payments/1/close-unpaid": () =>
        Promise.reject(
          new ApiError(
            409,
            "BUSINESS_RULE",
            "Giao dịch không ở trạng thái chờ xác minh thanh toán.",
          ),
        ),
      "/sales/orders/1/payments": { items: [verifyingPayment] },
      "/sales/orders/1": verifyingOrder,
    });
    render(<PaymentPanel orderId={1} />);

    fireEvent.click(
      await screen.findByRole("button", {
        name: "Đóng order chưa thu được tiền",
      }),
    );
    fireEvent.change(screen.getByLabelText("Lý do"), {
      target: { value: "Khách bỏ đi" },
    });
    fireEvent.change(screen.getByLabelText("Kết quả xử lý"), {
      target: { value: "Ghi nợ" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Đóng order" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Giao dịch không ở trạng thái chờ xác minh thanh toán.",
    );
    expect(screen.getByRole("button", { name: "Đóng order" })).toBeEnabled();
  });

  it("confirms received money as a manager", async () => {
    saveSession({ token: "t", role: "MANAGER", username: "quanly" });
    const onPaid = vi.fn();
    stubByPath({
      "/sales/payments/1/confirm-received": { SoHoaDon: "HD-1" },
      "/sales/orders/1/invoice": { SoHoaDon: "HD-1", TongTien: 0, SoLanIn: 0 },
      "/sales/orders/1/payments": { items: [verifyingPayment] },
      "/sales/orders/1": verifyingOrder,
    });
    render(<PaymentPanel orderId={1} onPaid={onPaid} />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Xác nhận đã nhận tiền" }),
    );
    fireEvent.click(
      screen.getAllByRole("button", { name: "Xác nhận đã nhận tiền" }).at(-1)!,
    );

    await vi.waitFor(() =>
      expect(onPaid).toHaveBeenCalledWith({ change: null }),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "/sales/payments/1/confirm-received",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("explains a closed-unpaid order without payment actions", async () => {
    saveSession({ token: "t", role: "MANAGER", username: "quanly" });
    stubByPath({
      "/sales/orders/1/payments": { items: [] },
      "/sales/orders/1": {
        ...openOrder,
        TrangThai: "Đóng – chưa thu được tiền",
        DaKhoa: true,
      },
    });
    render(<PaymentPanel orderId={1} />);

    expect(
      await screen.findByText(/Order đã đóng, chưa thu được tiền/),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("radiogroup", { name: "Phương thức thanh toán" }),
    ).not.toBeInTheDocument();
  });
});

describe("PaymentPanel provisional bill (FR-SALE-21)", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    clearSession();
  });

  const line = {
    MaChiTietOrder: 1,
    MaMon: 5,
    TenMon: "Phở bò",
    SoLuong: 2,
    DonGia: 65000,
    TrangThai: "Chờ làm",
  };

  it("opens the provisional bill for an order with lines", async () => {
    stubByPath({
      "/sales/orders/1/provisional-bill": {
        TieuDe: "PHIẾU TẠM TÍNH - CHƯA THANH TOÁN",
        MaOrderHienThi: "ORD-1",
        TrangThai: "Đang mở",
        ThoiDiemIn: "2026-10-13T10:00:00",
        TongTien: 130000,
        lines: [
          {
            MaMon: 5,
            TenMon: "Phở bò",
            SoLuong: 2,
            DonGia: 65000,
            ThanhTien: 130000,
            GhiChu: null,
          },
        ],
      },
      "/sales/orders/1/payments": { items: [] },
      "/sales/orders/1": { ...openOrder, lines: [line] },
    });
    render(<PaymentPanel orderId={1} />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Phiếu tạm tính" }),
    );

    expect(
      await screen.findByText("PHIẾU TẠM TÍNH - CHƯA THANH TOÁN"),
    ).toBeInTheDocument();
  });

  it("offers no provisional bill for a paid order", async () => {
    stubByPath({
      "/sales/orders/1/payments": { items: [] },
      "/sales/orders/1": {
        ...openOrder,
        TrangThai: "Đã thanh toán",
        DaKhoa: true,
        lines: [line],
      },
    });
    render(<PaymentPanel orderId={1} />);

    await screen.findByText("ORD-1");
    expect(
      screen.queryByRole("button", { name: "Phiếu tạm tính" }),
    ).not.toBeInTheDocument();
  });
});

describe("PaymentPanel cash and SePay", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    clearSession();
  });

  const priced = {
    ...openOrder,
    lines: [
      {
        MaChiTietOrder: 1,
        MaMon: 5,
        TenMon: "Phở bò",
        SoLuong: 2,
        DonGia: 170000,
        TrangThai: "Chờ làm",
      },
    ],
  };

  const qrWithDetails = (overrides: Record<string, unknown> = {}) =>
    qr({
      qr_image_url:
        "https://qr.sepay.vn/img?acc=1&bank=MBBank&amount=340000&des=TT1",
      payment_code: "TT1",
      bank_code: "MBBank",
      bank_account: "0123499999",
      account_name: "NHA HANG DEMO",
      ...overrides,
    });

  it("computes change and only confirms once enough cash is given", async () => {
    const onPaid = vi.fn();
    stubByPath({
      "/sales/orders/1/pay/cash": { MaHoaDon: 9 },
      "/sales/orders/1/invoice": { SoHoaDon: "HD-9", TongTien: 340000 },
      "/sales/orders/1/payments": { items: [] },
      "/sales/orders/1": priced,
    });
    render(<PaymentPanel orderId={1} onPaid={onPaid} />);

    const given = await screen.findByLabelText("Tiền khách đưa");
    fireEvent.change(given, { target: { value: "300000" } });
    expect(
      screen.getByRole("button", { name: /Xác nhận đã thu/ }),
    ).toBeDisabled();

    fireEvent.change(given, { target: { value: "500000" } });
    expect(screen.getByTestId("cash-change")).toHaveTextContent("160.000 ₫");
    fireEvent.click(screen.getByRole("button", { name: /Xác nhận đã thu/ }));

    await vi.waitFor(() =>
      expect(onPaid).toHaveBeenCalledWith({ change: 160000 }),
    );
  });

  it("offers exact and rounded quick amounts", async () => {
    const { quickAmounts } = await import("./payment-panel");
    expect(quickAmounts(340000)).toEqual([340000, 350000, 400000, 500000]);
    expect(quickAmounts(500000)).toEqual([500000]);
  });

  it("shows the VietQR image, bank details and transfer code", async () => {
    stubByPath({
      "/sales/orders/1/payments": { items: [qrWithDetails()] },
      "/sales/orders/1": { ...priced, TrangThai: "Chờ xác nhận thanh toán" },
    });
    render(<PaymentPanel orderId={1} />);

    expect(
      await screen.findByRole("img", { name: /Mã VietQR/ }),
    ).toHaveAttribute("src", expect.stringContaining("qr.sepay.vn"));
    expect(screen.getByText("TT1")).toBeInTheDocument();
    expect(screen.getByText("0123499999")).toBeInTheDocument();
  });

  it("copies the transfer content to the clipboard", async () => {
    stubByPath({
      "/sales/orders/1/payments": { items: [qrWithDetails()] },
      "/sales/orders/1": { ...priced, TrangThai: "Chờ xác nhận thanh toán" },
    });
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText },
      configurable: true,
    });
    render(<PaymentPanel orderId={1} />);

    fireEvent.click(
      await screen.findByRole("button", {
        name: "Sao chép nội dung chuyển khoản",
      }),
    );

    await vi.waitFor(() => expect(writeText).toHaveBeenCalledWith("TT1"));
  });

  it("cancels a live QR so the order can be paid in cash", async () => {
    stubByPath({
      "/sales/payments/1/cancel": { MaGiaoDich: 1, TrangThai: "Đã hủy" },
      "/sales/orders/1/payments": { items: [qr()] },
      "/sales/orders/1": { ...priced, TrangThai: "Chờ xác nhận thanh toán" },
    });
    render(<PaymentPanel orderId={1} />);

    fireEvent.click(await screen.findByRole("button", { name: "Hủy QR" }));

    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/sales/payments/1/cancel",
        expect.objectContaining({ method: "POST" }),
      ),
    );
  });

  it("reports the payment once check-again succeeds", async () => {
    const onPaid = vi.fn();
    stubByPath({
      "/sales/payments/1/check": { MaGiaoDich: 1, TrangThai: "Thành công" },
      "/sales/orders/1/payments": { items: [qr()] },
      "/sales/orders/1": { ...priced, TrangThai: "Chờ xác nhận thanh toán" },
    });
    render(<PaymentPanel orderId={1} onPaid={onPaid} />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Kiểm tra lại" }),
    );

    await vi.waitFor(() =>
      expect(onPaid).toHaveBeenCalledWith({ change: null }),
    );
  });

  it("shows a status message when check-again still finds nothing", async () => {
    const onPaid = vi.fn();
    stubByPath({
      "/sales/payments/1/check": { MaGiaoDich: 1, TrangThai: "Chờ xác nhận" },
      "/sales/orders/1/payments": { items: [qr()] },
      "/sales/orders/1": { ...priced, TrangThai: "Chờ xác nhận thanh toán" },
    });
    render(<PaymentPanel orderId={1} onPaid={onPaid} />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Kiểm tra lại" }),
    );

    expect(
      await screen.findByText(
        "Chưa thấy giao dịch. Chờ thêm hoặc kiểm tra lại sau.",
      ),
    ).toBeInTheDocument();
    expect(onPaid).not.toHaveBeenCalled();
  });

  it("locks the cash tab while a QR transaction is live", async () => {
    stubByPath({
      "/sales/orders/1/payments": { items: [qr()] },
      "/sales/orders/1": { ...priced, TrangThai: "Chờ xác nhận thanh toán" },
    });
    render(<PaymentPanel orderId={1} />);

    expect(
      await screen.findByRole("radio", { name: /Tiền mặt/ }),
    ).toBeDisabled();
    expect(
      screen.getByText("Đang có giao dịch QR. Hủy QR để chuyển sang tiền mặt."),
    ).toBeInTheDocument();
  });

  it("unlocks the cash tab once the QR has expired", async () => {
    stubByPath({
      "/sales/orders/1/payments": { items: [qr({ TrangThai: "Hết hạn" })] },
      "/sales/orders/1": priced,
    });
    render(<PaymentPanel orderId={1} />);

    expect(
      await screen.findByRole("radio", { name: /Tiền mặt/ }),
    ).not.toBeDisabled();
  });

  it("reloads the order once polling sees the QR move to verification", async () => {
    vi.useFakeTimers();
    try {
      saveSession({ token: "t", role: "MANAGER", username: "quanly" });
      let moved = false;
      let orderCalls = 0;
      fetchMock.mockImplementation((path: string) => {
        if (path.startsWith("/sales/orders/1/payments"))
          return Promise.resolve({
            items: [moved ? verifyingPayment : qr()],
          });
        if (path.startsWith("/sales/orders/1")) {
          orderCalls += 1;
          return Promise.resolve(moved ? verifyingOrder : waitingOrder);
        }
        return Promise.resolve({});
      });
      render(<PaymentPanel orderId={1} />);
      await act(async () => {});
      const callsBeforePoll = orderCalls;
      moved = true;
      await act(async () => {
        vi.advanceTimersByTime(3000);
      });
      await act(async () => {});

      expect(orderCalls).toBeGreaterThan(callsBeforePoll);
      expect(
        screen.getByText("Đang chờ xác minh thanh toán"),
      ).toBeInTheDocument();
    } finally {
      vi.useRealTimers();
    }
  });

  it("reports the payment once polling sees it succeed", async () => {
    vi.useFakeTimers();
    try {
      const onPaid = vi.fn();
      const live = qr();
      let succeeded = false;
      fetchMock.mockImplementation((path: string) => {
        if (path.startsWith("/sales/orders/1/payments"))
          return Promise.resolve({
            items: [succeeded ? { ...live, TrangThai: "Thành công" } : live],
          });
        if (path.startsWith("/sales/orders/1"))
          return Promise.resolve(waitingOrder);
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
