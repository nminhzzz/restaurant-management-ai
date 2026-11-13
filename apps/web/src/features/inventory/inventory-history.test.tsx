import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { InventoryHistory } from "./inventory-history";

vi.mock("@/lib/api-client", () => ({ apiFetch: vi.fn() }));
import { apiFetch } from "@/lib/api-client";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

afterEach(cleanup);

describe("inventory history", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("shows lot receipt and expiry dates as dd/mm/yyyy, not raw ISO (PH-06)", async () => {
    fetchMock.mockResolvedValue({
      items: [
        {
          MaLoNguyenLieu: 7,
          MaNguyenLieu: 1,
          TenNguyenLieu: "Thịt bò",
          DonViTinh: "kg",
          NgayNhap: "2026-11-10T18:57:13.171000",
          HanSuDung: "2026-11-13",
          SoLuongConLai: 5,
          SoLuongGiu: 0,
          SoLuongKhaDung: 5,
          TrangThai: "Còn hạn",
        },
      ],
      total: 1,
    });

    render(<InventoryHistory ingredientId={1} />);

    expect(await screen.findByText(/10\/11\/2026/)).toBeInTheDocument();
    expect(screen.getByText("13/11/2026")).toBeInTheDocument();
    expect(screen.queryByText(/2026-11-10T/)).not.toBeInTheDocument();
  });
});
