import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { clearSession, saveSession } from "@/lib/session";
import { IngredientList } from "./ingredient-list";

const mockFetch = apiFetch as unknown as ReturnType<typeof vi.fn>;

describe("IngredientList", () => {
  beforeEach(() => {
    mockFetch.mockReset();
    saveSession({ token: "t", role: "MANAGER", username: "quanly" });
  });

  afterEach(() => clearSession());

  it("narrows rows by search and unit, and pages through the rest", async () => {
    const items = Array.from({ length: 25 }, (_, i) => ({
      MaNguyenLieu: i + 1,
      TenNguyenLieu: `Nguyên liệu ${i + 1}`,
      DonViTinh: i % 2 === 0 ? "kg" : "lít",
      MucTonToiThieu: 5,
    }));
    mockFetch.mockResolvedValue({ items });
    render(<IngredientList />);

    await screen.findByText("Nguyên liệu 1");
    expect(screen.getByText("Hiển thị 1–20 trên 25")).toBeInTheDocument();
    expect(screen.queryByText("Nguyên liệu 21")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Trang 2" }));
    expect(await screen.findByText("Nguyên liệu 21")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Tìm nguyên liệu"), {
      target: { value: "Nguyên liệu 1" },
    });
    expect(screen.getByText("Hiển thị 1–11 trên 11")).toBeInTheDocument();
    expect(screen.getByText("Nguyên liệu 1")).toBeInTheDocument();
    expect(screen.queryByText("Nguyên liệu 2")).not.toBeInTheDocument();
  });

  it("shows an empty-result row and clears filters on reset", async () => {
    mockFetch.mockResolvedValue({
      items: [
        {
          MaNguyenLieu: 1,
          TenNguyenLieu: "Thịt bò",
          DonViTinh: "kg",
          MucTonToiThieu: 5,
        },
      ],
    });
    render(<IngredientList />);

    await screen.findByText("Thịt bò");
    fireEvent.change(screen.getByLabelText("Tìm nguyên liệu"), {
      target: { value: "không tồn tại" },
    });
    expect(
      screen.getByText("Không có nguyên liệu nào khớp bộ lọc."),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Xóa bộ lọc" }));
    expect(await screen.findByText("Thịt bò")).toBeInTheDocument();
  });

  it("shows the effective threshold and marks a default-following ingredient", async () => {
    mockFetch.mockResolvedValue({
      items: [
        {
          MaNguyenLieu: 1,
          TenNguyenLieu: "Muối",
          DonViTinh: "kg",
          MucTonToiThieu: null,
          MucTonToiThieuApDung: 7,
        },
        {
          MaNguyenLieu: 2,
          TenNguyenLieu: "Thịt bò",
          DonViTinh: "kg",
          MucTonToiThieu: 3,
          MucTonToiThieuApDung: 3,
        },
      ],
    });
    render(<IngredientList />);

    await screen.findByText("Muối");
    expect(screen.getAllByText("Mặc định hệ thống")).toHaveLength(1);
    expect(screen.getByText("7")).toBeInTheDocument();
  });

  it("sends null to return an ingredient to the default threshold", async () => {
    mockFetch.mockImplementation((path: string) =>
      Promise.resolve(
        path.startsWith("/catalog/ingredients?")
          ? {
              items: [
                {
                  MaNguyenLieu: 2,
                  TenNguyenLieu: "Thịt bò",
                  DonViTinh: "kg",
                  MucTonToiThieu: 3,
                  MucTonToiThieuApDung: 3,
                },
              ],
            }
          : {},
      ),
    );
    render(<IngredientList />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Sửa nguyên liệu" }),
    );
    fireEvent.change(screen.getByLabelText("Mức tồn tối thiểu"), {
      target: { value: "" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Lưu" }));

    await vi.waitFor(() =>
      expect(mockFetch).toHaveBeenCalledWith(
        "/catalog/ingredients/2",
        expect.objectContaining({
          body: { TenNguyenLieu: "Thịt bò", MucTonToiThieu: null },
        }),
      ),
    );
  });
});
