import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { ClosedUnpaidPanel } from "./closed-unpaid-panel";
import { stubFetch } from "./test-helpers";

const closed = {
  SoLuong: 1,
  TongGiaTri: "120000",
  TongGiaVon: "40000",
  items: [
    {
      MaOrder: 7,
      MaOrderHienThi: "ORD-007",
      TongTien: "120000",
      GiaVon: "40000",
      LyDo: "khách hết tiền",
      NguoiDong: "Quản lý",
      ThoiDiemDong: "2026-10-20T18:00:00",
    },
  ],
};

describe("ClosedUnpaidPanel", () => {
  it("shows the amount, cost, reason and who closed the order", async () => {
    stubFetch(closed);

    render(<ClosedUnpaidPanel granularity="month" anchor="2026-10-20" />);

    expect(await screen.findByText("ORD-007")).toBeInTheDocument();
    expect(screen.getByText("khách hết tiền")).toBeInTheDocument();
    expect(screen.getByText("Quản lý")).toBeInTheDocument();
    expect(screen.getByText(/20\/10\/2026/)).toBeInTheDocument();
  });

  it("shows the empty state when nothing is closed unpaid", async () => {
    stubFetch({ SoLuong: 0, TongGiaTri: "0", TongGiaVon: "0", items: [] });

    render(<ClosedUnpaidPanel granularity="month" anchor="2026-10-20" />);

    expect(
      await screen.findByText(/Không có order đóng chưa thu tiền/),
    ).toBeInTheDocument();
  });
});
