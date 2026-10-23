import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";

import { RevenueChart } from "./revenue-chart";
import { revenueResponse, stubFetch } from "./test-helpers";

describe("RevenueChart", () => {
  it("renders both a table and a chart", async () => {
    stubFetch(revenueResponse);

    render(<RevenueChart />);

    expect(await screen.findByRole("table")).toBeInTheDocument();
    expect(
      screen.getByRole("img", { name: /biểu đồ doanh thu/i }),
    ).toBeInTheDocument();
  });

  // FR-REP-02 and FR-REP-05b: a provisional figure must be labelled in words, not only coloured.
  it("labels provisional figures so the manager knows they are not final", async () => {
    stubFetch({ ...revenueResponse, provisional: "500000" });

    render(<RevenueChart />);

    expect(await screen.findByText(/tạm tính/)).toBeInTheDocument();
  });

  // FR-REP-01: revenue must also break down by order type, not only by date/table/method.
  it("breaks revenue down by order type", async () => {
    stubFetch({
      ...revenueResponse,
      items: [
        { key: "Tại chỗ", DoanhThu: "700000", SoDon: 2 },
        { key: "Mang về", DoanhThu: "300000", SoDon: 1 },
      ],
    });

    render(<RevenueChart />);

    fireEvent.click(await screen.findByRole("button", { name: "Loại đơn" }));

    await waitFor(() =>
      expect(apiFetch).toHaveBeenCalledWith(
        expect.stringContaining("group_by=order_type"),
      ),
    );
    expect((await screen.findAllByText("Tại chỗ")).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Mang về").length).toBeGreaterThan(0);
  });

  it("shows the empty state with a hint when the period has no data", async () => {
    stubFetch({ total: "0", items: [], provisional: "0" });

    render(<RevenueChart />);

    expect(
      await screen.findByText(/Chưa có dữ liệu trong kỳ/),
    ).toBeInTheDocument();
  });
});
