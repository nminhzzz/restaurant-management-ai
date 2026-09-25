"use client";

import { ChevronDown, ChevronRight, History } from "lucide-react";
import { Fragment, useCallback, useState } from "react";

import { EmptyState, ErrorState, LoadingState } from "@/components/page-states";
import { FormField } from "@/components/form-field";
import { Input } from "@/components/ui/input";
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
import { useResource } from "@/lib/use-resource";

type AuditEntry = {
  MaNhatKy: number;
  MaNguoiDung: number;
  ThoiDiem: string;
  LoaiThaoTac: string;
  DoiTuong: string;
  MaDoiTuong: string;
  DuLieuTruoc: Record<string, unknown> | null;
  DuLieuSau: Record<string, unknown> | null;
  LyDo: string | null;
};

type UserBrief = { MaNguoiDung: number; HoTen: string };
type Page<T> = { items: T[]; total: number };

/** FR-SET-08/09: filterable, expandable audit log lookup. */
export function AuditPanel() {
  const [actionFilter, setActionFilter] = useState("");
  const [userFilter, setUserFilter] = useState("");
  const [expanded, setExpanded] = useState<number | null>(null);

  const load = useCallback(async () => {
    const params = new URLSearchParams({ size: "50" });
    if (actionFilter.trim()) params.set("action", actionFilter.trim());
    if (userFilter.trim()) params.set("user_id", userFilter.trim());
    const [audit, users] = await Promise.all([
      apiFetch<Page<AuditEntry>>(`/settings/audit-log?${params.toString()}`),
      apiFetch<Page<UserBrief>>("/settings/users?size=200").catch(() => ({
        items: [],
        total: 0,
      })),
    ]);
    return {
      entries: audit.items,
      names: new Map(users.items.map((u) => [u.MaNguoiDung, u.HoTen])),
    };
  }, [actionFilter, userFilter]);

  const data = useResource(load);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-3">
        <FormField id="audit-action" label="Loại thao tác">
          <Input
            id="audit-action"
            placeholder="VD: LOCK_USER"
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
          />
        </FormField>
        <FormField id="audit-user" label="Mã người thực hiện">
          <Input
            id="audit-user"
            inputMode="numeric"
            value={userFilter}
            onChange={(e) => setUserFilter(e.target.value)}
          />
        </FormField>
      </div>

      {data.status === "loading" ? (
        <LoadingState />
      ) : data.status === "error" ? (
        <ErrorState message={data.message} onRetry={data.reload} />
      ) : data.data.entries.length === 0 ? (
        <EmptyState
          icon={History}
          title="Chưa có thao tác nào được ghi"
          description="Các thao tác rủi ro như hủy order, đổi giá, khóa tài khoản sẽ xuất hiện ở đây."
        />
      ) : (
        <Table>
          <caption className="sr-only">Nhật ký thao tác</caption>
          <TableHeader>
            <TableRow>
              <TableHead className="w-8" />
              <TableHead>Thời điểm</TableHead>
              <TableHead>Thao tác</TableHead>
              <TableHead>Đối tượng</TableHead>
              <TableHead>Người thực hiện</TableHead>
              <TableHead>Lý do</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.data.entries.map((entry) => {
              const isOpen = expanded === entry.MaNhatKy;
              const hasDetail =
                entry.DuLieuTruoc !== null || entry.DuLieuSau !== null;
              return (
                <Fragment key={entry.MaNhatKy}>
                  <TableRow>
                    <TableCell>
                      {hasDetail ? (
                        <button
                          type="button"
                          aria-label={
                            isOpen
                              ? `Thu gọn chi tiết #${entry.MaNhatKy}`
                              : `Xem chi tiết #${entry.MaNhatKy}`
                          }
                          onClick={() =>
                            setExpanded(isOpen ? null : entry.MaNhatKy)
                          }
                          className="text-subtle hover:text-ink"
                        >
                          {isOpen ? (
                            <ChevronDown className="size-4" />
                          ) : (
                            <ChevronRight className="size-4" />
                          )}
                        </button>
                      ) : null}
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-muted tabular-nums">
                      {formatDateTime(entry.ThoiDiem)}
                    </TableCell>
                    <TableCell className="font-medium">
                      {entry.LoaiThaoTac}
                    </TableCell>
                    <TableCell>
                      {entry.DoiTuong}{" "}
                      <span className="font-mono text-xs text-subtle">
                        #{entry.MaDoiTuong}
                      </span>
                    </TableCell>
                    <TableCell className="tabular-nums">
                      {data.data.names.get(entry.MaNguoiDung) ??
                        `#${entry.MaNguoiDung}`}
                    </TableCell>
                    <TableCell className="text-muted">
                      {entry.LyDo ?? ""}
                    </TableCell>
                  </TableRow>
                  {isOpen ? (
                    <TableRow>
                      <TableCell colSpan={6} className="bg-surface-sunken">
                        <div className="grid gap-3 py-2 sm:grid-cols-2">
                          <div>
                            <p className="mb-1 text-xs font-medium text-subtle uppercase">
                              Trước
                            </p>
                            <pre className="overflow-x-auto rounded-control bg-surface p-2 font-mono text-xs">
                              {entry.DuLieuTruoc
                                ? JSON.stringify(entry.DuLieuTruoc, null, 2)
                                : "—"}
                            </pre>
                          </div>
                          <div>
                            <p className="mb-1 text-xs font-medium text-subtle uppercase">
                              Sau
                            </p>
                            <pre className="overflow-x-auto rounded-control bg-surface p-2 font-mono text-xs">
                              {entry.DuLieuSau
                                ? JSON.stringify(entry.DuLieuSau, null, 2)
                                : "—"}
                            </pre>
                          </div>
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : null}
                </Fragment>
              );
            })}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
