import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
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
      await screen.findByText(/Không có order nào bị hủy trong kỳ/),
    ).toBeInTheDocument();
  });

  it("loads the report by day, week or month", async () => {
    stubFetch(cancelled);
    render(<CancelledReport />);
    await screen.findAllByText("Khách đổi ý");

    expect(apiFetch).toHaveBeenLastCalledWith(
      expect.stringMatching(/granularity=month&month=\d{4}-\d{2}$/),
    );
    fireEvent.click(screen.getByRole("button", { name: "Tuần" }));
    await vi.waitFor(() =>
      expect(apiFetch).toHaveBeenLastCalledWith(
        expect.stringMatching(/granularity=week&anchor=\d{4}-\d{2}-\d{2}$/),
      ),
    );
    expect(screen.queryByRole("button", { name: "Năm" })).toBeNull();
  });

  it("shows closed-unpaid orders as a separate group", async () => {
    stubFetch({
      ...cancelled,
      DongChuaThuDuocTien: {
        SoLuong: 1,
        TongSoTienChuaThu: "250000",
        TongGiaVonDaTieuHao: "90000",
        items: [
          {
            MaOrder: 9,
            MaOrderHienThi: "ORD-009",
            SoTienChuaThu: "250000",
            GiaVonDaTieuHao: "90000",
            LyDo: "Khách bỏ đi",
            NguoiDong: 1,
            ThoiDiemDong: "2026-10-12T21:00:00",
          },
        ],
      },
    });
    render(<CancelledReport />);

    const group = await screen.findByRole("region", {
      name: "Order đóng chưa thu được tiền",
    });
    expect(group).toHaveTextContent("ORD-009");
    expect(group).toHaveTextContent("Khách bỏ đi");
    expect(group).toHaveTextContent(/không cộng vào số order hủy/);
  });
});
