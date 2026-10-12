import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { ApiError, apiFetch } from "@/lib/api-client";
import { OrderStep } from "./order-step";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

const dishes = {
  items: [
    {
      MaMon: 5,
      TenMon: "Phở bò",
      TrangThai: "Hoạt động",
      GiaHienTai: 65000,
      MaNhomMon: 1,
    },
    {
      MaMon: 6,
      TenMon: "Nem rán",
      TrangThai: "Hoạt động",
      GiaHienTai: null,
      MaNhomMon: 1,
    },
    {
      MaMon: 7,
      TenMon: "Bún chả",
      TrangThai: "Hết nguyên liệu",
      GiaHienTai: 60000,
      MaNhomMon: 1,
    },
    {
      MaMon: 8,
      TenMon: "Gỏi cuốn",
      TrangThai: "Hoạt động",
      GiaHienTai: 30000,
      MaNhomMon: 1,
    },
  ],
};

function route(extra: Record<string, unknown> = {}) {
  const routes: Record<string, unknown> = {
    "/catalog/tables": [{ MaBan: 4, TenBan: "Bàn 04" }],
    "/catalog/dishes": dishes,
    "/catalog/groups": [{ MaNhomMon: 1, TenNhom: "Món chính" }],
    ...extra,
  };
  fetchMock.mockImplementation((path: string) => {
    const match = Object.entries(routes)
      .filter(([prefix]) => path === prefix || path.startsWith(prefix))
      .sort(([left], [right]) => right.length - left.length)[0];
    return Promise.resolve(match?.[1] ?? {});
  });
}

