"use client";

import {
  CircleAlert,
  CircleCheck,
  Minus,
  PencilLine,
  Plus,
  Search,
  ShoppingBasket,
  Trash2,
  UtensilsCrossed,
} from "lucide-react";
import { useState } from "react";

import { EmptyState, ErrorState, LoadingState } from "@/components/page-states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ApiError, apiFetch } from "@/lib/api-client";
import { formatVnd } from "@/lib/format";
import { useResource } from "@/lib/use-resource";
import { cn } from "@/lib/utils";

type Dish = {
  MaMon: number;
  TenMon: string;
  TrangThai?: string;
  MaNhomMon?: number | null;
  GiaHienTai?: number | null;
};

type DiningTable = { MaBan: number; TenBan: string };
type Group = { MaNhomMon: number; TenNhom: string };

type CartLine = {
  MaMon: number;
  TenMon: string;
  DonGia: number;
  SoLuong: number;
  GhiChu: string;
};

type CreatedOrder = {
  MaOrder: number;
  MaOrderHienThi: string;
  rejected?: { MaMon: number; reason: string }[];
};

const ORDER_TYPES = ["Tại chỗ", "Mang về"] as const;
const UNSELLABLE = new Set(["Hết nguyên liệu", "Ẩn", "Nháp"]);

function messageOf(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback;
}

async function loadMenu() {
  const [tables, dishPage, groups] = await Promise.all([
    apiFetch<DiningTable[]>("/catalog/tables"),
    apiFetch<{ items: Dish[] }>("/catalog/dishes?size=200"),
    apiFetch<Group[]>("/catalog/groups").catch(() => []),
  ]);
  return {
    tables: Array.isArray(tables) ? tables : [],
    dishes: (dishPage.items || []).filter(
      (d) => !UNSELLABLE.has(d.TrangThai ?? ""),
    ),
    groups: Array.isArray(groups) ? groups : [],
  };
}

function Chip({
  name,
  value,
  checked,
  onChange,
  children,
}: {
  name: string;
  value: string;
  checked: boolean;
  onChange: (value: string) => void;
  children: string;
}) {
  return (
    <label
      className={cn(
        "inline-flex h-11 min-w-16 cursor-pointer items-center justify-center rounded-full border px-4 font-medium transition-colors has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-primary has-[:focus-visible]:ring-offset-2",
        checked
          ? "border-primary bg-primary text-white"
          : "border-border bg-surface hover:border-border-strong",
      )}
    >
      <input
        type="radio"
        name={name}
        value={value}
        checked={checked}
        onChange={() => onChange(value)}
        className="sr-only"
      />
      {children}
    </label>
  );
}

