"use client";

import { UserPlus } from "lucide-react";
import { useState } from "react";

import { FormField } from "@/components/form-field";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
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

const ROLES = ["MANAGER", "CASHIER", "WAREHOUSE"] as const;

type NewUserForm = {
  HoTen: string;
  TenDangNhap: string;
  SoDienThoai: string;
  MaVaiTro: (typeof ROLES)[number];
  MatKhau: string;
};

const EMPTY: NewUserForm = {
  HoTen: "",
  TenDangNhap: "",
  SoDienThoai: "",
  MaVaiTro: "CASHIER",
  MatKhau: "",
};

/** FR-SET-01: create a staff account. */
export function CreateUserDialog({ onCreated }: { onCreated: () => void }) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<NewUserForm>(EMPTY);
  const { run, pending } = useAction();

  const usernameError =
    form.TenDangNhap.length > 0 && form.TenDangNhap.trim().length < 3
      ? "Tên đăng nhập tối thiểu 3 ký tự."
      : null;
  const passwordError =
    form.MatKhau.length > 0 && form.MatKhau.length < 6
      ? "Mật khẩu tối thiểu 6 ký tự."
      : null;
  const canSubmit =
    form.HoTen.trim() !== "" &&
    form.TenDangNhap.trim().length >= 3 &&
    form.MatKhau.length >= 6;

  function close(next: boolean) {
    setOpen(next);
    if (!next) setForm(EMPTY);
  }

  async function submit() {
    const result = await run(
      () =>
        apiFetch("/settings/users", {
          method: "POST",
          body: {
            username: form.TenDangNhap.trim(),
            password: form.MatKhau,
            full_name: form.HoTen.trim(),
            phone: form.SoDienThoai.trim() || null,
            role: form.MaVaiTro,
          },
        }),
      "Đã tạo tài khoản.",
    );
    if (result !== undefined) {
      close(false);
      onCreated();
    }
  }

  return (
    <Dialog open={open} onOpenChange={close}>
      <DialogTrigger asChild>
        <Button>
          <UserPlus />
          Thêm tài khoản
        </Button>
      </DialogTrigger>
      <DialogContent className="w-[min(28rem,calc(100vw-2rem))]">
        <DialogHeader>
          <DialogTitle>Thêm tài khoản</DialogTitle>
        </DialogHeader>
        <div className="space-y-3">
          <FormField id="new-user-name" label="Họ tên">
            <Input
              id="new-user-name"
              value={form.HoTen}
              onChange={(e) => setForm({ ...form, HoTen: e.target.value })}
            />
          </FormField>
          <FormField
            id="new-user-username"
            label="Tên đăng nhập"
            error={usernameError}
          >
            <Input
              id="new-user-username"
              value={form.TenDangNhap}
              onChange={(e) =>
                setForm({ ...form, TenDangNhap: e.target.value })
              }
            />
          </FormField>
          <FormField id="new-user-phone" label="Số điện thoại">
            <Input
              id="new-user-phone"
              value={form.SoDienThoai}
              onChange={(e) =>
                setForm({ ...form, SoDienThoai: e.target.value })
              }
            />
          </FormField>
          <FormField id="new-user-role" label="Vai trò">
            <Select
              value={form.MaVaiTro}
              onValueChange={(value) =>
                setForm({ ...form, MaVaiTro: value as NewUserForm["MaVaiTro"] })
              }
            >
              <SelectTrigger id="new-user-role">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ROLES.map((role) => (
                  <SelectItem key={role} value={role}>
                    {roleLabel(role)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </FormField>
          <FormField
            id="new-user-password"
            label="Mật khẩu ban đầu"
            error={passwordError}
          >
            <Input
              id="new-user-password"
              type="password"
              value={form.MatKhau}
              onChange={(e) => setForm({ ...form, MatKhau: e.target.value })}
            />
          </FormField>
        </div>
        <DialogFooter>
          <Button variant="secondary" onClick={() => close(false)}>
            Quay lại
          </Button>
          <Button disabled={pending || !canSubmit} onClick={submit}>
            Tạo tài khoản
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
