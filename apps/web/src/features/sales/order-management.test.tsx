import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
// The detail panels have their own tests; here only which order they receive matters.
vi.mock("./order-detail", () => ({
  OrderDetail: ({ orderId }: { orderId: number }) => (
    <p>Chi tiết món #{orderId}</p>
  ),
}));
vi.mock("./payment-panel", () => ({
  PaymentPanel: ({ orderId }: { orderId: number }) => (
    <p>Thanh toán #{orderId}</p>
  ),
}));
import { apiFetch } from "@/lib/api-client";
import { OrderManagement } from "./order-management";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

const tables = [{ MaBan: 3, TenBan: "Bàn 03" }];
const page = {
  total: 2,
  items: [
    {
      MaOrder: 41,
      MaOrderHienThi: "ORD-20261023-0041",
      LoaiDon: "Tại chỗ",
      MaBan: 3,
      TenBan: "Bàn 03",
      BusinessDate: "2026-10-23",
      NguoiLap: "Phạm Thu Hà",
      TrangThai: "Đã thanh toán",
      TongTien: 185000,
    },
    {
      MaOrder: 42,
      MaOrderHienThi: "ORD-20261023-0042",
      LoaiDon: "Mang về",
      MaBan: null,
      TenBan: null,
      BusinessDate: "2026-10-23",
      NguoiLap: null,
      TrangThai: "Đang mở",
      TongTien: 0,
    },
  ],
};

function lastOrderQuery(): URLSearchParams {
  const paths = fetchMock.mock.calls
    .map(([path]) => String(path))
    .filter((path) => path.startsWith("/sales/orders?"));
  return new URLSearchParams(paths.at(-1)?.split("?")[1]);
}

beforeEach(() => {
  fetchMock.mockImplementation((path: string) =>
    Promise.resolve(path.startsWith("/catalog/tables") ? tables : page),
  );
});

afterEach(() => {
  cleanup();
  fetchMock.mockReset();
});

describe("OrderManagement", () => {
  it("lists each order with type, table, date, creator, status and total", async () => {
    render(<OrderManagement />);

    await screen.findByText("ORD-20261023-0041");
    const table = within(screen.getByRole("table"));
    expect(table.getByText("Tại chỗ")).toBeTruthy();
    expect(table.getByText("Mang về")).toBeTruthy();
    expect(table.getByText("Bàn 03")).toBeTruthy();
    expect(table.getAllByText("23/10/2026")).toHaveLength(2);
    expect(table.getByText("Phạm Thu Hà")).toBeTruthy();
    expect(table.getByText("Đã thanh toán")).toBeTruthy();
    expect(table.getByText(/185\.000/)).toBeTruthy();
  });

  it("sends the combined filters to the order search", async () => {
    render(<OrderManagement />);
    await screen.findByText("ORD-20261023-0041");

    fireEvent.change(screen.getByLabelText("Mã order"), {
      target: { value: "ORD-20261023-0041" },
    });

    await waitFor(() =>
      expect(lastOrderQuery().get("code")).toBe("ORD-20261023-0041"),
    );
    expect(lastOrderQuery().get("page")).toBe("1");
  });

  it("opens the selected order's detail and payments, then goes back", async () => {
    render(<OrderManagement />);

    fireEvent.click(
      await screen.findByRole("button", {
        name: "Xem order ORD-20261023-0042",
      }),
    );

    expect(screen.getByText("Chi tiết món #42")).toBeTruthy();
    expect(screen.getByText("Thanh toán #42")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: /Quay lại danh sách/ }));
    expect(await screen.findByText("ORD-20261023-0041")).toBeTruthy();
  });

  it("explains an empty result instead of showing a blank table", async () => {
    fetchMock.mockImplementation((path: string) =>
      Promise.resolve(
        path.startsWith("/catalog/tables") ? tables : { items: [], total: 0 },
      ),
    );

    render(<OrderManagement />);

    expect(await screen.findByText("Không có order phù hợp")).toBeTruthy();
  });
});