export function OrderScreen({
  onOrderCreated,
  onPayNow,
}: {
  onOrderCreated?: (orderId: number) => void;
  onPayNow?: (orderId: number) => void;
} = {}) {
  const menu = useResource(loadMenu);
  const [tableId, setTableId] = useState("");
  const [orderType, setOrderType] = useState<string>("Tại chỗ");
  const [groupId, setGroupId] = useState<number | null>(null);
  const [query, setQuery] = useState("");
  const [cart, setCart] = useState<CartLine[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState<{ id: number; text: string } | null>(
    null,
  );
  const [submitting, setSubmitting] = useState(false);

  if (menu.status === "loading") return <LoadingState rows={6} />;
  if (menu.status === "error")
    return <ErrorState message={menu.message} onRetry={menu.reload} />;

  const { tables, dishes, groups } = menu.data;
  const usedGroups = groups.filter((g) =>
    dishes.some((d) => d.MaNhomMon === g.MaNhomMon),
  );
  const needle = query.trim().toLowerCase();
  const visible = dishes.filter(
    (d) =>
      (groupId === null || d.MaNhomMon === groupId) &&
      (!needle || d.TenMon.toLowerCase().includes(needle)),
  );
  const tableName = tables.find((t) => String(t.MaBan) === tableId)?.TenBan;
  const itemCount = cart.reduce((sum, l) => sum + l.SoLuong, 0);
  const total = cart.reduce((sum, l) => sum + l.SoLuong * l.DonGia, 0);

  function addDish(dish: Dish) {
    setCreated(null);
    setCart((prev) => {
      const existing = prev.find((l) => l.MaMon === dish.MaMon);
      if (existing) {
        return prev.map((l) =>
          l.MaMon === dish.MaMon ? { ...l, SoLuong: l.SoLuong + 1 } : l,
        );
      }
      return [
        ...prev,
        {
          MaMon: dish.MaMon,
          TenMon: dish.TenMon,
          DonGia: dish.GiaHienTai ?? 0,
          SoLuong: 1,
          GhiChu: "",
        },
      ];
    });
  }

  function updateLine(dishId: number, patch: Partial<CartLine>) {
    setCart((prev) =>
      prev.map((l) => (l.MaMon === dishId ? { ...l, ...patch } : l)),
    );
  }

  function step(line: CartLine, delta: number) {
    if (line.SoLuong + delta <= 0) {
      setCart((prev) => prev.filter((l) => l.MaMon !== line.MaMon));
    } else {
      updateLine(line.MaMon, { SoLuong: line.SoLuong + delta });
    }
  }

  async function submit() {
    setError(null);
    setCreated(null);
    if (orderType === "Tại chỗ" && tableId === "") {
      setError("Chọn bàn trước khi gửi order.");
      return;
    }
    if (cart.length === 0) {
      setError("Chưa chọn món nào.");
      return;
    }
    setSubmitting(true);
    try {
      const order = await apiFetch<CreatedOrder>("/sales/orders", {
        method: "POST",
        body: {
          MaBan: orderType === "Tại chỗ" ? Number(tableId) : null,
          LoaiDon: orderType,
          lines: cart.map((l) => ({
            MaMon: l.MaMon,
            SoLuong: l.SoLuong,
            GhiChu: l.GhiChu || null,
          })),
        },
      });
      const skipped = order.rejected?.length ?? 0;
      setCreated({
        id: order.MaOrder,
        text:
          `Đã tạo ${order.MaOrderHienThi}` +
          (skipped > 0 ? `, bỏ qua ${skipped} món thiếu tồn kho` : ""),
      });
      setCart([]);
      onOrderCreated?.(order.MaOrder);
    } catch (e: unknown) {
      setError(
        messageOf(e, "Không gửi được order. Kiểm tra kết nối rồi thử lại."),
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,1fr)_360px]">
      <div className="min-w-0 space-y-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <fieldset className="space-y-2">
            <legend className="mb-2 font-medium">Loại đơn</legend>
            <div className="flex gap-2">
              {ORDER_TYPES.map((type) => (
                <Chip
                  key={type}
                  name="order-type"
                  value={type}
                  checked={orderType === type}
                  onChange={setOrderType}
                >
                  {type}
                </Chip>
              ))}
            </div>
          </fieldset>
        </div>

        {orderType === "Tại chỗ" && (
          <fieldset className="space-y-2">
            <legend className="mb-2 font-medium">Bàn</legend>
            {tables.length === 0 ? (
              <p className="text-muted">
                Chưa có bàn nào. Quản lý thêm bàn trong mục Danh mục.
              </p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {tables.map((t) => (
                  <Chip
                    key={t.MaBan}
                    name="table"
                    value={String(t.MaBan)}
                    checked={tableId === String(t.MaBan)}
                    onChange={setTableId}
                  >
                    {t.TenBan}
                  </Chip>
                ))}
              </div>
            )}
          </fieldset>
        )}

        <div className="flex flex-wrap items-center justify-between gap-3">
          <div
            role="tablist"
            aria-label="Nhóm món"
            className="flex max-w-full gap-1 overflow-x-auto border-b border-border"
          >
            {[{ MaNhomMon: null, TenNhom: "Tất cả" }, ...usedGroups].map(
              (g) => (
                <button
                  key={g.MaNhomMon ?? "all"}
                  type="button"
                  role="tab"
                  aria-selected={groupId === g.MaNhomMon}
                  onClick={() => setGroupId(g.MaNhomMon)}
                  className={cn(
                    "-mb-px border-b-2 px-3 pt-2 pb-2.5 font-medium whitespace-nowrap transition-colors",
                    groupId === g.MaNhomMon
                      ? "border-primary text-primary-subtle-fg"
                      : "border-transparent text-muted hover:text-ink",
                  )}
                >
                  {g.TenNhom}
                </button>
              ),
            )}
          </div>
          <div className="relative w-full sm:max-w-60">
            <Search
              className="absolute top-2.5 left-2.5 size-4 text-subtle"
              aria-hidden
            />
            <Input
              type="search"
              aria-label="Tìm món"
              placeholder="Tìm món"
              className="pl-8"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
        </div>

        {dishes.length === 0 ? (
          <EmptyState
            icon={UtensilsCrossed}
            title="Không có món nào bán được"
            description="Các món đều đang hết nguyên liệu hoặc chưa được bật bán."
          />
        ) : visible.length === 0 ? (
          <p className="py-6 text-center text-muted">
            Không có món nào khớp “{query}”.
          </p>
        ) : (
          <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 xl:grid-cols-4">
            {visible.map((d) => {
              const inCart = cart.find((l) => l.MaMon === d.MaMon);
              return (
                <button
                  key={d.MaMon}
                  type="button"
                  onClick={() => addDish(d)}
                  className={cn(
                    "relative flex min-h-24 flex-col justify-between gap-2 rounded-container border bg-surface p-3 text-left transition-[border-color,transform] active:scale-[0.98]",
                    inCart
                      ? "border-primary ring-1 ring-primary"
                      : "border-border hover:border-border-strong",
                  )}
                >
                  <span className="line-clamp-2 pr-7 text-[15px] leading-5 font-medium">
                    {d.TenMon}
                  </span>
                  {typeof d.GiaHienTai === "number" && (
                    <span className="text-muted tabular-nums">
                      {formatVnd(d.GiaHienTai)}
                    </span>
                  )}
                  {inCart && (
                    <span
                      aria-hidden
                      className="absolute top-2.5 right-2.5 grid h-6 min-w-6 place-items-center rounded-full bg-primary px-1.5 text-xs font-semibold text-white tabular-nums"
                    >
                      {inCart.SoLuong}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        )}
      </div>

      <aside
        aria-label="Order đang soạn"
        className="flex flex-col rounded-container border border-border bg-surface lg:sticky lg:top-4 lg:max-h-[calc(100vh-2rem)]"
      >
        <div className="flex items-center justify-between gap-2 border-b border-border p-4">
          <h2 className="text-base font-semibold">
            {orderType === "Mang về"
              ? "Mang về"
              : (tableName ?? "Chưa chọn bàn")}
          </h2>
          <Badge tone="primary">Order mới</Badge>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto">
          {cart.length === 0 ? (
            <div className="grid justify-items-center gap-2 px-6 py-10 text-center text-subtle">
              <ShoppingBasket
                className="size-7 text-border-strong"
                aria-hidden
              />
              Chưa có món nào. Chạm vào món bên trái để thêm.
            </div>
          ) : (
            <ul className="divide-y divide-border">
              {cart.map((l) => (
                <li key={l.MaMon} className="space-y-2 px-4 py-3">
                  <div className="flex justify-between gap-3">
                    <div className="min-w-0">
                      <p className="font-medium">{l.TenMon}</p>
                      <p className="text-xs text-muted tabular-nums">
                        {formatVnd(l.DonGia)}
                      </p>
                    </div>
                    <p className="font-medium tabular-nums">
                      {formatVnd(l.DonGia * l.SoLuong)}
                    </p>
                  </div>
                  <label className="flex items-center gap-1.5 text-subtle">
                    <PencilLine className="size-3.5 shrink-0" aria-hidden />
                    <input
                      aria-label={`Ghi chú ${l.TenMon}`}
                      placeholder="Thêm ghi chú cho bếp"
                      className="min-w-0 flex-1 bg-transparent py-1 text-ink outline-none placeholder:text-subtle"
                      value={l.GhiChu}
                      onChange={(e) =>
                        updateLine(l.MaMon, { GhiChu: e.target.value })
                      }
                    />
                  </label>
                  <div className="inline-flex items-center overflow-hidden rounded-control border border-border">
                    <button
                      type="button"
                      aria-label={
                        l.SoLuong === 1
                          ? `Bỏ ${l.TenMon}`
                          : `Bớt một ${l.TenMon}`
                      }
                      onClick={() => step(l, -1)}
                      className="grid size-11 place-items-center text-muted hover:bg-surface-sunken hover:text-ink"
                    >
                      {l.SoLuong === 1 ? (
                        <Trash2 className="size-4" aria-hidden />
                      ) : (
                        <Minus className="size-4" aria-hidden />
                      )}
                    </button>
                    <input
                      aria-label={`Số lượng ${l.TenMon}`}
                      type="number"
                      inputMode="numeric"
                      min={1}
                      className="h-11 w-12 border-x border-border text-center font-semibold tabular-nums outline-none [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none"
                      value={l.SoLuong}
                      onChange={(e) =>
                        updateLine(l.MaMon, {
                          SoLuong: Math.max(1, Number(e.target.value) || 1),
                        })
                      }
                    />
                    <button
                      type="button"
                      aria-label={`Thêm một ${l.TenMon}`}
                      onClick={() => step(l, 1)}
                      className="grid size-11 place-items-center text-muted hover:bg-surface-sunken hover:text-ink"
                    >
                      <Plus className="size-4" aria-hidden />
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="space-y-3 border-t border-border p-4">
          <div className="flex justify-between text-muted">
            <span>Số món</span>
            <span className="tabular-nums">{itemCount}</span>
          </div>
          <div className="flex items-baseline justify-between">
            <span>Tổng cộng</span>
            <span className="text-2xl font-semibold tabular-nums">
              {formatVnd(total)}
            </span>
          </div>
          {error && (
            <p role="alert" className="flex items-start gap-1.5 text-danger-fg">
              <CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
              {error}
            </p>
          )}
          {created && (
            <div
              role="status"
              className="flex flex-wrap items-center gap-2 rounded-control bg-success-subtle px-3 py-2 text-success-fg"
            >
              <CircleCheck className="size-4 shrink-0" aria-hidden />
              <p className="flex-1">{created.text}</p>
              {onPayNow && (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => onPayNow(created.id)}
                >
                  Thanh toán
                </Button>
              )}
            </div>
          )}
          <Button
            size="pos"
            className="w-full"
            onClick={submit}
            disabled={submitting}
          >
            {submitting ? "Đang gửi…" : "Gửi order"}
          </Button>
        </div>
      </aside>
    </div>
  );
}
