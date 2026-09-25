import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
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

  it("closes the month's costing only after confirmation, then reloads", async () => {
    stubFetchByPath({
      "/reports/margin": margin,
      "/reports/costs/dishes": dishCosts,
      "/reports/costs": {
        NguyenLieu: "3500000",
        HaoHut: "0",
        TongGiaVon: "3500000",
        TamTinh: true,
        SoDongChuaTinhGiaVon: 2,
      },
      "/inventory/costing": [],
    });
    const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;
    render(<MarginReport />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Chốt giá vốn tháng" }),
    );
    expect(fetchMock).not.toHaveBeenCalledWith(
      expect.stringContaining("/inventory/costing/"),
      expect.anything(),
    );
    fireEvent.click(screen.getByRole("button", { name: "Chốt giá vốn" }));

    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringMatching(/^\/inventory\/costing\/\d{6}\/close$/),
        expect.objectContaining({ method: "POST" }),
      ),
    );
  });
});
