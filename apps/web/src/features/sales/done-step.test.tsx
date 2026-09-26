import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { DoneStep } from "./done-step";

describe("DoneStep", () => {
  it("shows the invoice, the change and goes back to the floor", async () => {
    (apiFetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      SoHoaDon: "88", TongTien: 340000, PhuongThucThanhToan: "Tiền mặt", SoLanIn: 1, lines: [],
    });
    const onFinish = vi.fn();
    render(<DoneStep orderId={1} change={160000} onFinish={onFinish} />);

    expect(await screen.findByText("88")).toBeInTheDocument();
    expect(screen.getByText("160.000 ₫")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Về sơ đồ bàn" }));
    expect(onFinish).toHaveBeenCalled();
  });
});
