import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { ApiError, apiFetch } from "@/lib/api-client";
import { DishWriteOff } from "./dish-write-off";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

const lines = [
  {
    MaChiTietOrder: 7,
    MaOrder: 3,
    MaOrderHienThi: "A-003",
    TenMon: "Phở bò",
    TrangThai: "Đã xong",
    BusinessDate: "2026-09-10",
    SoLuong: 4,
    SoSuatDaHuy: 1,
    SoSuatConLai: 3,
  },
];

const qtyLabel = "Số suất hủy Phở bò A-003";

function route(post?: () => Promise<unknown>) {
  fetchMock.mockImplementation(
    (path: string, options: { method?: string } = {}) => {
      if (path === "/inventory/issues/dishes" && options.method === "POST") {
        return post
          ? post()
          : Promise.resolve({
              MaPhieuXuat: 9,
              NguonXuat: "Món đã chế biến",
              DongMon: [{ MaChiTietOrder: 7, SoSuatHuy: 2, SoSuatConLai: 1 }],
            });
      }
      return Promise.resolve({ items: lines, total: 1 });
    },
  );
}

function fill(servings: string, reason: string) {
  fireEvent.change(screen.getByLabelText(qtyLabel), {
    target: { value: servings },
  });
  fireEvent.change(screen.getByLabelText("Lý do"), {
    target: { value: reason },
  });
  fireEvent.click(screen.getByRole("button", { name: "Hủy món đã chọn" }));
}

describe("DishWriteOff", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("requests the writable lines of the chosen Business Date", async () => {
    route();
    render(<DishWriteOff />);
    await screen.findByText("Phở bò");
    expect(fetchMock).toHaveBeenCalledWith(
      "/inventory/issues/dish-lines?page=1&page_size=20",
    );

    fireEvent.change(screen.getByLabelText("Ngày kinh doanh"), {
      target: { value: "2026-09-10" },
    });
    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenLastCalledWith(
        "/inventory/issues/dish-lines?business_date=2026-09-10&page=1&page_size=20",
      ),
    );
  });

  it("caps servings at the remaining servings and limits the reason length", async () => {
    route();
    render(<DishWriteOff />);
    await screen.findByText("Phở bò");

    fireEvent.change(screen.getByLabelText(qtyLabel), {
      target: { value: "10" },
    });
    expect(screen.getByLabelText(qtyLabel)).toHaveValue(3);
    expect(screen.getByLabelText("Lý do")).toHaveAttribute("maxlength", "50");
  });

  it("requires servings and a reason before asking for confirmation", async () => {
    route();
    render(<DishWriteOff />);
    await screen.findByText("Phở bò");

    fireEvent.click(screen.getByRole("button", { name: "Hủy món đã chọn" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "ít nhất một dòng món",
    );

    fill("2", "  ");
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Nhập lý do hủy.",
    );
    expect(fetchMock).not.toHaveBeenCalledWith(
      "/inventory/issues/dishes",
      expect.anything(),
    );
  });

  it("posts the selected lines after confirmation and reloads", async () => {
    route();
    render(<DishWriteOff />);
    await screen.findByText("Phở bò");

    fireEvent.change(screen.getByLabelText(qtyLabel), {
      target: { value: "2" },
    });
    fireEvent.change(screen.getByLabelText("Lý do"), {
      target: { value: "Làm đổ" },
    });
    fireEvent.change(screen.getByLabelText("Ghi chú (không bắt buộc)"), {
      target: { value: "Rơi khi bưng" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Hủy món đã chọn" }));
    fireEvent.click(
      await screen.findByRole("button", { name: "Xác nhận hủy" }),
    );

    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith("/inventory/issues/dishes", {
        method: "POST",
        body: {
          reason: "Làm đổ",
          note: "Rơi khi bưng",
          lines: [{ order_line_id: 7, servings: 2 }],
        },
      }),
    );
    await vi.waitFor(() =>
      expect(screen.getByLabelText(qtyLabel)).toHaveValue(null),
    );
  });

  it("shows the server's message inline when the request is rejected", async () => {
    route(() =>
      Promise.reject(
        new ApiError(
          409,
          "BUSINESS_RULE_VIOLATION",
          "Đang có phiếu kiểm kê mở, chưa thể hủy món.",
        ),
      ),
    );
    render(<DishWriteOff />);
    await screen.findByText("Phở bò");

    fill("1", "Hỏng");
    fireEvent.click(
      await screen.findByRole("button", { name: "Xác nhận hủy" }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Đang có phiếu kiểm kê mở, chưa thể hủy món.",
    );
    // The draft survives so the user can retry once the stocktake is closed.
    expect(screen.getByLabelText(qtyLabel)).toHaveValue(1);
  });

  it("shows an empty state when nothing is writable", async () => {
    fetchMock.mockResolvedValue({ items: [], total: 0 });
    render(<DishWriteOff />);
    expect(
      await screen.findByText("Không có món nào để hủy"),
    ).toBeInTheDocument();
  });
});
