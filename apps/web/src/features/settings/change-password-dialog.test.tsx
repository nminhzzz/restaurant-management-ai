import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { ChangePasswordDialog } from "./change-password-dialog";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

describe("ChangePasswordDialog", () => {
  beforeEach(() => vi.resetAllMocks());
  afterEach(cleanup);

  it("blocks submit when the confirmation does not match the new password", () => {
    render(<ChangePasswordDialog open onOpenChange={() => {}} />);

    fireEvent.change(screen.getByLabelText("Mật khẩu hiện tại"), {
      target: { value: "oldpass" },
    });
    fireEvent.change(screen.getByLabelText("Mật khẩu mới"), {
      target: { value: "newpass1" },
    });
    fireEvent.change(screen.getByLabelText("Xác nhận mật khẩu mới"), {
      target: { value: "different" },
    });

    expect(
      screen.getByText("Mật khẩu xác nhận không khớp."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Đổi mật khẩu" })).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Đổi mật khẩu" }));
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("submits the change once the passwords match", async () => {
    fetchMock.mockResolvedValue(undefined);
    render(<ChangePasswordDialog open onOpenChange={() => {}} />);

    fireEvent.change(screen.getByLabelText("Mật khẩu hiện tại"), {
      target: { value: "oldpass" },
    });
    fireEvent.change(screen.getByLabelText("Mật khẩu mới"), {
      target: { value: "newpass1" },
    });
    fireEvent.change(screen.getByLabelText("Xác nhận mật khẩu mới"), {
      target: { value: "newpass1" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Đổi mật khẩu" }));

    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/settings/auth/change-password",
        expect.objectContaining({
          method: "POST",
          body: { old_password: "oldpass", new_password: "newpass1" },
        }),
      ),
    );
  });
});
