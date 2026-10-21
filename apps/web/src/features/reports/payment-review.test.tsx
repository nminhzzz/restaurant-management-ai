import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { PaymentReview } from "./payment-review";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

const pending = {
  items: [
    {
      MaOrder: 5,
      MaOrderHienThi: "ORD-005",
      MaGiaoDich: 12,
      PhuongThuc: "QR",
      SoTien: "50000",
      TrangThai: "Chờ xác minh thanh toán",
      ThoiGianChoPhut: 25,
      KetQuaGanNhat: "FT-1",
    },
  ],
};

const exceptions = {
  items: [
    {
      MaNgoaiLe: 3,
      MaOrder: 6,
      MaOrderHienThi: "ORD-006",
      MaGiaoDich: 14,
      MaGiaoDichCong: "sepay:99",
      SoTien: "50000",
      TrangThai: "Chờ xử lý",
      LyDo: "Số tiền không khớp với order",
      GhiChu: null,
      MaThamChieuHoan: null,
      SoTienHoan: null,
      ThoiDiemTao: "2026-10-20T18:00:00",
      ThoiDiemXuLy: null,
    },
  ],
};

function stub() {
  fetchMock.mockImplementation((path: string) => {
    if (path.startsWith("/reports/pending-payments"))
      return Promise.resolve(pending);
    if (path.startsWith("/sales/payment-exceptions"))
      return Promise.resolve(exceptions);
    return Promise.resolve({});
  });
}

describe("PaymentReview", () => {
  it("lists payments waiting for verification and unmatched transfers", async () => {
    stub();

    render(<PaymentReview />);

    expect(await screen.findByText("ORD-005")).toBeInTheDocument();
    expect(screen.getByText(/25 phút/)).toBeInTheDocument();
    expect(screen.getByText("sepay:99")).toBeInTheDocument();
    expect(
      screen.getByText("Số tiền không khớp với order"),
    ).toBeInTheDocument();
  });

  it("applies an exception through the API and reloads the list", async () => {
    stub();

    render(<PaymentReview />);
    fireEvent.click(await screen.findByRole("button", { name: "Áp dụng" }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/sales/payment-exceptions/3/resolve",
        expect.objectContaining({
          method: "POST",
          body: { outcome: "applied", note: null },
        }),
      ),
    );
    await waitFor(() =>
      expect(
        fetchMock.mock.calls.filter(([path]) =>
          String(path).startsWith("/sales/payment-exceptions"),
        ).length,
      ).toBeGreaterThan(1),
    );
  });

  it("records a refund with its bank reference and amount", async () => {
    stub();
    const prompt = vi
      .spyOn(window, "prompt")
      .mockReturnValueOnce("REF-2026-01")
      .mockReturnValueOnce("30000")
      .mockReturnValueOnce("Khách nhận lại một phần");

    render(<PaymentReview />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Đã hoàn tiền" }),
    );

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/sales/payment-exceptions/3/resolve",
        expect.objectContaining({
          method: "POST",
          body: {
            outcome: "refunded",
            note: "Khách nhận lại một phần",
            refund_ref: "REF-2026-01",
            refund_amount: "30000",
          },
        }),
      ),
    );
    prompt.mockRestore();
  });
});
