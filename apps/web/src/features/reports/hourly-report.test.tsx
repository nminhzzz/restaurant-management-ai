import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { HourlyReport } from "./hourly-report";
import { stubFetch } from "./test-helpers";

const hourly = {
  items: [
    { ThoiDiem: 12, SoDon: 5, DoanhThu: "500000" },
    { ThoiDiem: 19, SoDon: 8, DoanhThu: "800000" },
  ],
  by_weekday: [
    { Thu: 1, SoDon: 3, DoanhThu: "300000" },
    { Thu: 6, SoDon: 9, DoanhThu: "900000" },
  ],
};

describe("HourlyReport", () => {
  it("renders both a table and charts for the hour and weekday distribution", async () => {
    stubFetch(hourly);

    render(<HourlyReport />);

    expect((await screen.findAllByRole("table")).length).toBe(2);
    expect(screen.getAllByRole("img").length).toBe(3);
  });

  it("pages the 24-hour detail table at 10 rows per page", async () => {
    stubFetch(hourly);

    render(<HourlyReport />);
    const table = (await screen.findAllByRole("table"))[0];

    expect(within(table).getByText("500.000 ₫")).toBeInTheDocument();
    expect(within(table).queryByText("800.000 ₫")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Trang 2" }));

    expect(within(table).getByText("800.000 ₫")).toBeInTheDocument();
    expect(within(table).queryByText("500.000 ₫")).not.toBeInTheDocument();
  });

  it("shows the empty state when the period has no orders", async () => {
    stubFetch({ items: [], by_weekday: [] });

    render(<HourlyReport />);

    expect(
      await screen.findByText(/Chưa có đơn nào trong kỳ/),
    ).toBeInTheDocument();
  });
});
