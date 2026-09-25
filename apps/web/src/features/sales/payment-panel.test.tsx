import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";

vi.mock("@/lib/api-client", () => ({ apiFetch: vi.fn() }));
import { apiFetch } from "@/lib/api-client";
import { PaymentPanel } from "./payment-panel";

function qr(overrides: Record<string, unknown> = {}) {
  const now = new Date();
  const end = new Date(now.getTime() + 10 * 60 * 1000);
  return {
    MaGiaoDich: 1,
    TrangThai: "Chờ xác nhận",
    ThoiDiemTaoQR: now.toISOString(),
    ThoiDiemHetHan: end.toISOString(),
    ...overrides,
  };
}

describe("PaymentPanel", () => {
  beforeEach(() => vi.resetAllMocks());

  it("disables creating a new QR while one is still live", async () => {
    (apiFetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(qr());
    render(<PaymentPanel orderId={1} />);
    // after qr created, button disabled
    const btn = await screen.findByText("Thanh toán QR");
    fireEvent.click(btn);
    // need to wait for state
    await screen.findByText("Chờ xác nhận");
    expect(screen.getByText("Tạo mã QR mới")).toBeDisabled();
  });
});

describe("OrderScreen", () => {
  it("hides out of stock dishes", async () => {
    const { OrderScreen } = await import("./order-screen");
    (apiFetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      items: [
        { MaMon: 1, TenMon: "Phở bò", TrangThai: "Hoạt động" },
        { MaMon: 2, TenMon: "Bún chả", TrangThai: "Hết nguyên liệu" },
      ],
    });
    render(<OrderScreen />);
    expect(await screen.findByText("Phở bò")).toBeInTheDocument();
    expect(screen.queryByText("Bún chả")).not.toBeInTheDocument();
  });

  it("only offers full cancel to manager", async () => {
    const { saveSession } = await import("@/lib/session");
    saveSession({
      token: "t",
      role: "CASHIER",
      username: "thungan01",
    } as never);
    const { OrderScreen } = await import("./order-screen");
    (apiFetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      items: [],
    });
    render(<OrderScreen />);
    // need to wait loading done
    await screen.findByText("Gọi món");
    expect(screen.queryByText("Hủy toàn bộ order")).not.toBeInTheDocument();
  });
});
