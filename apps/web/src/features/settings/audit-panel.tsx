"use client";

import { ChevronDown, ChevronRight, History } from "lucide-react";
import { Fragment, useCallback, useState } from "react";

import { DataPagination } from "@/components/data-pagination";
import {
  DateRangeFilter,
  FilterBar,
  SelectFilter,
} from "@/components/filter-bar";
import { EmptyState, ErrorState, LoadingState } from "@/components/page-states";
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

const PAGE_SIZE = 20;

// Vietnamese labels for the known target entities (physical table names, tokens.md §8).
const TARGET_LABELS: Record<string, string> = {
  BAN: "Bàn",
  CAU_HINH_HE_THONG: "Cấu hình hệ thống",
  CHI_TIET_ORDER: "Dòng order",
  CONG_THUC: "Công thức món",
  GIA_BINH_QUAN_THANG: "Giá vốn bình quân tháng",
  GIAO_DICH_THANH_TOAN: "Giao dịch thanh toán",
  LICH_SU_GIA_MON: "Lịch sử giá món",
  MON_AN: "Món ăn",
  NGUOI_DUNG: "Tài khoản người dùng",
  NGUYEN_LIEU: "Nguyên liệu",
  NHA_CUNG_CAP: "Nhà cung cấp",
  NHOM_MON: "Nhóm món",
  ORDER: "Order",
  PHIEU_KIEM_KE: "Phiếu kiểm kê",
  PHIEU_NHAP_KHO: "Phiếu nhập kho",
  PHIEU_XUAT_KHO: "Phiếu xuất kho",
  SYSTEM: "Hệ thống",
};

function targetLabel(target: string): string {
  return TARGET_LABELS[target] ?? target;
}

/** FR-SET-08/09: filterable, expandable, server-paged audit log lookup. */
export function AuditPanel() {
  const [page, setPage] = useState(1);
  const [actionFilter, setActionFilter] = useState("");
  const [userFilter, setUserFilter] = useState("");
  const [targetFilter, setTargetFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [expanded, setExpanded] = useState<number | null>(null);

  const active =
    actionFilter !== "" ||
    userFilter !== "" ||
    targetFilter !== "" ||
    dateFrom !== "" ||
    dateTo !== "";

  function resetFilters() {
    setActionFilter("");
    setUserFilter("");
    setTargetFilter("");
    setDateFrom("");
    setDateTo("");
    setPage(1);
  }

  const loadActions = useCallback(
    () => apiFetch<string[]>("/settings/audit-log/actions"),
    [],
  );
  const actions = useResource(loadActions);

  const load = useCallback(async () => {
    const params = new URLSearchParams({
      page: String(page),
      size: String(PAGE_SIZE),
    });
    if (actionFilter) params.set("action", actionFilter);
    if (userFilter) params.set("user_id", userFilter);
    if (targetFilter) params.set("target", targetFilter);
    if (dateFrom) params.set("date_from", dateFrom);
    if (dateTo) params.set("date_to", dateTo);
    const [audit, users] = await Promise.all([
      apiFetch<Page<AuditEntry> & { page: number; size: number }>(
        `/settings/audit-log?${params.toString()}`,
      ),
      apiFetch<Page<UserBrief>>("/settings/users?size=200").catch(() => ({
        items: [],
        total: 0,
      })),
    ]);
    return {
      entries: audit.items,
      total: audit.total,
      users: users.items,
      names: new Map(users.items.map((u) => [u.MaNguoiDung, u.HoTen])),
    };
  }, [page, actionFilter, userFilter, targetFilter, dateFrom, dateTo]);

  const data = useResource(load);

  return (
    <div className="space-y-4">
      <FilterBar active={active} onReset={resetFilters}>
        <SelectFilter
          label="Loại thao tác"
          value={actionFilter}
          onChange={(v) => {
            setActionFilter(v);
            setPage(1);
          }}
          allLabel="Tất cả thao tác"
          options={(actions.status === "ready" ? actions.data : []).map(
            (a) => ({
              value: a,
              label: a,
            }),
          )}
        />
        <SelectFilter
          label="Người thực hiện"
          value={userFilter}
          onChange={(v) => {
            setUserFilter(v);
            setPage(1);
          }}
          allLabel="Tất cả người dùng"
          options={(data.status === "ready" ? data.data.users : []).map(
            (u) => ({
              value: String(u.MaNguoiDung),
              label: u.HoTen,
            }),
          )}
        />
        <SelectFilter
          label="Đối tượng"
          value={targetFilter}
          onChange={(v) => {
            setTargetFilter(v);
            setPage(1);
          }}
          allLabel="Tất cả đối tượng"
          options={Object.keys(TARGET_LABELS).map((target) => ({
            value: target,
            label: targetLabel(target),
          }))}
        />
        <DateRangeFilter
          from={dateFrom}
          to={dateTo}
          onChange={({ from, to }) => {
            setDateFrom(from);
            setDateTo(to);
            setPage(1);
          }}
        />
      </FilterBar>

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
        <>
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
          <DataPagination
            page={page}
            pageSize={PAGE_SIZE}
            total={data.data.total}
            onPageChange={setPage}
          />
        </>
      )}
    </div>
  );
}
