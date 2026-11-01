"use client";

import { Search } from "lucide-react";
import { useState } from "react";

import { EmptyState, ErrorState, LoadingState } from "@/components/page-states";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ApiError, apiFetch } from "@/lib/api-client";
import { formatDate } from "@/lib/format";

import type { FloorTable } from "./types";

type FoundOrder = {
  MaOrder: number;
  MaOrderHienThi: string;
  MaBan: number | null;
  BusinessDate: string;
  TrangThai: string;
};

export const ORDER_STATUSES = [
  "Đang mở",
  "Chờ xác nhận thanh toán",
  "Chờ xác minh thanh toán",
  "Đã thanh toán",
  "Đóng – chưa thu được tiền",
  "Đã hủy",
];

export function OrderLookupDialog({
  open,
  onOpenChange,
  tables,
  onOpenOrder,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  tables: FloorTable[];
  onOpenOrder: (orderId: number, tableId: number | null) => void;
}) {
  const [code, setCode] = useState("");
  const [tableId, setTableId] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [status, setStatus] = useState("");
  const [results, setResults] = useState<FoundOrder[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function search() {
    setLoading(true);
    setError(null);
    const query = new URLSearchParams({ size: "50" });
    if (code.trim()) query.set("code", code.trim());
    if (tableId) query.set("table_id", tableId);
    if (from) query.set("date_from", from);
    if (to) query.set("date_to", to);
    if (status) query.set("status", status);
    try {
      const found = await apiFetch<{ items: FoundOrder[] }>(
        `/sales/orders?${query.toString()}`,
      );
      setResults(found.items);
    } catch (cause) {
      setError(
        cause instanceof ApiError ? cause.message : "Không tra cứu được order.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-[min(46rem,calc(100vw-2rem))]">
        <DialogHeader>
          <DialogTitle>Tra cứu order</DialogTitle>
        </DialogHeader>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="grid gap-1.5">
            <Label htmlFor="lookup-code">Mã order</Label>
            <Input
              id="lookup-code"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="ORD-..."
            />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="lookup-table">Bàn</Label>
            <Select value={tableId} onValueChange={setTableId}>
              <SelectTrigger id="lookup-table">
                <SelectValue placeholder="Tất cả bàn" />
              </SelectTrigger>
              <SelectContent>
                {tables.map((table) => (
                  <SelectItem key={table.MaBan} value={String(table.MaBan)}>
                    {table.TenBan}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="lookup-from">Từ Business Date</Label>
            <Input
              id="lookup-from"
              type="date"
              value={from}
              onChange={(e) => setFrom(e.target.value)}
            />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="lookup-to">Đến Business Date</Label>
            <Input
              id="lookup-to"
              type="date"
              value={to}
              onChange={(e) => setTo(e.target.value)}
            />
          </div>
          <div className="grid gap-1.5 sm:col-span-2">
            <Label htmlFor="lookup-status">Trạng thái</Label>
            <Select value={status} onValueChange={setStatus}>
              <SelectTrigger id="lookup-status">
                <SelectValue placeholder="Tất cả trạng thái" />
              </SelectTrigger>
              <SelectContent>
                {ORDER_STATUSES.map((value) => (
                  <SelectItem key={value} value={value}>
                    {value}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <Button onClick={search} disabled={loading}>
          <Search />
          Tìm kiếm
        </Button>

        {error && <ErrorState message={error} onRetry={search} />}
        {loading && <LoadingState rows={3} />}
        {!loading && results !== null && results.length === 0 && (
          <EmptyState
            icon={Search}
            title="Không tìm thấy order"
            description="Thử bỏ bớt điều kiện hoặc chọn khoảng ngày rộng hơn."
          />
        )}
        {!loading && results !== null && results.length > 0 && (
          <ul className="max-h-80 divide-y divide-border overflow-y-auto rounded-control border border-border">
            {results.map((order) => (
              <li
                key={order.MaOrder}
                className="flex flex-wrap items-center justify-between gap-2 px-3 py-2"
              >
                <div>
                  <p className="font-mono text-sm font-semibold">
                    {order.MaOrderHienThi}
                  </p>
                  <p className="text-xs text-muted">
                    {order.MaBan === null ? "Mang về" : `Bàn ${order.MaBan}`} ·{" "}
                    {formatDate(order.BusinessDate)} · {order.TrangThai}
                  </p>
                </div>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => {
                    onOpenOrder(order.MaOrder, order.MaBan);
                    onOpenChange(false);
                  }}
                >
                  Mở
                </Button>
              </li>
            ))}
          </ul>
        )}
      </DialogContent>
    </Dialog>
  );
}
