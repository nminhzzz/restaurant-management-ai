"use client";

import { KeyRound, Lock, LockOpen, Users } from "lucide-react";
import { useState } from "react";

import { ConfirmDialog } from "@/components/confirm-dialog";
import {
  EmptyState,
  ErrorState,
  LoadingState,
  StatusBadge,
} from "@/components/page-states";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { apiFetch } from "@/lib/api-client";
import { formatDateTime } from "@/lib/format";
import { roleLabel } from "@/lib/roles";
import { useAction } from "@/lib/use-action";
import { useResource } from "@/lib/use-resource";

import { CreateUserDialog } from "./create-user-dialog";
import { ResetPasswordDialog } from "./reset-password-dialog";

export type User = {
  MaNguoiDung: number;
  TenDangNhap: string;
  HoTen: string;
  SoDienThoai: string | null;
  MaVaiTro: string;
  TrangThai: string;
  NgayTao: string;
};

type Page<T> = { items: T[]; total: number };

const LOCKED_STATUS = "Đã khóa";

const loadUsers = () => apiFetch<Page<User>>("/settings/users?size=200");

export function UsersPanel() {
  const users = useResource(loadUsers);
  const { run: runLock, pending: lockPending } = useAction();
  const [lockTarget, setLockTarget] = useState<User | null>(null);
  const [resetTarget, setResetTarget] = useState<User | null>(null);

  const unlocking = lockTarget?.TrangThai === LOCKED_STATUS;

  async function confirmLock() {
    if (!lockTarget) return;
    const result = await runLock(
      () =>
        apiFetch(
          `/settings/users/${lockTarget.MaNguoiDung}/${unlocking ? "unlock" : "lock"}`,
          { method: "PATCH" },
        ),
      `Đã ${unlocking ? "mở khóa" : "khóa"} tài khoản ${lockTarget.HoTen}.`,
    );
    if (result !== undefined) {
      setLockTarget(null);
      users.reload();
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <CreateUserDialog onCreated={users.reload} />
      </div>

      {users.status === "loading" ? (
        <LoadingState />
      ) : users.status === "error" ? (
        <ErrorState message={users.message} onRetry={users.reload} />
      ) : users.data.items.length === 0 ? (
        <EmptyState
          icon={Users}
          title="Chưa có tài khoản nào"
          description="Tài khoản quản lý đầu tiên được tạo khi khởi tạo dữ liệu."
        />
      ) : (
        <Table>
          <caption className="sr-only">Tài khoản người dùng</caption>
          <TableHeader>
            <TableRow>
              <TableHead>Họ tên</TableHead>
              <TableHead>Tên đăng nhập</TableHead>
              <TableHead>Vai trò</TableHead>
              <TableHead>Số điện thoại</TableHead>
              <TableHead>Trạng thái</TableHead>
              <TableHead>Ngày tạo</TableHead>
              <TableHead className="text-right">Thao tác</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {users.data.items.map((u) => (
              <TableRow key={u.MaNguoiDung}>
                <TableCell className="font-medium">{u.HoTen}</TableCell>
                <TableCell className="font-mono text-xs">
                  {u.TenDangNhap}
                </TableCell>
                <TableCell>{roleLabel(u.MaVaiTro)}</TableCell>
                <TableCell className="tabular-nums">
                  {u.SoDienThoai ?? ""}
                </TableCell>
                <TableCell>
                  <StatusBadge status={u.TrangThai} />
                </TableCell>
                <TableCell className="text-muted tabular-nums">
                  {formatDateTime(u.NgayTao)}
                </TableCell>
                <TableCell>
                  <div className="flex justify-end gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      aria-label={`Đặt lại mật khẩu cho ${u.HoTen}`}
                      onClick={() => setResetTarget(u)}
                    >
                      <KeyRound />
                    </Button>
                    {u.TrangThai !== LOCKED_STATUS ? (
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label={`Khóa tài khoản ${u.HoTen}`}
                        onClick={() => setLockTarget(u)}
                      >
                        <Lock />
                      </Button>
                    ) : (
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label={`Mở khóa tài khoản ${u.HoTen}`}
                        onClick={() => setLockTarget(u)}
                      >
                        <LockOpen />
                      </Button>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      <ConfirmDialog
        open={lockTarget !== null}
        onOpenChange={(open) => !open && setLockTarget(null)}
        title={unlocking ? "Mở khóa tài khoản" : "Khóa tài khoản"}
        description={
          lockTarget
            ? unlocking
              ? `Mở khóa tài khoản "${lockTarget.HoTen}"? Người này đăng nhập lại được ngay.`
              : `Khóa tài khoản "${lockTarget.HoTen}"? Người này sẽ không đăng nhập được nữa.`
            : undefined
        }
        confirmLabel={unlocking ? "Mở khóa" : "Khóa tài khoản"}
        danger={!unlocking}
        pending={lockPending}
        onConfirm={confirmLock}
      />
      <ResetPasswordDialog
        user={resetTarget}
        onOpenChange={(open) => !open && setResetTarget(null)}
      />
    </div>
  );
}
