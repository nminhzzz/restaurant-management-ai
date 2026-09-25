import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { MarginReport } from "./margin-report";
import { stubFetchByPath } from "./test-helpers";

const margin = {
  DoanhThu: "10000000",
  GiaVon: "4000000",
  BienLoiNhuanGop: "6000000",
};
const dishCosts = {
  items: [{ MaMon: 1, TenMon: "Phở bò", GiaVon: "2000000" }],
};

describe("MarginReport", () => {
  it("renders both a table and a chart", async () => {
    stubFetchByPath({
      "/reports/margin": margin,
      "/reports/costs/dishes": dishCosts,
      "/reports/costs": {
        NguyenLieu: "3500000",
        HaoHut: "500000",
        TongGiaVon: "4000000",
        TamTinh: false,
        SoDongChuaTinhGiaVon: 0,
      },
    });

    render(<MarginReport />);

    await screen.findAllByText("Phở bò");
    expect(screen.getAllByRole("table").length).toBeGreaterThan(1);
    expect(screen.getAllByRole("img").length).toBeGreaterThan(0);
  });

  // FR-REP-05: a month with uncosted waste lines must be flagged "Tạm tính" in words.
  it("shows a provisional badge and sentence when the month's cost is provisional", async () => {
    stubFetchByPath({
      "/reports/margin": margin,
      "/reports/costs/dishes": dishCosts,
      "/reports/costs": {
        NguyenLieu: "3500000",
        HaoHut: "500000",
        TongGiaVon: "4000000",
        TamTinh: true,
        SoDongChuaTinhGiaVon: 3,
      },
    });

    render(<MarginReport />);

    expect(await screen.findByText("Tạm tính")).toBeInTheDocument();
    expect(screen.getByText(/chưa được tính giá vốn/)).toBeInTheDocument();
  });
});
