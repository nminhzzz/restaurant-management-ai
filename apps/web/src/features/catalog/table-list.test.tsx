import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { clearSession, saveSession } from "@/lib/session";
import { TableList } from "./table-list";

const mockFetch = apiFetch as unknown as ReturnType<typeof vi.fn>;

describe("TableList", () => {
  beforeEach(() => {
    mockFetch.mockReset();
    saveSession({ token: "t", role: "MANAGER", username: "quanly" });
  });

  afterEach(() => clearSession());

  it("narrows tables by status and clears the filter on reset", async () => {
    mockFetch.mockResolvedValue([
      { MaBan: 1, TenBan: "Bàn 1", TrangThai: "Trống" },
      { MaBan: 2, TenBan: "Bàn 2", TrangThai: "Đang phục vụ" },
    ]);
    render(<TableList />);

    await screen.findByText("Bàn 1");
    expect(screen.getByText("Bàn 2")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Trạng thái"), {
      target: { value: "Trống" },
    });
    expect(screen.getByText("Bàn 1")).toBeInTheDocument();
    expect(screen.queryByText("Bàn 2")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Xóa bộ lọc" }));
    expect(await screen.findByText("Bàn 2")).toBeInTheDocument();
  });
});
