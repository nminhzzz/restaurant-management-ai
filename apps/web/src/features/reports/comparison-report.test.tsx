import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { ComparisonReport } from "./comparison-report";
import { stubFetch } from "./test-helpers";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

const comparison = {
  left: { DoanhThu: "1000000", SoDon: 10, GiaVon: "400000" },
  right: { DoanhThu: "1200000", SoDon: 12, GiaVon: "300000" },
  doanh_thu: {
    ChenhLechTuyetDoi: "200000",
    PhanTramChenhLech: "20.00",
    GhiChu: null,
  },
  chi_phi: {
    ChenhLechTuyetDoi: "-100000",
    PhanTramChenhLech: "-25.00",
    GhiChu: null,
  },
  change_percent: "20.00",
};

describe("ComparisonReport", () => {
  it("renders a table, a chart, and both revenue and cost changes", async () => {
    stubFetch(comparison);

    render(<ComparisonReport />);

    expect(await screen.findByRole("table")).toBeInTheDocument();
    expect(screen.getByRole("img")).toBeInTheDocument();
    expect(await screen.findByText(/Tăng 20/)).toBeInTheDocument();
    expect(screen.getByText(/Giảm 25/)).toBeInTheDocument();
  });

  it("shows the server note instead of a percentage when the base is 0", async () => {
    stubFetch({
      ...comparison,
      left: { DoanhThu: "0", SoDon: 0, GiaVon: "0" },
      right: { DoanhThu: "500000", SoDon: 5, GiaVon: "100000" },
      doanh_thu: {
        ChenhLechTuyetDoi: "500000",
        PhanTramChenhLech: null,
        GhiChu: "Không xác định tỷ lệ phần trăm",
      },
      chi_phi: {
        ChenhLechTuyetDoi: "100000",
        PhanTramChenhLech: null,
        GhiChu: "Không xác định tỷ lệ phần trăm",
      },
      change_percent: null,
    });

    render(<ComparisonReport />);

    expect(
      await screen.findAllByText("Không xác định tỷ lệ phần trăm"),
    ).toHaveLength(2);
  });

  it("compares two arbitrary date ranges", async () => {
    stubFetch(comparison);
    render(<ComparisonReport />);
    await screen.findByRole("table");

    fireEvent.change(screen.getByLabelText("Kỳ gốc: kiểu kỳ"), {
      target: { value: "range" },
    });
    fireEvent.change(screen.getByLabelText("Kỳ gốc: từ ngày"), {
      target: { value: "2026-09-01" },
    });
    fireEvent.change(screen.getByLabelText("Kỳ gốc: đến ngày"), {
      target: { value: "2026-09-07" },
    });

    await vi.waitFor(() =>
      expect(
        fetchMock.mock.calls.some(([path]) =>
          String(path).includes(
            `left=${encodeURIComponent("2026-09-01..2026-09-07")}`,
          ),
        ),
      ).toBe(true),
    );
  });

  it("does not call the API for a range whose end is before its start", async () => {
    stubFetch(comparison);
    render(<ComparisonReport />);
    await screen.findByRole("table");
    fetchMock.mockClear();

    fireEvent.change(screen.getByLabelText("Kỳ gốc: kiểu kỳ"), {
      target: { value: "range" },
    });
    fireEvent.change(screen.getByLabelText("Kỳ gốc: từ ngày"), {
      target: { value: "2026-09-10" },
    });
    fireEvent.change(screen.getByLabelText("Kỳ gốc: đến ngày"), {
      target: { value: "2026-09-01" },
    });

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /ngày bắt đầu không sau ngày kết thúc/,
    );
    expect(
      fetchMock.mock.calls.some(([path]) =>
        String(path).includes(encodeURIComponent("2026-09-10..2026-09-01")),
      ),
    ).toBe(false);
  });
});
