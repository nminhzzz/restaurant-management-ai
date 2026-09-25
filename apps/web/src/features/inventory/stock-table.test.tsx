import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, it, expect, vi } from "vitest";
import { StockTable } from "./stock-table";
vi.mock("@/lib/api-client", () => ({
  apiFetch: vi.fn().mockResolvedValue({
    items: [
      {
        MaNguyenLieu: 1,
        TenNguyenLieu: "B\u1ed9t m\u00ec",
        CanhBaoTonThap: false,
      },
      {
        MaNguyenLieu: 2,
        TenNguyenLieu: "\u0110\u01b0\u1eddng",
        CanhBaoTonThap: true,
      },
    ],
  }),
}));
afterEach(cleanup);
describe("stock table", () => {
  it("shows loading then table", async () => {
    render(<StockTable />);
    expect(screen.getByText("\u0110ang t\u1ea3i\u2026")).toBeInTheDocument();
    expect(await screen.findByText("B\u1ed9t m\u00ec")).toBeInTheDocument();
  });
  it("marks low-stock rows with a worded warning badge", async () => {
    render(<StockTable />);
    await screen.findByText("\u0110\u01b0\u1eddng");
    const alertRows = screen.getAllByTestId("alert-row");
    expect(alertRows.length).toBe(1);
    expect(alertRows[0].textContent).toContain("S\u1eafp h\u1ebft");
    const okRows = screen.getAllByTestId("ok-row");
    expect(okRows[0].textContent).not.toContain("S\u1eafp h\u1ebft");
  });
});
