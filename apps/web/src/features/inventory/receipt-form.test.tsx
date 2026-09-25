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

describe("ReceiptForm", () => {
  beforeEach(() => vi.resetAllMocks());

  it("totals quantity x conversion factor x unit price live", async () => {
    render(
      <ReceiptForm
        ingredients={ingredients}
        suppliers={suppliers}
        prefillIngredientId={1}
        onCreated={vi.fn()}
      />,
    );

    fireEvent.change(screen.getByLabelText("Hệ số quy đổi"), {
      target: { value: "5" },
    });
    fireEvent.change(screen.getByLabelText("Số lượng"), {
      target: { value: "3" },
    });
    fireEvent.change(screen.getByLabelText("Đơn giá"), {
      target: { value: "20000" },
    });

    // 3 x 5 x 20000 = 300000
    expect(await screen.findByText("300.000 ₫")).toBeInTheDocument();
  });

  it("posts the converted line to the API on submit", async () => {
    fetchMock.mockResolvedValue({ MaPhieuNhap: 7 });
    const onCreated = vi.fn();
    render(
      <ReceiptForm
        ingredients={ingredients}
        suppliers={suppliers}
        prefillIngredientId={1}
        onCreated={onCreated}
      />,
    );

    fireEvent.change(screen.getByLabelText("Đơn vị mua"), {
      target: { value: "bao" },
    });
    fireEvent.change(screen.getByLabelText("Hệ số quy đổi"), {
      target: { value: "5" },
    });
    fireEvent.change(screen.getByLabelText("Số lượng"), {
      target: { value: "3" },
    });
    fireEvent.change(screen.getByLabelText("Đơn giá"), {
      target: { value: "20000" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Tạo phiếu nhập" }));

    await screen.findByRole("button", { name: "Tạo phiếu nhập" });
    expect(fetchMock).toHaveBeenCalledWith(
      "/inventory/receipts",
      expect.objectContaining({
        method: "POST",
        body: {
          supplier_id: null,
          lines: [
            {
              ingredient_id: 1,
              quantity: 3,
              unit_price: 20000,
              purchase_unit: "bao",
              conversion_factor: 5,
            },
          ],
        },
      }),
    );
    expect(onCreated).toHaveBeenCalled();
  });

  it("blocks submit when quantity is missing", async () => {
    render(
      <ReceiptForm
        ingredients={ingredients}
        suppliers={suppliers}
        prefillIngredientId={1}
        onCreated={vi.fn()}
      />,
    );

    fireEvent.change(screen.getByLabelText("Đơn giá"), {
      target: { value: "1000" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Tạo phiếu nhập" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Số lượng phải lớn hơn 0.",
    );
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
