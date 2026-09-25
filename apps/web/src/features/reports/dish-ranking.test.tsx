import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { DishRanking } from "./dish-ranking";
import { stubFetch } from "./test-helpers";

const dishRanking = {
  items: [
    { MaMon: 1, TenMon: "Phở bò", SoLuong: 40, DoanhThu: "4000000" },
    { MaMon: 2, TenMon: "Bún chả", SoLuong: 10, DoanhThu: "1000000" },
  ],
};

describe("DishRanking", () => {
  it("renders both a table and a chart", async () => {
    stubFetch(dishRanking);

    render(<DishRanking />);

    expect(await screen.findAllByText("Phở bò")).not.toHaveLength(0);
    expect(screen.getAllByRole("table").length).toBeGreaterThan(0);
    expect(screen.getAllByRole("img").length).toBeGreaterThan(0);
  });

  it("shows the empty state when no dish sold in the period", async () => {
    stubFetch({ items: [] });

    render(<DishRanking />);

    expect(
      await screen.findByText(/Chưa có món nào được bán trong kỳ/),
    ).toBeInTheDocument();
  });
});
