import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { ReceiptForm } from "./receipt-form";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

const ingredients = [
  { MaNguyenLieu: 1, TenNguyenLieu: "Gạo", DonViTinh: "kg" },
];
const suppliers = [{ MaNhaCungCap: 9, TenNhaCungCap: "NCC A" }];

function renderForm(prefill: number | null = 1, onCreated = vi.fn()) {
  render(
    <ReceiptForm
      ingredients={ingredients}
      suppliers={suppliers}
      prefillIngredientId={prefill}
      onCreated={onCreated}
    />,
  );
  return onCreated;
}

const field = (label: string) =>
  screen.getByLabelText(label) as HTMLInputElement;
const type = (label: string, value: string) =>
  fireEvent.change(screen.getByLabelText(label), { target: { value } });

describe("ReceiptForm", () => {
  beforeEach(() => vi.resetAllMocks());

  it("has no purchase-unit or conversion-factor fields", () => {
    renderForm();
    expect(screen.queryByLabelText("Đơn vị mua")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Hệ số quy đổi")).not.toBeInTheDocument();
  });

  it("uses plain labels before an ingredient is chosen", () => {
    renderForm(null);
    expect(screen.getByLabelText("Số lượng")).toBeInTheDocument();
    expect(screen.getByLabelText("Đơn giá (đ)")).toBeInTheDocument();
  });

  it("uses the ingredient unit in the labels and keeps it out of the option", () => {
    renderForm(1);
    expect(screen.getByLabelText("Số lượng (kg)")).toBeInTheDocument();
    expect(screen.getByLabelText("Đơn giá (đ/kg)")).toBeInTheDocument();
    expect(screen.getByLabelText("Thành tiền (đ)")).toBeInTheDocument();
    expect(screen.queryByText(/Gạo \(kg\)/)).not.toBeInTheDocument();
  });

  it("computes the line total from quantity and unit price", () => {
    renderForm();
    type("Số lượng (kg)", "3");
    type("Đơn giá (đ/kg)", "20000");
    expect(field("Thành tiền (đ)").value).toBe("60000");
    expect(screen.getByText("60.000 ₫")).toBeInTheDocument();
  });

  it("computes the unit price from the line total", () => {
    renderForm();
    type("Số lượng (kg)", "20");
    type("Thành tiền (đ)", "4000000");
    expect(field("Đơn giá (đ/kg)").value).toBe("200000");
  });

  it("rounds the unit price half-up to 2 decimals", () => {
    renderForm();
    type("Số lượng (kg)", "1000");
    type("Thành tiền (đ)", "1005");
    // 1005 / 1000 = 1.005 -> 1.01; float Math.round(100.49999..) would give 1
    expect(field("Đơn giá (đ/kg)").value).toBe("1.01");
  });

  it("recomputes the field the user did not edit last when quantity changes", () => {
    renderForm();
    type("Số lượng (kg)", "2");
    type("Đơn giá (đ/kg)", "100");
    expect(field("Thành tiền (đ)").value).toBe("200");
    type("Số lượng (kg)", "5");
    expect(field("Thành tiền (đ)").value).toBe("500");

    type("Thành tiền (đ)", "1000");
    expect(field("Đơn giá (đ/kg)").value).toBe("200");
    type("Số lượng (kg)", "4");
    expect(field("Đơn giá (đ/kg)").value).toBe("250");
    expect(field("Thành tiền (đ)").value).toBe("1000");
  });

  it("posts the unit price derived from the total, without purchase_unit", async () => {
    fetchMock.mockResolvedValue({ MaPhieuNhap: 7 });
    const onCreated = renderForm();

    type("Số lượng (kg)", "20");
    type("Thành tiền (đ)", "4000000");
    fireEvent.click(screen.getByRole("button", { name: "Tạo phiếu nhập" }));

    await screen.findByRole("button", { name: "Tạo phiếu nhập" });
    expect(fetchMock).toHaveBeenCalledWith(
      "/inventory/receipts",
      expect.objectContaining({
        method: "POST",
        body: expect.objectContaining({
          supplier_id: null,
          receipt_date: expect.stringMatching(/T00:00:00$/),
          lines: [{ ingredient_id: 1, quantity: 20, unit_price: 200000 }],
        }),
      }),
    );
    expect(onCreated).toHaveBeenCalled();
  });

  it("never shows NaN when the total is typed before the quantity, and blocks submit", async () => {
    renderForm();
    type("Thành tiền (đ)", "4000000");
    expect(field("Đơn giá (đ/kg)").value).toBe("");

    fireEvent.click(screen.getByRole("button", { name: "Tạo phiếu nhập" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Số lượng phải lớn hơn 0.",
    );
    expect(fetchMock).not.toHaveBeenCalled();

    type("Số lượng (kg)", "0");
    expect(field("Đơn giá (đ/kg)").value).toBe("");
  });

  it("blocks submit when quantity is missing", async () => {
    renderForm();
    type("Đơn giá (đ/kg)", "1000");
    fireEvent.click(screen.getByRole("button", { name: "Tạo phiếu nhập" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Số lượng phải lớn hơn 0.",
    );
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