describe("OrderStep", () => {
  beforeEach(() => vi.resetAllMocks());

  it("shows prices and keeps unpriced and unsellable dishes out of the cart", async () => {
    route();
    render(
      <OrderStep
        tableId={4}
        orderId={null}
        onBack={vi.fn()}
        onSent={vi.fn()}
      />,
    );

    expect(await screen.findByText("65.000 ₫")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Nem rán/ })).toBeDisabled();
    expect(screen.getByText("Chưa có giá")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Bún chả/ }),
    ).not.toBeInTheDocument();
  });

  it("totals the cart as dishes are added", async () => {
    route();
    render(
      <OrderStep
        tableId={4}
        orderId={null}
        onBack={vi.fn()}
        onSent={vi.fn()}
      />,
    );
    const tile = await screen.findByRole("button", { name: /Phở bò/ });
    fireEvent.click(tile);
    fireEvent.click(tile);
    expect(screen.getByTestId("cart-total")).toHaveTextContent("130.000 ₫");
  });

  it("creates a new dine-in order and moves on to payment", async () => {
    const onSent = vi.fn();
    route({
      "/sales/selections": { MaLuotChon: "selection-42" },
      "/sales/selections/selection-42/lines/5": {
        MaGiuCho: 91,
        MaLuotChon: "selection-42",
        MaMon: 5,
        SoLuong: 1,
        ThoiDiemHetHan: "2099-01-01T10:00:00",
        TrangThai: "Đang giữ",
      },
      "/sales/selections/selection-42/submit": {
        MaOrder: 42,
        MaOrderHienThi: "ORD-42",
        CanXacNhanLai: false,
        stale: [],
        lines: [{ MaChiTietOrder: 1, MaMon: 5, SoLuong: 1, DonGia: 65000 }],
      },
    });
    render(
      <OrderStep tableId={4} orderId={null} onBack={vi.fn()} onSent={onSent} />,
    );
    fireEvent.click(await screen.findByRole("button", { name: /Phở bò/ }));
    fireEvent.click(
      screen.getByRole("button", { name: "Gửi bếp & thanh toán" }),
    );

    await vi.waitFor(() => expect(onSent).toHaveBeenCalledWith(42, "pay"));
    expect(fetchMock).toHaveBeenCalledWith(
      "/sales/selections/selection-42/submit",
      expect.objectContaining({
        method: "POST",
        body: expect.objectContaining({ MaYeuCauGui: expect.any(String) }),
      }),
    );
  });

  it("adds lines to an open order instead of creating one", async () => {
    const onSent = vi.fn();
    route({
      "/sales/selections": { MaLuotChon: "selection-142" },
      "/sales/selections/selection-142/lines/5": {
        MaGiuCho: 92,
        MaLuotChon: "selection-142",
        MaMon: 5,
        SoLuong: 1,
        ThoiDiemHetHan: "2099-01-01T10:00:00",
        TrangThai: "Đang giữ",
      },
      "/sales/selections/selection-142/submit": {
        MaOrder: 142,
        MaOrderHienThi: "ORD-142",
        CanXacNhanLai: false,
        stale: [],
        lines: [{ MaChiTietOrder: 9, MaMon: 5, SoLuong: 1, DonGia: 65000 }],
      },
      "/sales/orders/142": {
        MaOrder: 142,
        MaOrderHienThi: "ORD-142",
        TrangThai: "Đang mở",
        ThoiDiemTao: "2026-09-26T14:32:00",
        lines: [
          {
            MaChiTietOrder: 1,
            MaMon: 5,
            SoLuong: 2,
            DonGia: 65000,
            TrangThai: "Chờ",
          },
        ],
      },
    });
    render(
      <OrderStep tableId={4} orderId={142} onBack={vi.fn()} onSent={onSent} />,
    );

    expect(await screen.findByText("Đã gửi bếp")).toBeInTheDocument();
    expect(screen.getByText(/mở 14:32/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Phở bò/ }));
    fireEvent.click(screen.getByRole("button", { name: "Gửi bếp" }));

    await vi.waitFor(() => expect(onSent).toHaveBeenCalledWith(142, "floor"));
    expect(fetchMock).toHaveBeenCalledWith(
      "/sales/selections/selection-142/submit",
      expect.objectContaining({
        method: "POST",
        body: expect.objectContaining({ MaYeuCauGui: expect.any(String) }),
      }),
    );
  });

  it("keeps the sent total right after a partial add-more failure", async () => {
    const onSent = vi.fn();
    const routes: Record<string, unknown> = {
      "/catalog/tables": [{ MaBan: 4, TenBan: "Bàn 04" }],
      "/catalog/dishes": dishes,
      "/catalog/groups": [{ MaNhomMon: 1, TenNhom: "Món chính" }],
      "/sales/orders/142": {
        MaOrder: 142,
        MaOrderHienThi: "ORD-142",
        TrangThai: "Đang mở",
        lines: [
          {
            MaChiTietOrder: 1,
            MaMon: 5,
            SoLuong: 2,
            DonGia: 65000,
            TrangThai: "Chờ",
          },
        ],
      },
    };
    fetchMock.mockImplementation((path: string) => {
      if (path === "/sales/selections")
        return Promise.resolve({ MaLuotChon: "selection-partial" });
      if (path === "/sales/selections/selection-partial/lines/5")
        return Promise.resolve({
          MaGiuCho: 94,
          ThoiDiemHetHan: "2099-01-01T10:00:00",
        });
      if (path === "/sales/selections/selection-partial/lines/8") {
        return Promise.reject(
          new ApiError(409, "OUT_OF_STOCK", "Hết nguyên liệu."),
        );
      }
      if (path === "/sales/selections/selection-partial/submit")
        return Promise.resolve({
          MaOrder: 142,
          CanXacNhanLai: false,
          stale: [],
          lines: [{ MaChiTietOrder: 9, MaMon: 5, SoLuong: 1, DonGia: 65000 }],
        });
      return Promise.resolve(
        Object.entries(routes).find(([p]) => path.startsWith(p))?.[1] ?? {},
      );
    });

    render(
      <OrderStep tableId={4} orderId={142} onBack={vi.fn()} onSent={onSent} />,
    );
    fireEvent.click(await screen.findByRole("button", { name: /Phở bò/ }));
    fireEvent.click(screen.getByRole("button", { name: /Gỏi cuốn/ }));
    fireEvent.click(screen.getByRole("button", { name: "Gửi bếp" }));

    expect(
      await screen.findByText(
        "Một số món chưa giữ được. Sửa lỗi từng món rồi gửi lại.",
      ),
    ).toBeInTheDocument();
    expect(onSent).not.toHaveBeenCalled();
    // Phở bò was confirmed and left the cart; Gỏi cuốn failed and stayed.
    expect(screen.queryByLabelText("Số lượng Phở bò")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Số lượng Gỏi cuốn")).toBeInTheDocument();
    // sent (130.000) + confirmed Phở bò (65.000) + unsent Gỏi cuốn (30.000)
    expect(screen.getByTestId("cart-total")).toHaveTextContent("225.000 ₫");
  });

  it("creates a takeaway order when there is no table", async () => {
    route({
      "/sales/selections": { MaLuotChon: "selection-50" },
      "/sales/selections/selection-50/lines/5": {
        MaGiuCho: 95,
        MaLuotChon: "selection-50",
        MaMon: 5,
        SoLuong: 1,
        ThoiDiemHetHan: "2099-01-01T10:00:00",
        TrangThai: "Đang giữ",
      },
      "/sales/selections/selection-50/submit": {
        MaOrder: 50,
        CanXacNhanLai: false,
        stale: [],
        lines: [{ MaChiTietOrder: 1, MaMon: 5, SoLuong: 1, DonGia: 65000 }],
      },
    });
    render(
      <OrderStep
        tableId={null}
        orderId={null}
        onBack={vi.fn()}
        onSent={vi.fn()}
      />,
    );
    fireEvent.click(await screen.findByRole("button", { name: /Phở bò/ }));
    fireEvent.click(screen.getByRole("button", { name: "Gửi bếp" }));
    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/sales/selections/selection-50/submit",
        expect.objectContaining({
          body: expect.objectContaining({ MaYeuCauGui: expect.any(String) }),
        }),
      ),
    );
  });

  it("creates a server selection and hold and renders the hold expiry", async () => {
    route({
      "/sales/selections": { MaLuotChon: "selection-1" },
      "/sales/selections/selection-1/lines/5": {
        MaGiuCho: 91,
        MaLuotChon: "selection-1",
        MaMon: 5,
        SoLuong: 1,
        ThoiDiemHetHan: "2020-01-01T10:00:00",
        TrangThai: "Đang giữ",
      },
    });
    render(
      <OrderStep
        tableId={4}
        orderId={null}
        onBack={vi.fn()}
        onSent={vi.fn()}
      />,
    );

    fireEvent.click(await screen.findByRole("button", { name: /Phở bò/ }));

    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/sales/selections",
        expect.objectContaining({
          method: "POST",
          body: expect.objectContaining({ MaBan: 4, MaOrder: null }),
        }),
      ),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "/sales/selections/selection-1/lines/5",
      expect.objectContaining({
        method: "PUT",
        body: { SoLuong: 1, GhiChu: null, MaBan: 4, MaOrder: null },
      }),
    );
    expect(await screen.findByText(/Đã hết hạn/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Thêm một Phở bò" }));
    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/sales/selections/selection-1/lines/5",
        expect.objectContaining({
          method: "PUT",
          body: expect.objectContaining({ SoLuong: 2 }),
        }),
      ),
    );
    fireEvent.change(screen.getByLabelText("Ghi chú Phở bò"), {
      target: { value: "Ít hành" },
    });
    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/sales/selections/selection-1/lines/5",
        expect.objectContaining({
          method: "PUT",
          body: expect.objectContaining({ GhiChu: "Ít hành" }),
        }),
      ),
    );
    fireEvent.click(screen.getByRole("button", { name: "Bớt một Phở bò" }));
    fireEvent.click(screen.getByRole("button", { name: "Bỏ Phở bò" }));
    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/sales/holds/91",
        expect.objectContaining({ method: "DELETE" }),
      ),
    );
  });

  it("retries submission with the same request key after a timeout", async () => {
    let submits = 0;
    fetchMock.mockImplementation(
      (path: string, options?: { method?: string }) => {
        if (path === "/catalog/tables")
          return Promise.resolve([{ MaBan: 4, TenBan: "Bàn 04" }]);
        if (path === "/catalog/dishes?size=200") return Promise.resolve(dishes);
        if (path === "/catalog/groups")
          return Promise.resolve([{ MaNhomMon: 1, TenNhom: "Món chính" }]);
        if (path === "/sales/selections" && options?.method === "POST")
          return Promise.resolve({ MaLuotChon: "selection-retry" });
        if (path.endsWith("/lines/5"))
          return Promise.resolve({
            MaGiuCho: 92,
            ThoiDiemHetHan: "2099-01-01T10:00:00",
          });
        if (path === "/sales/selections/selection-retry/submit") {
          submits += 1;
          return submits === 1
            ? Promise.reject(new Error("timeout"))
            : Promise.resolve({
                MaOrder: 42,
                MaOrderHienThi: "ORD-42",
                CanXacNhanLai: false,
                stale: [],
                lines: [
                  { MaChiTietOrder: 1, MaMon: 5, SoLuong: 1, DonGia: 65000 },
                ],
              });
        }
        return Promise.resolve({});
      },
    );
    const onSent = vi.fn();
    render(
      <OrderStep tableId={4} orderId={null} onBack={vi.fn()} onSent={onSent} />,
    );

    fireEvent.click(await screen.findByRole("button", { name: /Phở bò/ }));
    await screen.findByText(/Giữ đến/);
    fireEvent.click(screen.getByRole("button", { name: "Gửi bếp" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Không gửi được món.",
    );
    fireEvent.click(screen.getByRole("button", { name: "Gửi bếp" }));

    await vi.waitFor(() => expect(onSent).toHaveBeenCalledWith(42, "floor"));
    const submitBodies = fetchMock.mock.calls
      .filter(([path]) => path === "/sales/selections/selection-retry/submit")
      .map(([, options]) => options.body);
    expect(submitBodies).toHaveLength(2);
    expect(submitBodies[1]).toEqual(submitBodies[0]);
  });

  it("requires explicit reconfirmation after a stale selection response", async () => {
    let submits = 0;
    fetchMock.mockImplementation(
      (path: string, options?: { method?: string }) => {
        if (path === "/catalog/tables")
          return Promise.resolve([{ MaBan: 4, TenBan: "Bàn 04" }]);
        if (path === "/catalog/dishes?size=200") return Promise.resolve(dishes);
        if (path === "/catalog/groups")
          return Promise.resolve([{ MaNhomMon: 1, TenNhom: "Món chính" }]);
        if (path === "/sales/selections" && options?.method === "POST")
          return Promise.resolve({ MaLuotChon: "selection-stale" });
        if (path.endsWith("/lines/5"))
          return Promise.resolve({
            MaGiuCho: 93,
            ThoiDiemHetHan: "2099-01-01T10:00:00",
          });
        if (path === "/sales/selections/selection-stale/submit") {
          submits += 1;
          return Promise.resolve(
            submits === 1
              ? {
                  MaOrder: null,
                  CanXacNhanLai: true,
                  stale: [{ MaGiuCho: 93, MaMon: 5 }],
                  lines: [],
                }
              : {
                  MaOrder: 42,
                  MaOrderHienThi: "ORD-42",
                  CanXacNhanLai: false,
                  stale: [],
                  lines: [
                    { MaChiTietOrder: 2, MaMon: 5, SoLuong: 1, DonGia: 65000 },
                  ],
                },
          );
        }
        return Promise.resolve({});
      },
    );
    const onSent = vi.fn();
    render(
      <OrderStep tableId={4} orderId={null} onBack={vi.fn()} onSent={onSent} />,
    );

    fireEvent.click(await screen.findByRole("button", { name: /Phở bò/ }));
    await screen.findByText(/Giữ đến/);
    fireEvent.click(screen.getByRole("button", { name: "Gửi bếp" }));
    const confirm = await screen.findByRole("button", {
      name: /Xác nhận.*gửi bếp/i,
    });
    expect(onSent).not.toHaveBeenCalled();
    expect(screen.getByLabelText("Số lượng Phở bò")).toBeInTheDocument();

    fireEvent.click(confirm);
    await vi.waitFor(() => expect(onSent).toHaveBeenCalledWith(42, "floor"));
    expect(submits).toBe(2);
  });
});
