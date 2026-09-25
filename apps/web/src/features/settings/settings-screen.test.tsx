import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { ApiError, apiFetch } from "@/lib/api-client";
import { SettingsScreen } from "./settings-screen";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

describe("SettingsScreen", () => {
  beforeEach(() => vi.resetAllMocks());

  it("lists accounts with the Vietnamese role name", async () => {
    fetchMock.mockResolvedValue({
      items: [
        {
          MaNguoiDung: 2,
          TenDangNhap: "thungan01",
          HoTen: "Phạm Thu Hà",
          SoDienThoai: null,
          MaVaiTro: "CASHIER",
          TrangThai: "Hoạt động",
          NgayTao: "2026-09-01T08:00:00",
        },
      ],
      total: 1,
    });

    render(<SettingsScreen />);

    expect(await screen.findByText("Phạm Thu Hà")).toBeInTheDocument();
    expect(screen.getByText("Thu ngân")).toBeInTheDocument();
    expect(screen.queryByText("CASHIER")).not.toBeInTheDocument();
  });

  it("shows the API's refusal instead of an empty table", async () => {
    fetchMock.mockRejectedValue(
      new ApiError(403, "FORBIDDEN", "Bạn không có quyền xem tài khoản."),
    );

    render(<SettingsScreen />);

    expect(
      await screen.findByText("Bạn không có quyền xem tài khoản."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Thử lại" })).toBeInTheDocument();
  });
});
