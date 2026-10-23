import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";

import { ReceiptEditDialog } from "./receipt-edit-dialog";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

describe("ReceiptEditDialog", () => {
  it("loads the original lines and patches corrected quantity and price", async () => {
    fetchMock.mockImplementation((path: string, init?: { method?: string }) => {
      if (init?.method === "PATCH") return Promise.resolve({ ok: true });
      return Promise.resolve({
        MaPhieuNhap: 3,
        MaNhaCungCap: null,
        NgayNhap: "2026-10-20T00:00:00",
        TrangThai: "Nháp",
        TongTien: 5000,
        lines: [
          {
            MaChiTietNhap: 11,
            MaNguyenLieu: 1,
            TenNguyenLieu: "Gạo",
            DonViTinh: "kg",
            SoLuong: 5,
            DonGia: 1000,
          },
        ],
      });
    });
    const onSaved = vi.fn();

    render(
      <ReceiptEditDialog receiptId={3} onClose={() => {}} onSaved={onSaved} />,
    );

    fireEvent.change(await screen.findByLabelText("Số lượng Gạo"), {
      target: { value: "9" },
    });
    fireEvent.change(screen.getByLabelText("Đơn giá Gạo"), {
      target: { value: "1200" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Lưu thay đổi" }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/inventory/receipts/3",
        expect.objectContaining({
          method: "PATCH",
          body: { lines: [{ line_id: 11, quantity: 9, unit_price: 1200 }] },
        }),
      ),
    );
    expect(onSaved).toHaveBeenCalled();
  });
});
