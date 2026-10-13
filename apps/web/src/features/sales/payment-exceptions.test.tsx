import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { ApiError, apiFetch } from "@/lib/api-client";
import { PaymentExceptions } from "./payment-exceptions";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

function entry(overrides: Record<string, unknown> = {}) {
  return {
    MaGiaoDich: 7,
    MaOrder: 3,
    MaOrderHienThi: "ORD-3",
    TrangThaiOrder: "Đóng – chưa thu được tiền",
    TongTienOrder: 340000,
    SoTienNgoaiLe: 340000,
    MaGiaoDichCong: "GW-99",
    MaGiaoDichNganHang: null,
    TrangThaiNgoaiLe: "Chờ xử lý",
    MaThamChieuHoan: null,
    ThoiDiemNhan: "2026-10-13T09:00:00",
    ThoiDiemXuLy: null,
    NguoiXuLy: null,
    CoTheApDung: true,
    ...overrides,
  };
}

describe("PaymentExceptions", () => {
  beforeEach(() => vi.resetAllMocks());
  afterEach(cleanup);

  it("lists pending exceptions with amount and gateway id", async () => {
    fetchMock.mockResolvedValue({ items: [entry()] });
    render(<PaymentExceptions />);

    expect(await screen.findByText("ORD-3")).toBeInTheDocument();
    expect(screen.getByText("GW-99")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/sales/payment-exceptions?status=Ch%E1%BB%9D%20x%E1%BB%AD%20l%C3%BD",
    );
  });

  it("disables apply when the amount no longer matches", async () => {
    fetchMock.mockResolvedValue({
      items: [entry({ CoTheApDung: false, SoTienNgoaiLe: 100000 })],
    });
    render(<PaymentExceptions />);

    expect(
      await screen.findByRole("button", { name: /Áp dụng khoản 7/ }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: /Ghi nhận hoàn tiền khoản 7/ }),
    ).toBeEnabled();
  });

  it("applies an exception after confirmation", async () => {
    fetchMock.mockImplementation((path: string) =>
      Promise.resolve(
        path.startsWith("/sales/payment-exceptions?")
          ? { items: [entry()] }
          : { MaGiaoDich: 7 },
      ),
    );
    render(<PaymentExceptions />);

    fireEvent.click(
      await screen.findByRole("button", { name: /Áp dụng khoản 7/ }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Áp dụng" }));

    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/sales/payment-exceptions/7/apply",
        expect.objectContaining({ method: "POST" }),
      ),
    );
  });

  it("records a refund only with a reference", async () => {
    fetchMock.mockImplementation((path: string) =>
      Promise.resolve(
        path.startsWith("/sales/payment-exceptions?")
          ? { items: [entry({ CoTheApDung: false })] }
          : { MaGiaoDich: 7 },
      ),
    );
    render(<PaymentExceptions />);

    fireEvent.click(
      await screen.findByRole("button", { name: /Ghi nhận hoàn tiền khoản 7/ }),
    );
    const submit = screen
      .getAllByRole("button", { name: "Ghi nhận hoàn tiền" })
      .at(-1)!;
    expect(submit).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Mã tham chiếu hoàn tiền"), {
      target: { value: "RF-1" },
    });
    fireEvent.click(submit);

    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/sales/payment-exceptions/7/refund",
        expect.objectContaining({ body: { MaThamChieuHoan: "RF-1" } }),
      ),
    );
  });

  it("shows the server message when the apply is refused", async () => {
    fetchMock.mockImplementation((path: string) =>
      path.startsWith("/sales/payment-exceptions?")
        ? Promise.resolve({ items: [entry()] })
        : Promise.reject(
            new ApiError(
              409,
              "BUSINESS_RULE",
              "Khoản ngoại lệ này đã được xử lý.",
            ),
          ),
    );
    render(<PaymentExceptions />);

    fireEvent.click(
      await screen.findByRole("button", { name: /Áp dụng khoản 7/ }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Áp dụng" }));

    expect(
      await screen.findByText("Khoản ngoại lệ này đã được xử lý."),
    ).toBeInTheDocument();
  });

  it("offers no actions on a handled exception and shows the empty state", async () => {
    fetchMock.mockResolvedValueOnce({
      items: [
        entry({
          TrangThaiNgoaiLe: "Đã hoàn tiền",
          MaThamChieuHoan: "RF-9",
          CoTheApDung: false,
        }),
      ],
    });
    render(<PaymentExceptions />);

    expect(await screen.findByText("RF-9")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Ghi nhận hoàn tiền khoản/ }),
    ).toBeNull();

    fetchMock.mockResolvedValue({ items: [] });
    fireEvent.change(screen.getByLabelText("Trạng thái ngoại lệ"), {
      target: { value: "Đã áp dụng cho order" },
    });
    expect(
      await screen.findByText("Không có khoản ngoại lệ nào"),
    ).toBeInTheDocument();
  });
});
