import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { clearSession, saveSession } from "@/lib/session";
import { SupplierList } from "./supplier-list";

const mockFetch = apiFetch as unknown as ReturnType<typeof vi.fn>;

describe("SupplierList", () => {
  beforeEach(() => {
    mockFetch.mockReset();
    saveSession({ token: "t", role: "MANAGER", username: "quanly" });
  });

  afterEach(() => clearSession());

  it("narrows rows by name or phone and pages through the rest", async () => {
    const items = Array.from({ length: 25 }, (_, i) => ({
      MaNhaCungCap: i + 1,
      TenNhaCungCap: `Nhà cung cấp ${i + 1}`,
      SoDienThoai: `090000000${i}`,
    }));
    mockFetch.mockResolvedValue({ items });
    render(<SupplierList />);

    await screen.findByText("Nhà cung cấp 1");
    expect(screen.getByText("Hiển thị 1–20 trên 25")).toBeInTheDocument();
    expect(screen.queryByText("Nhà cung cấp 21")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Trang 2" }));
    expect(await screen.findByText("Nhà cung cấp 21")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Tìm nhà cung cấp"), {
      target: { value: "Nhà cung cấp 1" },
    });
    expect(screen.getByText("Hiển thị 1–11 trên 11")).toBeInTheDocument();
    expect(screen.getByText("Nhà cung cấp 1")).toBeInTheDocument();
    expect(screen.queryByText("Nhà cung cấp 2")).not.toBeInTheDocument();
  });

  it("shows an empty-result row and clears the filter on reset", async () => {
    mockFetch.mockResolvedValue({
      items: [
        { MaNhaCungCap: 1, TenNhaCungCap: "Vissan", SoDienThoai: "0900000000" },
      ],
    });
    render(<SupplierList />);

    await screen.findByText("Vissan");
    fireEvent.change(screen.getByLabelText("Tìm nhà cung cấp"), {
      target: { value: "không tồn tại" },
    });
    expect(
      screen.getByText("Không có nhà cung cấp nào khớp bộ lọc."),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Xóa bộ lọc" }));
    expect(await screen.findByText("Vissan")).toBeInTheDocument();
  });
});
