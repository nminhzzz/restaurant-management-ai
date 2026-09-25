"use client";

import { useState } from "react";

import { FormField } from "@/components/form-field";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { apiFetch } from "@/lib/api-client";
import { useAction } from "@/lib/use-action";

import type { User } from "./users-panel";

/** FR-SET-02: a manager sets a new password for another account. */
export function ResetPasswordDialog({
  user,
  onOpenChange,
}: {
  user: User | null;
  onOpenChange: (open: boolean) => void;
}) {
  return (
    <Dialog open={user !== null} onOpenChange={onOpenChange}>
      <DialogContent className="w-[min(28rem,calc(100vw-2rem))]">
        {user ? (
          // Keyed by user id so the password field resets when the target account changes.
          <ResetPasswordForm
            key={user.MaNguoiDung}
            user={user}
            onDone={() => onOpenChange(false)}
          />
        ) : null}
        <DialogFooter>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>
            Quay lại
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function ResetPasswordForm({
  user,
  onDone,
}: {
  user: User;
  onDone: () => void;
}) {
  const [password, setPassword] = useState("");
  const { run, pending } = useAction();

  const error =
    password.length > 0 && password.length < 6
      ? "Mật khẩu tối thiểu 6 ký tự."
      : null;

  async function submit() {
    const result = await run(
      () =>
        apiFetch(`/settings/users/${user.MaNguoiDung}/reset-password`, {
          method: "POST",
          body: { new_password: password },
        }),
      `Đã đặt lại mật khẩu cho ${user.HoTen}.`,
    );
    if (result !== undefined) onDone();
  }

  return (
    <>
      <DialogHeader>
        <DialogTitle>Đặt lại mật khẩu</DialogTitle>
        <DialogDescription>
          Nhập mật khẩu mới cho {user.HoTen} ({user.TenDangNhap}).
        </DialogDescription>
      </DialogHeader>
      <FormField id="reset-password" label="Mật khẩu mới" error={error}>
        <Input
          id="reset-password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </FormField>
      <Button
        className="mt-4 w-full"
        disabled={pending || password.length < 6}
        onClick={submit}
      >
        Đặt lại mật khẩu
      </Button>
    </>
  );
}
