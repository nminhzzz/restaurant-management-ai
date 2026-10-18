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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { apiFetch } from "@/lib/api-client";
import { roleLabel } from "@/lib/roles";
import { useAction } from "@/lib/use-action";

import type { User } from "./users-panel";

const ROLES = ["MANAGER", "CASHIER", "WAREHOUSE"] as const;
type RoleValue = (typeof ROLES)[number];

/** FR-SET-01: edit an account and assign one of the three roles. */
export function EditUserDialog({
  user,
  onOpenChange,
  onUpdated,
}: {
  user: User | null;
  onOpenChange: (open: boolean) => void;
  onUpdated: () => void;
}) {
  return (
    <Dialog open={user !== null} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Sửa tài khoản {user?.TenDangNhap}</DialogTitle>
        </DialogHeader>
        {user ? (
          <EditUserForm
            key={user.MaNguoiDung}
            user={user}
            onCancel={() => onOpenChange(false)}
            onUpdated={() => {
              onOpenChange(false);
              onUpdated();
            }}
          />
        ) : null}
      </DialogContent>
    </Dialog>
  );
}

function EditUserForm({
  user,
  onCancel,
  onUpdated,
}: {
  user: User;
  onCancel: () => void;
  onUpdated: () => void;
}) {
  const [fullName, setFullName] = useState(user.HoTen);
  const [phone, setPhone] = useState(user.SoDienThoai ?? "");
  const [role, setRole] = useState<RoleValue>(user.MaVaiTro as RoleValue);
  const { run, pending } = useAction();

  async function save() {
    if (fullName.trim() === "") return;
    const result = await run(
      () =>
        apiFetch(`/settings/users/${user.MaNguoiDung}`, {
          method: "PATCH",
          body: {
            full_name: fullName.trim(),
            phone: phone.trim() || null,
            role,
          },
        }),
      "Đã cập nhật tài khoản.",
    );
    if (result !== undefined) onUpdated();
  }

  return (
    <>
      <div className="space-y-3">
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
        <FormField id="edit-user-role" label="Vai trò">
          <Select
            value={role}
            onValueChange={(value) => setRole(value as RoleValue)}
          >
            <SelectTrigger id="edit-user-role">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {ROLES.map((item) => (
                <SelectItem key={item} value={item}>
                  {roleLabel(item)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </FormField>
      </div>
      <DialogFooter>
        <Button variant="secondary" onClick={onCancel}>
          Quay lại
        </Button>
        <Button disabled={pending || fullName.trim() === ""} onClick={save}>
          Lưu thay đổi
        </Button>
      </DialogFooter>
    </>
  );
}
