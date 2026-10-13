import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch, ApiError } from "@/lib/api-client";
import { stubFetch } from "./test-helpers";
import { UnsettledReport } from "./unsettled-report";

describe("UnsettledReport", () => {
  it("lists orders waiting for verification with their wait time", async () => {
    stubFetch({
      SoLuong: 1,
      TongGiaTri: "340000",
      items: [
        {
          MaOrder: 4,
          MaOrderHienThi: "ORD-004",
          GiaTriOrder: "340000",
          ThoiDiemBatDauCho: "2026-10-13T09:00:00",
          SoPhutDaCho: 42,
          KetQuaXuLyGanNhat: "Đã gọi ngân hàng",
        },
      ],
    });

    render(<UnsettledReport />);

    expect(await screen.findByText("ORD-004")).toBeInTheDocument();
    expect(screen.getByText("42 phút")).toBeInTheDocument();
    expect(screen.getByText("Đã gọi ngân hàng")).toBeInTheDocument();
  });

  it("shows the empty state when nothing is waiting", async () => {
    stubFetch({ SoLuong: 0, TongGiaTri: "0", items: [] });
    render(<UnsettledReport />);
    expect(
      await screen.findByText("Không có order nào chờ xác minh"),
    ).toBeInTheDocument();
  });

  it("shows the server error and a retry", async () => {
    (apiFetch as unknown as ReturnType<typeof vi.fn>).mockRejectedValue(
      new ApiError(403, "FORBIDDEN", "Bạn không có quyền xem báo cáo này."),
    );
    render(<UnsettledReport />);
    expect(
      await screen.findByText("Bạn không có quyền xem báo cáo này."),
    ).toBeInTheDocument();
  });
});
