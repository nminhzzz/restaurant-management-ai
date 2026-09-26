"use client";

import {
  ArrowLeft,
  ChefHat,
  CircleAlert,
  Minus,
  PencilLine,
  Plus,
  Search,
  ShoppingBasket,
  Trash2,
  UtensilsCrossed,
} from "lucide-react";
import { useCallback, useState } from "react";
import { toast } from "sonner";

import {
  EmptyState,
  ErrorState,
  LoadingState,
  StatusBadge,
} from "@/components/page-states";
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

const UNSELLABLE = new Set(["Hết nguyên liệu", "Ẩn", "Nháp"]);

function messageOf(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback;
}

type SentLine = {
  MaChiTietOrder: number;
  MaMon: number;
  SoLuong: number;
  DonGia: number;
  TrangThai: string;
};
type OpenOrder = {
  MaOrder: number;
  MaOrderHienThi: string | null;
  TrangThai: string;
  ThoiDiemTao?: string | null;
  lines?: SentLine[];
};

function openedAt(iso?: string | null): string {
  if (!iso) return "";
  return new Date(iso).toLocaleTimeString("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

async function loadMenu(orderId: number | null) {
  const [tables, dishPage, groups, order] = await Promise.all([
    apiFetch<{ MaBan: number; TenBan: string }[]>("/catalog/tables"),
    apiFetch<{ items: Dish[] }>("/catalog/dishes?size=200"),
    apiFetch<Group[]>("/catalog/groups").catch(() => []),
    orderId === null
      ? Promise.resolve(null)
      : apiFetch<OpenOrder>(`/sales/orders/${orderId}`),
  ]);
  const all = dishPage.items || [];
  return {
    tables: Array.isArray(tables) ? tables : [],
    names: new Map(all.map((d) => [d.MaMon, d.TenMon])),
    dishes: all.filter((d) => !UNSELLABLE.has(d.TrangThai ?? "")),
    groups: Array.isArray(groups) ? groups : [],
    order,
  };
}

export function OrderStep({
  tableId,
  orderId,
  onBack,
  onSent,
}: {
  tableId: number | null;
  orderId: number | null;
  onBack: () => void;
  onSent: (orderId: number, next: "floor" | "pay") => void;
}) {
  const fetcher = useCallback(() => loadMenu(orderId), [orderId]);
  const menu = useResource(fetcher);
  const [groupId, setGroupId] = useState<number | null>(null);
  const [query, setQuery] = useState("");
  const [cart, setCart] = useState<CartLine[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  // Lines confirmed by the server during this visit but not yet reflected in
  // `menu.data.order` (no reload happens on a partial failure, so the total
  // would otherwise undercount them until the next full reload).
  const [extraSent, setExtraSent] = useState<
    { MaMon: number; SoLuong: number; DonGia: number }[]
  >([]);

  if (menu.status === "loading") return <LoadingState rows={6} />;
  if (menu.status === "error")
    return <ErrorState message={menu.message} onRetry={menu.reload} />;

  const { tables, dishes, groups, names, order } = menu.data;
  const tableName =
    tableId === null
      ? "Mang về"
      : (tables.find((t) => t.MaBan === tableId)?.TenBan ?? `Bàn #${tableId}`);
  const sent = (order?.lines ?? []).filter((l) => l.TrangThai !== "Đã hủy");
  // `extraSent` covers lines the server already confirmed but that a partial
  // failure kept out of `order.lines` (no reload happens on error).
  const sentDisplay = [
    ...sent.map((l) => ({
      key: `line-${l.MaChiTietOrder}`,
      MaMon: l.MaMon,
      SoLuong: l.SoLuong,
      DonGia: l.DonGia,
      TrangThai: l.TrangThai,
    })),
    ...extraSent.map((l, i) => ({
      key: `extra-${i}-${l.MaMon}`,
      MaMon: l.MaMon,
      SoLuong: l.SoLuong,
      DonGia: l.DonGia,
      TrangThai: "Chờ",
    })),
  ];
  const sentTotal = sentDisplay.reduce(
    (sum, l) => sum + l.DonGia * l.SoLuong,
    0,
  );
  const newTotal = cart.reduce((sum, l) => sum + l.DonGia * l.SoLuong, 0);
  const usedGroups = groups.filter((g) =>
    dishes.some((d) => d.MaNhomMon === g.MaNhomMon),
  );
  const needle = query.trim().toLowerCase();
  const visible = dishes.filter(
    (d) =>
      (groupId === null || d.MaNhomMon === groupId) &&
      (!needle || d.TenMon.toLowerCase().includes(needle)),
  );

  function addDish(dish: Dish) {
    if (dish.GiaHienTai == null) return;
    const price = dish.GiaHienTai;
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
          DonGia: price,
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

  async function send(next: "floor" | "pay") {
    setError(null);
    if (cart.length === 0) {
      if (orderId !== null && next === "pay") onSent(orderId, "pay");
      else setError("Chưa chọn món nào.");
      return;
    }
    setSubmitting(true);
    try {
      let id = orderId;
      if (id === null) {
        const created = await apiFetch<CreatedOrder>("/sales/orders", {
          method: "POST",
          body: {
            MaBan: tableId,
            LoaiDon: tableId === null ? "Mang về" : "Tại chỗ",
            lines: cart.map((l) => ({
              MaMon: l.MaMon,
              SoLuong: l.SoLuong,
              GhiChu: l.GhiChu || null,
            })),
          },
        });
        id = created.MaOrder;
        const skipped = created.rejected?.length ?? 0;
        if (skipped > 0) toast.warning(`Bỏ qua ${skipped} món thiếu tồn kho.`);
        setCart([]);
      } else {
        // One line per request: a failure keeps the unsent lines in the cart,
        // and the already-confirmed ones move into `extraSent` so the total
        // stays right until the next reload.
        for (const line of [...cart]) {
          await apiFetch(`/sales/orders/${id}/lines`, {
            method: "POST",
            body: {
              MaMon: line.MaMon,
              SoLuong: line.SoLuong,
              GhiChu: line.GhiChu || null,
            },
          });
          setExtraSent((prev) => [
            ...prev,
            { MaMon: line.MaMon, SoLuong: line.SoLuong, DonGia: line.DonGia },
          ]);
          setCart((prev) => prev.filter((l) => l.MaMon !== line.MaMon));
        }
      }
      toast.success(`Đã gửi món của ${tableName} xuống bếp.`);
      onSent(id, next);
    } catch (e: unknown) {
      setError(
        messageOf(e, "Không gửi được món. Kiểm tra kết nối rồi thử lại."),
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,1fr)_360px]">
      <div className="min-w-0 space-y-5">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 rounded-container border border-border bg-surface px-3 py-2">
          <Button variant="ghost" size="sm" onClick={onBack}>
            <ArrowLeft />
            Sơ đồ bàn
          </Button>
          <span className="text-base font-bold">{tableName}</span>
          {order && (
            <span className="font-mono text-xs text-subtle">
              {order.MaOrderHienThi}
              {order.ThoiDiemTao && ` · mở ${openedAt(order.ThoiDiemTao)}`}
            </span>
          )}
        </div>

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
                  disabled={d.GiaHienTai == null}
                  className={cn(
                    "relative flex min-h-24 flex-col justify-between gap-2 rounded-container border bg-surface p-3 text-left transition-[border-color,box-shadow,transform] active:translate-y-px disabled:cursor-not-allowed disabled:bg-surface-sunken disabled:hover:border-border disabled:hover:shadow-none",
                    inCart
                      ? "border-primary ring-1 ring-primary"
                      : "border-border hover:border-ink hover:shadow-lift",
                  )}
                >
                  <span className="line-clamp-2 pr-7 text-[15px] leading-5 font-semibold">
                    {d.TenMon}
                  </span>
                  {d.GiaHienTai != null ? (
                    <span className="font-bold tabular-nums">
                      {formatVnd(d.GiaHienTai)}
                    </span>
                  ) : (
                    <span className="text-subtle">Chưa có giá</span>
                  )}
                  {inCart && (
                    <span
                      aria-hidden
                      className="absolute top-2.5 right-2.5 grid h-6 min-w-6 place-items-center rounded-badge bg-primary px-1.5 text-xs font-bold text-white tabular-nums"
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
          <h2 className="text-base font-bold">
            {order ? `Order ${tableName}` : tableName}
          </h2>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto">
          {cart.length === 0 && sentDisplay.length === 0 ? (
            <div className="grid justify-items-center gap-2 px-6 py-10 text-center text-subtle">
              <ShoppingBasket
                className="size-7 text-border-strong"
                aria-hidden
              />
              Chưa có món nào. Chạm vào món bên trái để thêm.
            </div>
          ) : (
            <>
              {cart.length > 0 && (
                <p className="px-4 pt-3 pb-1 text-[11px] font-bold tracking-wider text-subtle uppercase">
                  Món mới
                </p>
              )}
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
              {sentDisplay.length > 0 && (
                <div className="border-t border-border">
                  <p className="px-4 pt-3 pb-1 text-[11px] font-bold tracking-wider text-subtle uppercase">
                    Đã gửi bếp
                  </p>
                  <ul className="divide-y divide-border bg-surface-sunken">
                    {sentDisplay.map((l) => (
                      <li
                        key={l.key}
                        className="flex items-center justify-between gap-3 px-4 py-2.5"
                      >
                        <span>
                          {l.SoLuong}× {names.get(l.MaMon) ?? `Món #${l.MaMon}`}
                        </span>
                        <span className="flex items-center gap-2">
                          <StatusBadge status={l.TrangThai} />
                          <span className="font-semibold tabular-nums">
                            {formatVnd(l.DonGia * l.SoLuong)}
                          </span>
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}
        </div>

        <div className="space-y-3 border-t border-border p-4">
          {sentDisplay.length > 0 && (
            <div className="flex justify-between text-muted">
              <span>Tổng đã gửi bếp</span>
              <span className="tabular-nums">{formatVnd(sentTotal)}</span>
            </div>
          )}
          <div className="flex items-baseline justify-between">
            <span>Tổng cộng</span>
            <span
              data-testid="cart-total"
              className="text-2xl font-bold tracking-tight tabular-nums"
            >
              {formatVnd(sentTotal + newTotal)}
            </span>
          </div>
          {error && (
            <p role="alert" className="flex items-start gap-1.5 text-danger-fg">
              <CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
              {error}
            </p>
          )}
          <div className="grid grid-cols-[1fr_1.4fr] gap-2">
            <Button
              variant="secondary"
              size="pos"
              onClick={() => send("floor")}
              disabled={submitting}
            >
              <ChefHat />
              Gửi bếp
            </Button>
            <Button
              size="pos"
              onClick={() => send("pay")}
              disabled={submitting}
            >
              Gửi bếp &amp; thanh toán
            </Button>
          </div>
        </div>
      </aside>
    </div>
  );
}
