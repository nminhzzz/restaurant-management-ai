import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import type { Ingredient, RecipeVersion } from "@/features/catalog/types";
import { RecipeEditor } from "./recipe-editor";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

const ingredients = [
  { MaNguyenLieu: 1, TenNguyenLieu: "Thịt bò", DonViTinh: "g" },
  { MaNguyenLieu: 2, TenNguyenLieu: "Hành lá", DonViTinh: "g" },
] as unknown as Ingredient[];

const current: RecipeVersion = {
  MaCongThuc: 7,
  MaMon: 3,
  BusinessDateApDung: "2026-11-01",
  TrangThai: "Đang áp dụng",
  LoaiThayDoi: "Tạo mới",
  items: [
    { MaNguyenLieu: 1, TenNguyenLieu: "Thịt bò", SoLuong: 150, DonViTinh: "g" },
    { MaNguyenLieu: 2, TenNguyenLieu: "Hành lá", SoLuong: 10, DonViTinh: "g" },
  ],
};

function renderEditor(currentRecipe: RecipeVersion | null) {
  const onChanged = vi.fn();
  render(
    <RecipeEditor
      dishId={3}
      ingredients={ingredients}
      canWrite
      currentRecipe={currentRecipe}
      pendingRecipe={null}
      history={[]}
      onChanged={onChanged}
    />,
  );
  return onChanged;
}

describe("RecipeEditor", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("has no separate first-assignment button", () => {
    renderEditor(current);
    expect(
      screen.queryByRole("button", { name: /Gán công thức lần đầu/ }),
    ).toBeNull();
  });

  it("prefills the current recipe, shows units and saves an edited copy", async () => {
    fetchMock.mockResolvedValue({});
    const onChanged = renderEditor(current);
    fireEvent.click(screen.getByRole("button", { name: "Sửa công thức" }));

    const quantities = screen.getAllByRole("spinbutton", { name: "Số lượng" });
    expect(quantities.map((q) => (q as HTMLInputElement).value)).toEqual([
      "150",
      "10",
    ]);
    expect(screen.getAllByText("g").length).toBeGreaterThanOrEqual(2);

    fireEvent.change(quantities[0], { target: { value: "180" } });
    fireEvent.click(screen.getByRole("button", { name: "Áp dụng ngay" }));

    await waitFor(() => expect(onChanged).toHaveBeenCalled());
    expect(fetchMock).toHaveBeenCalledWith(
      "/catalog/dishes/3/recipes/apply-now",
      {
        method: "POST",
        body: {
          items: [
            { MaNguyenLieu: 1, SoLuong: 180 },
            { MaNguyenLieu: 2, SoLuong: 10 },
          ],
        },
      },
    );
  });

  it("starts empty for a dish without a recipe and offers no scheduling", () => {
    renderEditor(null);
    fireEvent.click(screen.getByRole("button", { name: "Thêm công thức" }));
    expect(
      (screen.getByRole("spinbutton", { name: "Số lượng" }) as HTMLInputElement)
        .value,
    ).toBe("");
    expect(
      screen.queryByRole("button", { name: "Lên lịch thay đổi" }),
    ).toBeNull();
    expect(screen.getByRole("button", { name: "Áp dụng ngay" })).toBeDisabled();
  });

  it("blocks saving when the same ingredient is chosen twice", () => {
    renderEditor(current);
    fireEvent.click(screen.getByRole("button", { name: "Sửa công thức" }));
    const selects = screen.getAllByRole("combobox", { name: "Nguyên liệu" });
    fireEvent.change(selects[1], { target: { value: "1" } });
    expect(screen.getByRole("alert")).toHaveTextContent(/hai lần/);
    expect(screen.getByRole("button", { name: "Áp dụng ngay" })).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Lên lịch thay đổi" }),
    ).toBeDisabled();
  });

  it("blocks saving a zero or empty quantity", () => {
    renderEditor(current);
    fireEvent.click(screen.getByRole("button", { name: "Sửa công thức" }));
    const quantities = screen.getAllByRole("spinbutton", { name: "Số lượng" });
    fireEvent.change(quantities[0], { target: { value: "0" } });
    expect(screen.getByRole("alert")).toHaveTextContent(/lớn hơn 0/);
    expect(screen.getByRole("button", { name: "Áp dụng ngay" })).toBeDisabled();
  });
});
