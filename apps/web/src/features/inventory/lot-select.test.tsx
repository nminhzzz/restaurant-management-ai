import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { apiFetch } from "@/lib/api-client";
import { LotSelect } from "./lot-select";

vi.mock("@/lib/api-client", () => ({ apiFetch: vi.fn() }));

it("offers actual lots including expired stock for an explicit write-off", async () => {
  vi.mocked(apiFetch).mockResolvedValue({
    items: [
      {
        MaLoNguyenLieu: 24,
        SoLuongConLai: 7,
        SoLuongGiu: 2,
        TrangThai: "Hết hạn",
        HanSuDung: "2026-09-01",
      },
    ],
    total: 1,
  });
  const change = vi.fn();
  render(<LotSelect id="lot" ingredientId="3" value="" onChange={change} />);
  expect(
    await screen.findByRole("option", { name: /#24.*Hết hạn/ }),
  ).toBeInTheDocument();
  fireEvent.change(screen.getByRole("combobox", { name: "Lô nguyên liệu" }), {
    target: { value: "24" },
  });
  expect(change).toHaveBeenCalledWith("24");
});
