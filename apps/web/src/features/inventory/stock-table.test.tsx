import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { StockTable } from "./stock-table";
vi.mock("@/lib/api-client", () => ({
  apiFetch: vi.fn().mockResolvedValue({
    items: [
      { MaNguyenLieu: 1, TenNguyenLieu: "Bột mì", CanhBaoTonThap: false },
    ],
  }),
}));
describe("stock table", () => {
  it("shows loading then table", async () => {
    render(<StockTable />);
    expect(screen.getByText("Đang tải…")).toBeInTheDocument();
    expect(await screen.findByText("Bột mì")).toBeInTheDocument();
  });
});
