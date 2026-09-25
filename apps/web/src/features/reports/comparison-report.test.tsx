import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { ComparisonReport } from "./comparison-report";
import { stubFetch } from "./test-helpers";

describe("ComparisonReport", () => {
  it("renders both a table and a chart, and shows the percentage change", async () => {
    stubFetch({
      left: { DoanhThu: "1000000", SoDon: 10 },
      right: { DoanhThu: "1200000", SoDon: 12 },
      change_percent: "20.00",
    });

    render(<ComparisonReport />);

    expect(await screen.findByRole("table")).toBeInTheDocument();
    expect(screen.getByRole("img")).toBeInTheDocument();
    expect(await screen.findByText(/Tăng 20/)).toBeInTheDocument();
  });

  it("handles a zero baseline period without dividing by zero", async () => {
    stubFetch({
      left: { DoanhThu: "0", SoDon: 0 },
      right: { DoanhThu: "500000", SoDon: 5 },
      change_percent: null,
    });

    render(<ComparisonReport />);

    expect(
      await screen.findByText(/Không có kỳ gốc để so sánh/),
    ).toBeInTheDocument();
  });
});
