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

  it("shows the system default for a null threshold and 0 for an own zero", async () => {
    mockFetch.mockResolvedValue({
      items: [
        {
          MaNguyenLieu: 1,
          TenNguyenLieu: "Muối",
          DonViTinh: "kg",
          MucTonToiThieu: null,
        },
        {
          MaNguyenLieu: 2,
          TenNguyenLieu: "Đường",
          DonViTinh: "kg",
          MucTonToiThieu: 0,
        },
      ],
    });
    render(<IngredientList />);

    const salt = (await screen.findByText("Muối")).closest("tr")!;
    const sugar = screen.getByText("Đường").closest("tr")!;
    expect(salt).toHaveTextContent("Mặc định");
    expect(sugar).not.toHaveTextContent("Mặc định");
    expect(sugar).toHaveTextContent("0");
  });

  it("opens the add dialog empty after a previous ingredient was saved", async () => {
    mockFetch.mockResolvedValue({ items: [] });
    render(<IngredientList />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Thêm nguyên liệu" }),
    );
    fireEvent.change(screen.getByLabelText("Tên nguyên liệu"), {
      target: { value: "Thịt bò" },
    });
    fireEvent.change(screen.getByLabelText("Đơn vị tính"), {
      target: { value: "g" },
    });
    fireEvent.change(screen.getByLabelText("Mức tồn tối thiểu"), {
      target: { value: "500" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Lưu" }));
    await vi.waitFor(() =>
      expect(
        screen.queryByLabelText("Tên nguyên liệu"),
      ).not.toBeInTheDocument(),
    );

    fireEvent.click(screen.getByRole("button", { name: "Thêm nguyên liệu" }));

    const field = (label: string) =>
      (screen.getByLabelText(label) as HTMLInputElement).value;
    expect(field("Tên nguyên liệu")).toBe("");
    expect(field("Mức tồn tối thiểu")).toBe("");
  });

  it("sends the shelf life when creating an ingredient", async () => {
    mockFetch.mockResolvedValue({ items: [] });
    render(<IngredientList />);

    fireEvent.click(
      await screen.findByRole("button", { name: "Thêm nguyên liệu" }),
    );
    fireEvent.change(screen.getByLabelText("Tên nguyên liệu"), {
      target: { value: "Cà chua" },
    });
    fireEvent.change(screen.getByLabelText("Đơn vị tính"), {
      target: { value: "kg" },
    });
    fireEvent.change(screen.getByLabelText("Số ngày bảo quản"), {
      target: { value: "5" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Lưu" }));

    await vi.waitFor(() =>
      expect(mockFetch).toHaveBeenCalledWith(
        "/catalog/ingredients",
        expect.objectContaining({
          method: "POST",
          body: expect.objectContaining({ SoNgayBaoQuan: 5 }),
        }),
      ),
    );
  });
});
