"use client";

import { useState } from "react";

import { FormField } from "@/components/form-field";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { apiFetch } from "@/lib/api-client";
import { roleLabel } from "@/lib/roles";
import { loadSession } from "@/lib/session";
import { useAction } from "@/lib/use-action";

import type { User } from "./users-panel";

const ROLES = ["MANAGER", "CASHIER", "WAREHOUSE"] as const;

/**
 * FR-SET-01: edit an account's name, phone and role. The server refuses changing your own
 * role and demoting the last manager; the select is disabled for yourself as a hint only.
 */
export function EditUserDialog({
  user,
  onOpenChange,
  onSaved,
}: {
  user: User | null;
  onOpenChange: (open: boolean) => void;
  onSaved: () => void;
}) {
  return (
    <Dialog open={user !== null} onOpenChange={onOpenChange}>
      <DialogContent className="w-[min(28rem,calc(100vw-2rem))]">
        {user ? (
          <EditUserForm
            key={user.MaNguoiDung}
            user={user}
            onClose={() => onOpenChange(false)}
            onSaved={onSaved}
          />
        ) : null}
      </DialogContent>
    </Dialog>
  );
}

function EditUserForm({
  user,
  onClose,
  onSaved,
}: {
  user: User;
  onClose: () => void;
  onSaved: () => void;
}) {
  const { run, pending, error } = useAction();
  const [fullName, setFullName] = useState(user.HoTen);
  const [phone, setPhone] = useState(user.SoDienThoai ?? "");
  const [role, setRole] = useState(user.MaVaiTro);
  const isSelf = loadSession()?.username === user.TenDangNhap;

  async function save() {
    const result = await run(
      () =>
        apiFetch(`/settings/users/${user.MaNguoiDung}`, {
          method: "PATCH",
          body: {
            full_name: fullName.trim(),
            phone: phone.trim() || null,
            ...(role !== user.MaVaiTro ? { role } : {}),
          },
        }),
      `Đã cập nhật tài khoản ${fullName.trim()}.`,
    );
    if (result !== undefined) {
      onSaved();
      onClose();
    }
  }

  return (
    <>
      <DialogHeader>
        <DialogTitle>Sửa tài khoản {user.TenDangNhap}</DialogTitle>
      </DialogHeader>
      <div className="space-y-4">
        <FormField id="edit-user-name" label="Họ tên">
          <Input
            id="edit-user-name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
        </FormField>
        <FormField id="edit-user-phone" label="Số điện thoại">
          <Input
            id="edit-user-phone"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
        </FormField>
        <FormField
          id="edit-user-role"
          label="Vai trò"
          help={isSelf ? "Không thể tự đổi vai trò của chính mình." : undefined}
        >
          <select
            id="edit-user-role"
            disabled={isSelf}
            value={role}
            onChange={(e) => setRole(e.target.value)}
            className="flex h-9 w-full rounded-control border border-border-strong bg-surface px-3 py-1 text-sm text-ink hover:border-ink focus-visible:border-primary focus-visible:ring-1 focus-visible:ring-primary focus-visible:outline-none disabled:opacity-50"
          >
            {ROLES.map((value) => (
              <option key={value} value={value}>
                {roleLabel(value)}
              </option>
            ))}
          </select>
        </FormField>
        {error ? (
          <p role="alert" className="text-danger-fg">
            {error}
          </p>
        ) : null}
      </div>
      <DialogFooter>
        <Button variant="secondary" onClick={onClose}>
          Quay lại
        </Button>
        <Button disabled={pending || fullName.trim() === ""} onClick={save}>
          Lưu
        </Button>
      </DialogFooter>
    </>
  );
}
