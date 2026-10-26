"use client";

import { ArrowLeft, ClipboardList } from "lucide-react";
import { useCallback, useState } from "react";

import { DataPagination } from "@/components/data-pagination";
import {
  DateRangeFilter,
  FilterBar,
  SearchFilter,
  SelectFilter,
} from "@/components/filter-bar";
import {
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
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
import { formatDate, formatVnd } from "@/lib/format";
import { useResource } from "@/lib/use-resource";

import { OrderDetail } from "./order-detail";
import { ORDER_STATUSES } from "./order-lookup";
import { PaymentPanel } from "./payment-panel";

type OrderRow = {
  MaOrder: number;
  MaOrderHienThi: string;
  LoaiDon: string;
  MaBan: number | null;
  TenBan: string | null;
  BusinessDate: string;
  NguoiLap: string | null;
  TrangThai: string;
  TongTien: number;
};

const PAGE_SIZE = 20;

/** FR-SALE-25: the Manager's order list, combined filters and per-order detail. */
export function OrderManagement() {
  const [page, setPage] = useState(1);
  const [code, setCode] = useState("");
  const [tableId, setTableId] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [status, setStatus] = useState("");
  const [selected, setSelected] = useState<number | null>(null);

  const active =
    code !== "" ||
    tableId !== "" ||
    dateFrom !== "" ||
    dateTo !== "" ||
    status !== "";

  function resetFilters() {
    setCode("");
    setTableId("");
    setDateFrom("");
    setDateTo("");
    setStatus("");
    setPage(1);
  }

  const loadTables = useCallback(
    () => apiFetch<{ MaBan: number; TenBan: string }[]>("/catalog/tables"),
    [],
  );
  const tables = useResource(loadTables);

  const load = useCallback(() => {
    const params = new URLSearchParams({
      page: String(page),
      size: String(PAGE_SIZE),
    });
    if (code.trim()) params.set("code", code.trim());
    if (tableId) params.set("table_id", tableId);
    if (dateFrom) params.set("date_from", dateFrom);
    if (dateTo) params.set("date_to", dateTo);
    if (status) params.set("status", status);
    return apiFetch<{ items: OrderRow[]; total: number }>(
      `/sales/orders?${params.toString()}`,
    );
  }, [page, code, tableId, dateFrom, dateTo, status]);
  const orders = useResource(load);

  if (selected !== null) {
    return (
      <div className="space-y-5">
        <PageHeader
          title="Chi tiết order"
          actions={
            <Button variant="secondary" onClick={() => setSelected(null)}>
              <ArrowLeft />
              Quay lại danh sách
            </Button>
          }
        />
        <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
          <OrderDetail key={`detail-${selected}`} orderId={selected} />
          <PaymentPanel key={`payment-${selected}`} orderId={selected} />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <PageHeader title="Quản lý đơn hàng" />
      <FilterBar active={active} onReset={resetFilters}>
        <SearchFilter
          label="Mã order"
          value={code}
          onChange={(v) => {
            setCode(v);
            setPage(1);
          }}
        />
        <SelectFilter
          label="Bàn"
          value={tableId}
          onChange={(v) => {
            setTableId(v);
            setPage(1);
          }}
          allLabel="Tất cả bàn"
          options={(tables.status === "ready" ? tables.data : []).map((t) => ({
            value: String(t.MaBan),
            label: t.TenBan,
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
        <SelectFilter
          label="Trạng thái"
          value={status}
          onChange={(v) => {
            setStatus(v);
            setPage(1);
          }}
          allLabel="Tất cả trạng thái"
          options={ORDER_STATUSES.map((value) => ({ value, label: value }))}
        />
      </FilterBar>

      {orders.status === "loading" ? (
        <LoadingState />
      ) : orders.status === "error" ? (
        <ErrorState message={orders.message} onRetry={orders.reload} />
      ) : orders.data.items.length === 0 ? (
        <EmptyState
          icon={ClipboardList}
          title="Không có order phù hợp"
          description="Bỏ bớt điều kiện lọc hoặc chọn khoảng ngày kinh doanh rộng hơn."
        />
      ) : (
        <>
          <Table>
            <caption className="sr-only">Danh sách order</caption>
            <TableHeader>
              <TableRow>
                <TableHead>Mã order</TableHead>
                <TableHead>Loại đơn</TableHead>
                <TableHead>Bàn</TableHead>
                <TableHead>Ngày kinh doanh</TableHead>
                <TableHead>Người lập</TableHead>
                <TableHead>Trạng thái</TableHead>
                <TableHead className="text-right">Tổng tiền</TableHead>
                <TableHead className="w-0" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {orders.data.items.map((order) => (
                <TableRow key={order.MaOrder}>
                  <TableCell className="font-mono text-sm font-semibold">
                    {order.MaOrderHienThi}
                  </TableCell>
                  <TableCell>{order.LoaiDon}</TableCell>
                  <TableCell>{order.TenBan ?? "—"}</TableCell>
                  <TableCell className="tabular-nums">
                    {formatDate(order.BusinessDate)}
                  </TableCell>
                  <TableCell>{order.NguoiLap ?? "—"}</TableCell>
                  <TableCell>
                    <StatusBadge status={order.TrangThai} />
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatVnd(order.TongTien)}
                  </TableCell>
                  <TableCell>
                    <Button
                      size="sm"
                      variant="secondary"
                      aria-label={`Xem order ${order.MaOrderHienThi}`}
                      onClick={() => setSelected(order.MaOrder)}
                    >
                      Xem
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <DataPagination
            page={page}
            pageSize={PAGE_SIZE}
            total={orders.data.total}
            onPageChange={setPage}
          />
        </>
      )}
    </div>
  );
}
