import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { CancelledReport } from "./cancelled-report";
import { stubFetch } from "./test-helpers";

const cancelled = {
  SoLuong: 2,
  TongGiaTri: "300000",
  items: [
    {
      MaOrder: 1,
      MaOrderHienThi: "ORD-001",
      TongTien: "200000",
      LyDoHuy: "Khách đổi ý",
    },
    {
      MaOrder: 2,
      MaOrderHienThi: "ORD-002",
      TongTien: "100000",
      LyDoHuy: "Khách đổi ý",
    },
  ],
};

describe("CancelledReport", () => {
  it("renders both a table and a chart, and lists cancellation reasons", async () => {
    stubFetch(cancelled);

    render(<CancelledReport />);

    expect(await screen.findAllByText("Khách đổi ý")).not.toHaveLength(0);
    expect(screen.getAllByRole("table").length).toBeGreaterThan(0);
    expect(screen.getAllByRole("img").length).toBeGreaterThan(0);
  });

  it("shows the empty state when nothing was cancelled in the month", async () => {
    stubFetch({ SoLuong: 0, TongGiaTri: "0", items: [] });

    render(<CancelledReport />);

    expect(
      await screen.findByText(/Không có order nào bị hủy trong tháng/),
    ).toBeInTheDocument();
  });
});
