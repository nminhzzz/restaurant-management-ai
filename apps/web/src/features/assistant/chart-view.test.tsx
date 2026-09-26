import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ChartView } from "./chart-view";

const timeSeries = [
  { BusinessDate: "2026-09-01", DoanhThu: "100000" },
  { BusinessDate: "2026-09-02", DoanhThu: "120000" },
];

const shares = [
  { TenMon: "Phở bò", TyTrong: "60" },
  { TenMon: "Bún chả", TyTrong: "40" },
];

describe("ChartView", () => {
  it("renders a line chart for a time series", () => {
    render(
      <ChartView
        spec={{ type: "line", x: "BusinessDate", y: ["DoanhThu"] }}
        rows={timeSeries}
      />,
    );

    expect(
      screen.getByRole("img", { name: /biểu đồ đường/i }),
    ).toBeInTheDocument();
  });

  it("renders a doughnut chart for shares", () => {
    render(
      <ChartView
        spec={{ type: "doughnut", x: "TenMon", y: ["TyTrong"] }}
        rows={shares}
      />,
    );

    expect(
      screen.getByRole("img", { name: /biểu đồ tròn/i }),
    ).toBeInTheDocument();
  });

  it("renders no chart when the server sends none", () => {
    const { container } = render(<ChartView spec={null} rows={timeSeries} />);

    expect(container).toBeEmptyDOMElement();
  });
});
