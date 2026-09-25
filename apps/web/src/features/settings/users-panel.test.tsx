import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { UsersPanel } from "./users-panel";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

/** Route the mocked apiFetch by path prefix; the first matching prefix wins. */
function stubByPath(routes: Record<string, unknown>) {
  const entries = Object.entries(routes);
  fetchMock.mockImplementation((path: string) =>
    Promise.resolve(
      entries.find(([prefix]) => path.startsWith(prefix))?.[1] ?? {},
    ),
  );
}

const oneUser = {
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
};

const twoUsers = {
  items: [
    ...oneUser.items,
    {
      MaNguoiDung: 3,
      TenDangNhap: "quanly01",
      HoTen: "Trần Văn Quản",
      SoDienThoai: null,
      MaVaiTro: "MANAGER",
      TrangThai: "Hoạt động",
      NgayTao: "2026-09-01T08:00:00",
    },
  ],
  total: 2,
};

describe("UsersPanel", () => {
  beforeEach(() => vi.resetAllMocks());
  afterEach(cleanup);

  it("posts the new-account form to POST /settings/users", async () => {
    stubByPath({ "/settings/users": oneUser });
    render(<UsersPanel />);

    await screen.findByText("Phạm Thu Hà");
    fireEvent.click(screen.getByRole("button", { name: "Thêm tài khoản" }));

    fireEvent.change(screen.getByLabelText("Họ tên"), {
      target: { value: "Trần Văn A" },
    });
    fireEvent.change(screen.getByLabelText("Tên đăng nhập"), {
      target: { value: "tranvana" },
    });
    fireEvent.change(screen.getByLabelText("Mật khẩu ban đầu"), {
      target: { value: "123456" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Tạo tài khoản" }));

    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/settings/users",
        expect.objectContaining({
          method: "POST",
          body: expect.objectContaining({
            username: "tranvana",
            password: "123456",
            full_name: "Trần Văn A",
            phone: null,
            role: "CASHIER",
          }),
        }),
      ),
    );
  });

  it("locks an account only after the confirmation dialog is accepted", async () => {
    stubByPath({ "/settings/users": oneUser });
    render(<UsersPanel />);

    await screen.findByText("Phạm Thu Hà");
    fireEvent.click(
      screen.getByRole("button", { name: "Khóa tài khoản Phạm Thu Hà" }),
    );

    expect(fetchMock).not.toHaveBeenCalledWith(
      expect.stringContaining("/lock"),
      expect.anything(),
    );

    fireEvent.click(screen.getByRole("button", { name: "Khóa tài khoản" }));

    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/settings/users/2/lock",
        expect.objectContaining({ method: "PATCH" }),
      ),
    );
  });

  it("unlocks a locked account through PATCH /unlock after confirmation", async () => {
    stubByPath({
      "/settings/users": {
        ...oneUser,
        items: [{ ...oneUser.items[0], TrangThai: "Đã khóa" }],
      },
    });
    render(<UsersPanel />);

    await screen.findByText("Phạm Thu Hà");
    expect(
      screen.queryByRole("button", { name: "Khóa tài khoản Phạm Thu Hà" }),
    ).not.toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: "Mở khóa tài khoản Phạm Thu Hà" }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Mở khóa" }));

    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/settings/users/2/unlock",
        expect.objectContaining({ method: "PATCH" }),
      ),
    );
  });

  it("narrows the list with the search box", async () => {
    stubByPath({ "/settings/users": twoUsers });
    render(<UsersPanel />);

    await screen.findByText("Phạm Thu Hà");
    expect(screen.getByText("Trần Văn Quản")).toBeInTheDocument();

    fireEvent.change(
      screen.getByLabelText("Tìm theo tên, tên đăng nhập, số điện thoại"),
      { target: { value: "Quản" } },
    );

    expect(screen.queryByText("Phạm Thu Hà")).not.toBeInTheDocument();
    expect(screen.getByText("Trần Văn Quản")).toBeInTheDocument();
  });

  it("narrows the list with the role filter", async () => {
    stubByPath({ "/settings/users": twoUsers });
    render(<UsersPanel />);

    await screen.findByText("Phạm Thu Hà");

    fireEvent.change(screen.getByLabelText("Vai trò"), {
      target: { value: "MANAGER" },
    });

    expect(screen.queryByText("Phạm Thu Hà")).not.toBeInTheDocument();
    expect(screen.getByText("Trần Văn Quản")).toBeInTheDocument();
  });
});
