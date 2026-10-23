import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { ApiError, apiFetch } from "@/lib/api-client";
import { IssueList } from "./issue-list";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

const ingredients = [
  { MaNguyenLieu: 1, TenNguyenLieu: "Gạo", DonViTinh: "kg" },
];

const issues = [{ MaPhieuXuat: 1, LyDo: "Hao hụt", TrangThai: "Nháp" }];

describe("IssueList", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    // Radix Select scrolls the highlighted item into view on open; jsdom has no
    // layout engine, so the method is missing outright.
    Element.prototype.scrollIntoView = vi.fn();
  });

  it("shows the API's negative-stock error inline", async () => {
    fetchMock.mockImplementation(
      (path: string, options: { method?: string } = {}) => {
        if (path.startsWith("/catalog/ingredients")) {
          return Promise.resolve({ items: ingredients });
        }
        if (path.startsWith("/inventory/issues") && options.method === "POST") {
          return Promise.reject(
            new ApiError(422, "BUSINESS_RULE_VIOLATION", "Không đủ tồn kho."),
          );
        }
        if (path.startsWith("/inventory/issues")) {
          return Promise.resolve({ items: [], total: 0 });
        }
        return Promise.resolve([]);
      },
    );

    render(<IssueList />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Tạo phiếu xuất" }),
    );

    fireEvent.change(await screen.findByLabelText("Số lượng"), {
      target: { value: "100" },
    });
    // Select defaults to the first ingredient's value only after interaction, so
    // the form still validates ingredient_id; pick it directly via the trigger.
    fireEvent.click(screen.getByRole("combobox", { name: "Nguyên liệu" }));
    fireEvent.click(await screen.findByText("Gạo (kg)"));

    fireEvent.click(screen.getByRole("button", { name: "Ghi nhận xuất kho" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Không đủ tồn kho.",
    );
  });

  it("requests page 1 with the default page size and shows the real total", async () => {
    fetchMock.mockImplementation((path: string) => {
      if (path.startsWith("/catalog/ingredients")) {
        return Promise.resolve({ items: ingredients });
      }
      if (path.startsWith("/inventory/issues")) {
        return Promise.resolve({ items: issues, total: 33 });
      }
      return Promise.resolve({});
    });

    render(<IssueList />);
    await screen.findByText("#1");

    expect(fetchMock).toHaveBeenCalledWith(
      "/inventory/issues?page=1&page_size=20",
    );
    expect(screen.getByText("Hiển thị 1–20 trên 33")).toBeInTheDocument();
  });

  it("sends the reason and date range filters and resets paging to page 1", async () => {
    fetchMock.mockImplementation((path: string) => {
      if (path.startsWith("/catalog/ingredients")) {
        return Promise.resolve({ items: ingredients });
      }
      if (path.startsWith("/inventory/issues")) {
        return Promise.resolve({ items: issues, total: 33 });
      }
      return Promise.resolve({});
    });

    render(<IssueList />);
    await screen.findByText("#1");

    fireEvent.click(screen.getByRole("button", { name: "Trang 2" }));
    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenLastCalledWith(
        "/inventory/issues?page=2&page_size=20",
      ),
    );

    fireEvent.change(screen.getByLabelText("Lý do"), {
      target: { value: "Hao hụt" },
    });
    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenLastCalledWith(
        "/inventory/issues?reason=Hao+h%E1%BB%A5t&page=1&page_size=20",
      ),
    );

    fireEvent.change(screen.getByLabelText("Từ ngày"), {
      target: { value: "2026-09-01" },
    });
    fireEvent.change(screen.getByLabelText("Đến ngày"), {
      target: { value: "2026-09-25" },
    });
    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenLastCalledWith(
        "/inventory/issues?reason=Hao+h%E1%BB%A5t&date_from=2026-09-01&date_to=2026-09-25&page=1&page_size=20",
      ),
    );
  });

  it("derives prepared-dish ingredients and sends only the line and servings", async () => {
    fetchMock.mockImplementation(
      (path: string, options: { method?: string; body?: unknown } = {}) => {
        if (path.startsWith("/catalog/ingredients")) {
          return Promise.resolve({ items: ingredients });
        }
        if (path.startsWith("/inventory/issues/prepared-preview")) {
          return Promise.resolve({
            order_line_id: 11,
            servings: 1,
            written_servings: 0,
            eligible_servings: 2,
            lines: [
              {
                ingredient_id: 1,
                ingredient_name: "Gạo",
                unit: "kg",
                quantity: 0.5,
              },
            ],
          });
        }
        if (path === "/inventory/issues" && options.method === "POST") {
          return Promise.resolve({ MaPhieuXuat: 9 });
        }
        if (path.startsWith("/inventory/issues")) {
          return Promise.resolve({ items: [], total: 0 });
        }
        if (path.startsWith("/sales/orders?")) {
          return Promise.resolve({ items: [{ MaOrder: 7 }] });
        }
        if (path === "/sales/orders/7") {
          return Promise.resolve({
            lines: [
              {
                MaChiTietOrder: 11,
                TenMon: "Phở",
                SoLuong: 2,
                TrangThai: "Đã phục vụ",
              },
            ],
          });
        }
        return Promise.resolve([]);
      },
    );

    render(<IssueList />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Tạo phiếu xuất" }),
    );

    fireEvent.click(screen.getByRole("combobox", { name: "Nguồn" }));
    fireEvent.click(await screen.findByText("Món đã chế biến"));
    expect(
      screen.queryByRole("combobox", { name: "Nguyên liệu" }),
    ).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Mã order"), {
      target: { value: "ORD-7" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Tìm" }));
    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith("/sales/orders/7"),
    );

    fireEvent.click(screen.getByRole("combobox", { name: "Dòng món" }));
    fireEvent.click(await screen.findByText(/#11 · Phở × 2/));
    fireEvent.change(screen.getByLabelText("Số suất"), {
      target: { value: "1" },
    });

    expect(await screen.findByText("Gạo (kg)")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Ghi nhận xuất kho" }));

    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/inventory/issues",
        expect.objectContaining({
          method: "POST",
          body: expect.objectContaining({
            source: "Món đã chế biến",
            lines: [{ order_line_id: 11, servings: 1 }],
          }),
        }),
      ),
    );
  });
});
