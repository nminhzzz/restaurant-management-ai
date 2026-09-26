"use client";

import { ChevronRight, Search } from "lucide-react";
import { useCallback, useState } from "react";

import { DataPagination } from "@/components/data-pagination";
import { DateRangeFilter } from "@/components/filter-bar";
import { StatusBadge } from "@/components/page-states";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api-client";
import { formatDate } from "@/lib/format";
import { useResource } from "@/lib/use-resource";
import { cn } from "@/lib/utils";

type OrderRow = {
  MaOrder: number;
  MaOrderHienThi: string | null;
  MaBan: number | null;
  BusinessDate: string;
  TrangThai: string;
};

type Filters = {
  code: string;
  tableId: string;
  dateFrom: string;
  dateTo: string;
  status: string;
};

const STATUSES = [
  "Đang mở",
  "Chờ đối soát",
  "Đã thanh toán",
  "Đã hủy",
  "Tự động đóng",
];

const PAGE_SIZE = 20;

// Opening the tab should already answer "which tables are still eating?".
const INITIAL: Filters = {
  code: "",
  tableId: "",
  dateFrom: "",
  dateTo: "",
  status: "Đang mở",
};

const loadTableNames = () =>
  apiFetch<{ MaBan: number; TenBan: string }[]>("/catalog/tables").then(
    (rows) =>
      new Map(
        (Array.isArray(rows) ? rows : []).map((t) => [t.MaBan, t.TenBan]),
      ),
  );

// The Business Date range replaces the old single exact-match `business_date`
// param; a from == to range covers the same case.
function queryOf(filters: Filters, page: number): string {
  const params = new URLSearchParams();
  if (filters.code.trim()) params.set("code", filters.code.trim());
  if (filters.tableId) params.set("table_id", filters.tableId);
  if (filters.status) params.set("status", filters.status);
  if (filters.dateFrom) params.set("date_from", filters.dateFrom);
  if (filters.dateTo) params.set("date_to", filters.dateTo);
  params.set("page", String(page));
  params.set("size", String(PAGE_SIZE));
  return `/sales/orders?${params.toString()}`;
}

const selectClass =
  "h-11 w-full rounded-control border border-border bg-surface px-3 text-ink focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none";

export function OrderLookup({
  onSelect,
  selectedId,
}: {
  onSelect?: (orderId: number) => void;
  selectedId?: number | null;
} = {}) {
  const [draft, setDraft] = useState<Filters>(INITIAL);
  const [applied, setApplied] = useState<Filters>(INITIAL);
  const [page, setPage] = useState(1);
  const tables = useResource(loadTableNames);
  const fetchOrders = useCallback(
    () =>
      apiFetch<{ items: OrderRow[]; total: number }>(queryOf(applied, page)),
    [applied, page],
  );
  const orders = useResource(fetchOrders);
  const tableName = (id: number) =>
    (tables.status === "ready" && tables.data.get(id)) || `Bàn #${id}`;

  function search(event: React.FormEvent) {
    event.preventDefault();
    setApplied({ ...draft });
    setPage(1);
  }

  function update(patch: Partial<Filters>) {
    setDraft((previous) => ({ ...previous, ...patch }));
  }

  return (
    <section className="space-y-3 rounded-container border border-border bg-surface p-4">
      <h2 className="text-base font-bold">Tra cứu order</h2>
      <form onSubmit={search} className="space-y-2">
        <div className="relative">
          <Search
            className="absolute top-3.5 left-2.5 size-4 text-subtle"
            aria-hidden
          />
          <Input
            aria-label="Mã order"
            placeholder="Mã order, ví dụ ORD-250926-042"
            className="h-11 pl-8 font-mono"
            value={draft.code}
            onChange={(e) => update({ code: e.target.value })}
          />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <select
            aria-label="Bàn"
            className={selectClass}
            value={draft.tableId}
            onChange={(e) => update({ tableId: e.target.value })}
          >
            <option value="">Mọi bàn</option>
            {tables.status === "ready" &&
              [...tables.data].map(([id, name]) => (
                <option key={id} value={String(id)}>
                  {name}
                </option>
              ))}
          </select>
          <select
            aria-label="Trạng thái"
            className={selectClass}
            value={draft.status}
            onChange={(e) => update({ status: e.target.value })}
          >
            <option value="">Mọi trạng thái</option>
            {STATUSES.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <DateRangeFilter
            from={draft.dateFrom}
            to={draft.dateTo}
            onChange={({ from, to }) => update({ dateFrom: from, dateTo: to })}
          />
          <Button type="submit" variant="secondary" size="pos">
            Tìm
          </Button>
        </div>
      </form>

      {orders.status === "loading" ? (
        <div role="status" className="space-y-2">
          <span className="sr-only">Đang tải…</span>
          <Skeleton className="h-14" />
          <Skeleton className="h-14" />
        </div>
      ) : orders.status === "error" ? (
        <p className="text-danger-fg">{orders.message}</p>
      ) : orders.data.items.length === 0 ? (
        <p className="py-4 text-center text-muted">
          Không có order nào khớp bộ lọc.
        </p>
      ) : (
        <ul className="-mx-2 max-h-[28rem] space-y-1 overflow-y-auto">
          {orders.data.items.map((o) => (
            <li key={o.MaOrder}>
              <button
                type="button"
                onClick={() => onSelect?.(o.MaOrder)}
                aria-label={`Chọn ${o.MaOrderHienThi}`}
                aria-current={selectedId === o.MaOrder ? "true" : undefined}
                className={cn(
                  "flex min-h-14 w-full items-center gap-3 rounded-control px-2 text-left transition-colors",
                  selectedId === o.MaOrder
                    ? "bg-primary-subtle"
                    : "hover:bg-surface-sunken",
                )}
              >
                <span className="min-w-0 flex-1">
                  <span className="block font-mono font-medium">
                    {o.MaOrderHienThi}
                  </span>
                  <span className="text-xs text-muted">
                    {o.MaBan === null ? "Mang về" : tableName(o.MaBan)},{" "}
                    {formatDate(o.BusinessDate)}
                  </span>
                </span>
                <StatusBadge status={o.TrangThai} />
                <ChevronRight className="size-4 text-subtle" aria-hidden />
              </button>
            </li>
          ))}
        </ul>
      )}

      {orders.status === "ready" && orders.data.items.length > 0 ? (
        <DataPagination
          page={page}
          pageSize={PAGE_SIZE}
          total={orders.data.total}
          onPageChange={setPage}
        />
      ) : null}
    </section>
  );
}
