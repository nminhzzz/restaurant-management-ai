"use client";

import { Plus, Search, ShoppingBag } from "lucide-react";
import { useState } from "react";

import { ErrorState, LoadingState, StatusBadge } from "@/components/page-states";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ApiError, apiFetch } from "@/lib/api-client";
import { formatVnd } from "@/lib/format";
import { useResource } from "@/lib/use-resource";
import { cn } from "@/lib/utils";

import type { FloorBoard, FloorOrder, FloorTable } from "./types";

const FILTERS = [
  { key: "all", label: "Tất cả" },
  { key: "free", label: "Trống" },
  { key: "busy", label: "Có khách" },
  { key: "booked", label: "Đã đặt" },
] as const;
type FilterKey = (typeof FILTERS)[number]["key"];

const loadBoard = () => apiFetch<FloorBoard>("/sales/floor");

function kindOf(table: FloorTable): Exclude<FilterKey, "all"> {
  if (table.order) return "busy";
  return table.TrangThai === "Đã đặt" ? "booked" : "free";
}

function openedAt(order: FloorOrder): string {
  if (!order.MoLuc) return "";
  return new Date(order.MoLuc).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });
}

export function FloorStep({
  onNewOrder,
  onAddMore,
  onPay,
}: {
  onNewOrder: (tableId: number | null) => void;
  onAddMore: (orderId: number, tableId: number | null) => void;
  onPay: (orderId: number, tableId: number | null) => void;
}) {
  const board = useResource(loadBoard);
  const [filter, setFilter] = useState<FilterKey>("all");
  const [selected, setSelected] = useState<number | null>(null);
  const [code, setCode] = useState("");
  const [lookupError, setLookupError] = useState<string | null>(null);

  if (board.status === "loading") return <LoadingState rows={6} />;
  if (board.status === "error") return <ErrorState message={board.message} onRetry={board.reload} />;

  const { tables, takeaway } = board.data;
  const counts = { all: tables.length, free: 0, busy: 0, booked: 0 };
  for (const t of tables) counts[kindOf(t)] += 1;
  const visible = tables.filter((t) => filter === "all" || kindOf(t) === filter);
  const active = tables.find((t) => t.MaBan === selected && t.order) ?? null;
  const activeOrder = active?.order;

  async function lookup(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLookupError(null);
    const needle = code.trim();
    if (!needle) return;
    try {
      const found = await apiFetch<{ items: { MaOrder: number; MaBan: number | null }[] }>(
        `/sales/orders?code=${encodeURIComponent(needle)}&size=1`,
      );
      const order = found.items[0];
      if (!order) {
        setLookupError(`Không tìm thấy order ${needle}.`);
        return;
      }
      onPay(order.MaOrder, order.MaBan ?? null);
    } catch (error: unknown) {
      setLookupError(error instanceof ApiError ? error.message : "Không tra cứu được order.");
    }
  }

  return (
    <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,1fr)_340px]">
      <div className="min-w-0 space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <form role="search" onSubmit={lookup} className="relative w-full sm:w-72">
            <Search className="absolute top-2.5 left-2.5 size-4 text-subtle" aria-hidden />
            <Input
              aria-label="Tra mã order"
              placeholder="Tra mã order, ví dụ ORD-260926-142"
              className="pl-8"
              value={code}
              onChange={(e) => setCode(e.target.value)}
            />
          </form>
          <div role="group" aria-label="Lọc bàn" className="inline-flex overflow-hidden rounded-control border border-border-strong">
            {FILTERS.map((f) => (
              <button
                key={f.key}
                type="button"
                aria-pressed={filter === f.key}
                onClick={() => setFilter(f.key)}
                className={cn(
                  "h-9 px-3 font-semibold not-first:border-l not-first:border-border",
                  filter === f.key ? "bg-primary text-white" : "bg-surface hover:bg-surface-sunken",
                )}
              >
                {f.label} <span className="font-mono text-xs tabular-nums opacity-80">{counts[f.key]}</span>
              </button>
            ))}
          </div>
        </div>
        {lookupError && <p role="alert" className="text-danger-fg">{lookupError}</p>}

        <div className="grid grid-cols-[repeat(auto-fill,minmax(150px,1fr))] gap-2">
          {visible.map((table) => {
            const busy = table.order !== null;
            return (
              <button
                key={table.MaBan}
                type="button"
                aria-pressed={selected === table.MaBan}
                onClick={() => (busy ? setSelected(table.MaBan) : onNewOrder(table.MaBan))}
                className={cn(
                  "grid min-h-28 content-between gap-2 rounded-container border border-border bg-surface p-3 text-left transition-[border-color,box-shadow] hover:border-ink hover:shadow-lift",
                  busy && "shadow-[inset_0_3px_0_0_var(--color-ink)]",
                  selected === table.MaBan && "border-ink ring-1 ring-ink",
                )}
              >
                <span className="flex items-center justify-between gap-2 text-lg font-bold tracking-tight">
                  {table.TenBan}
                  <StatusBadge status={busy ? "Đang phục vụ" : table.TrangThai} />
                </span>
                {table.order ? (
                  <span className="grid gap-0.5 text-xs text-muted">
                    <span className="text-[15px] font-bold text-ink tabular-nums">{formatVnd(table.order.TamTinh)}</span>
                    <span>{table.order.SoMon} món · từ {openedAt(table.order)}</span>
                  </span>
                ) : (
                  <span className="text-xs text-muted">Chạm để mở order</span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      <aside className="space-y-3 lg:sticky lg:top-4">
        {active && activeOrder && (
          <section aria-label={`Order ${active.TenBan}`} className="rounded-container border border-border bg-surface">
            <header className="flex items-center justify-between gap-2 border-b border-border px-4 py-3">
              <h2 className="text-base font-bold">{active.TenBan}</h2>
              <StatusBadge status="Đang phục vụ" />
            </header>
            <div className="space-y-3 p-4">
              <p className="font-mono text-xs text-subtle">
                {activeOrder.MaOrderHienThi} · mở {openedAt(activeOrder)} · {activeOrder.SoMon} món
              </p>
              <p className="flex items-baseline justify-between border-t border-border-strong pt-3 text-lg font-bold">
                <span>Tạm tính</span>
                <span className="tabular-nums">{formatVnd(activeOrder.TamTinh)}</span>
              </p>
              <div className="grid grid-cols-2 gap-2">
                <Button variant="secondary" size="pos" onClick={() => onAddMore(activeOrder.MaOrder, active.MaBan)}>
                  <Plus />
                  Gọi thêm
                </Button>
                <Button size="pos" onClick={() => onPay(activeOrder.MaOrder, active.MaBan)}>
                  Thanh toán
                </Button>
              </div>
            </div>
          </section>
        )}

        <section aria-label="Mang về" className="rounded-container border border-border bg-surface">
          <header className="flex items-center justify-between gap-2 border-b border-border px-4 py-3">
            <h2 className="text-base font-bold">Mang về</h2>
            <Button size="sm" onClick={() => onNewOrder(null)} aria-label="Đơn mang về mới">
              <ShoppingBag />
              Đơn mới
            </Button>
          </header>
          <div className="grid gap-1.5 p-3">
            {takeaway.length === 0 ? (
              <p className="px-1 py-2 text-muted">Chưa có đơn mang về đang mở.</p>
            ) : (
              takeaway.map((order) => (
                <button
                  key={order.MaOrder}
                  type="button"
                  onClick={() => onPay(order.MaOrder, null)}
                  className="flex items-center justify-between gap-2 rounded-control border border-border px-3 py-2.5 text-left hover:border-ink"
                >
                  <span>
                    <span className="block font-mono font-semibold">{order.MaOrderHienThi}</span>
                    <span className="text-xs text-subtle">{order.SoMon} món · {openedAt(order)}</span>
                  </span>
                  <span className="font-bold tabular-nums">{formatVnd(order.TamTinh)}</span>
                </button>
              ))
            )}
          </div>
        </section>
      </aside>
    </div>
  );
}
