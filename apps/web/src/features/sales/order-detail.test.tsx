import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { OrderDetail } from "./order-detail";
import { Toaster } from "sonner";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

function stubByPath(routes: Record<string, unknown>) {
  const entries = Object.entries(routes);
  fetchMock.mockImplementation((path: string) =>
    Promise.resolve(
      entries.find(([prefix]) => path.startsWith(prefix))?.[1] ?? {},
    ),
  );
}

const dishes = {
  items: [{ MaMon: 5, TenMon: "Phở bò", GiaHienTai: 65000 }],
};

const tables = [
  { MaBan: 1, TenBan: "Bàn 1", TrangThai: "Đang phục vụ" },
  { MaBan: 2, TenBan: "Bàn 2", TrangThai: "Trống" },
];

function openOrder(overrides: Record<string, unknown> = {}) {
  return {
    MaOrder: 1,
    MaOrderHienThi: "ORD-1",
    MaBan: 1,
    TrangThai: "Đang mở",
    lines: [
      {
        MaChiTietOrder: 10,
        MaMon: 5,
        SoLuong: 2,
        DonGia: 65000,
        GhiChu: null,
        TrangThai: "Chờ",
      },
    ],
    ...overrides,
  };
}

describe("OrderDetail", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    // jsdom does not implement these; Radix Select calls them when opening.
    Element.prototype.scrollIntoView = vi.fn();
    Element.prototype.hasPointerCapture = vi.fn();
    Element.prototype.releasePointerCapture = vi.fn();
  });

  it("requires a reason to cancel a waiting line", async () => {
    stubByPath({
      "/sales/orders/1/tickets": { items: [] },
      "/sales/orders/1": openOrder(),
      "/catalog/dishes": dishes,
      "/catalog/tables": tables,
    });
    render(<OrderDetail orderId={1} />);

    fireEvent.click(await screen.findByRole("button", { name: "Hủy món" }));
    const confirmButton = await screen.findByRole("button", {
      name: "Hủy món",
    });
    expect(confirmButton).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Lý do"), {
      target: { value: "khách đổi ý" },
    });
    expect(confirmButton).not.toBeDisabled();
  });

  it("disables line actions once the order is locked", async () => {
    stubByPath({
      "/sales/orders/1/tickets": { items: [] },
      "/sales/orders/1": openOrder({ TrangThai: "Đã thanh toán" }),
      "/catalog/dishes": dishes,
      "/catalog/tables": tables,
    });
    render(<OrderDetail orderId={1} />);

    await screen.findByText("ORD-1");
    expect(
      screen.queryByRole("button", { name: "Hủy món" }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Thêm món/ })).toBeDisabled();
    // FR-SALE-09/22: serving progress stays editable after the bill is settled.
    expect(
      screen.getByRole("button", { name: "Đã xác nhận xong" }),
    ).toBeInTheDocument();
  });

  it("moves the order to a free table", async () => {
    stubByPath({
      "/sales/orders/1/tickets": { items: [] },
      "/sales/orders/1": openOrder(),
      "/catalog/dishes": dishes,
      "/catalog/tables": tables,
      "/sales/orders/1/move": { MaOrder: 1, MaBan: 2 },
    });
    render(<OrderDetail orderId={1} />);

    fireEvent.click(await screen.findByRole("button", { name: /Chuyển bàn/ }));
    fireEvent.click(screen.getByRole("combobox", { name: "Bàn đích" }));
    fireEvent.click(await screen.findByText("Bàn 2"));
    fireEvent.click(screen.getByRole("button", { name: "Chuyển bàn" }));

    expect(fetchMock).toHaveBeenCalledWith(
      "/sales/orders/1/move",
      expect.objectContaining({ body: { to_table_id: 2 } }),
    );
  });

  it("sends an idempotency key when quantity becomes a new add-on line", async () => {
    stubByPath({
      "/sales/orders/1/tickets": { items: [] },
      "/sales/orders/1": openOrder(),
      "/catalog/dishes": dishes,
      "/catalog/tables": tables,
    });
    render(
      <>
        <Toaster />
        <OrderDetail orderId={1} />
      </>,
    );
    fireEvent.click(await screen.findByRole("button", { name: "× 2" }));
    fireEvent.change(screen.getByLabelText("Số lượng Phở bò"), {
      target: { value: "4" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Lưu" }));
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/sales/orders/1/lines/10",
        expect.objectContaining({
          method: "PATCH",
          body: { quantity: 4, request_line_id: expect.any(String) },
        }),
      ),
    );
    expect(
      await screen.findByText(/Đã gọi thêm thành dòng món mới/),
    ).toBeInTheDocument();
  });
  it("queues reprints on server and shows actual delivery problems", async () => {
    stubByPath({
      "/sales/orders/1/tickets": {
        items: [
          {
            MaPhieuBep: 7,
            NoiDung: "Phở bò",
            TrangThaiIn: "Chưa rõ kết quả",
            SoLanIn: 1,
            LoiIn: "Kiểm tra giấy trước khi in lại.",
          },
        ],
      },
      "/sales/orders/1": openOrder(),
      "/catalog/dishes": dishes,
      "/catalog/tables": tables,
    });
    const browserPrint = vi.spyOn(window, "open");
    render(<OrderDetail orderId={1} />);
    expect(
      await screen.findByText("Kiểm tra giấy trước khi in lại."),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "In lại" }));
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/sales/orders/1/tickets/7/reprint",
        expect.objectContaining({ method: "POST" }),
      ),
    );
    expect(browserPrint).not.toHaveBeenCalled();
    browserPrint.mockRestore();
  });
});
