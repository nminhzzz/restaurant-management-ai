import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";

import { OrderLookupDialog } from "./order-lookup";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

describe("OrderLookupDialog", () => {
  it("searches by table and Business Date range, then opens the chosen order", async () => {
    fetchMock.mockResolvedValue({
      items: [
        {
          MaOrder: 7,
          MaOrderHienThi: "ORD-7",
          MaBan: 2,
          BusinessDate: "2026-10-20",
          TrangThai: "Đang mở",
        },
      ],
    });
    const onOpenOrder = vi.fn();
    render(
      <OrderLookupDialog
        open
        onOpenChange={() => {}}
        tables={[
          { MaBan: 2, TenBan: "Bàn 2", TrangThai: "Đang phục vụ", order: null },
        ]}
        onOpenOrder={onOpenOrder}
      />,
    );

    Element.prototype.scrollIntoView = vi.fn();
    Element.prototype.hasPointerCapture = vi.fn();
    Element.prototype.releasePointerCapture = vi.fn();

    fireEvent.change(screen.getByLabelText("Từ Business Date"), {
      target: { value: "2026-10-01" },
    });
    fireEvent.change(screen.getByLabelText("Đến Business Date"), {
      target: { value: "2026-10-31" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Tìm kiếm" }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("date_from=2026-10-01"),
      ),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("date_to=2026-10-31"),
    );
    fireEvent.click(await screen.findByRole("button", { name: "Mở" }));
    expect(onOpenOrder).toHaveBeenCalledWith(7, 2);
  });
});
