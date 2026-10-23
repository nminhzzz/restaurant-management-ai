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
import { useCallback, useEffect, useRef, useState } from "react";
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
  SoSuatKhaDung?: number | null;
};

type Group = { MaNhomMon: number; TenNhom: string };

type CartLine = {
  MaMon: number;
  TenMon: string;
  DonGia: number;
  SoLuong: number;
  GhiChu: string;
  holdId: number;
  RequestLineId: string;
  expired?: boolean;
};

type Hold = {
  MaGiuCho: number;
  MaLuotChon: string;
  MaMon: number;
  TenMon?: string | null;
  SoLuong: number;
  GhiChu?: string | null;
  DonGia?: number | null;
  ThoiDiemHetHan: string;
  TrangThai: string;
};

const SELECTION_PREFIX = "sales-selection:";

function requestId(): string {
  return (
    globalThis.crypto?.randomUUID?.() ??
    `req-${Date.now()}-${Math.random().toString(36).slice(2)}`
  );
}

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
    dishes: all.filter(
      (d) =>
        !UNSELLABLE.has(d.TrangThai ?? "") &&
        (d.SoSuatKhaDung == null || d.SoSuatKhaDung > 0),
    ),
    groups: Array.isArray(groups) ? groups : [],
    order,
  };
}

function selectionStorageKey(
  tableId: number | null,
  orderId: number | null,
): string {
  if (orderId !== null) return `${SELECTION_PREFIX}order-${orderId}`;
  if (tableId !== null) return `${SELECTION_PREFIX}table-${tableId}`;
  return `${SELECTION_PREFIX}takeaway`;
}

function storedSelection(key: string): string | null {
  if (typeof window === "undefined") return null;
  return window.sessionStorage.getItem(key);
}

function rememberSelection(key: string, code: string): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(key, code);
}

function newSelectionCode(): string {
  return (
    globalThis.crypto?.randomUUID?.() ??
    `sel-${Date.now()}-${Math.random().toString(36).slice(2)}`
  );
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
  const selectionKey = selectionStorageKey(tableId, orderId);
  const fetcher = useCallback(() => loadMenu(orderId), [orderId]);
  const menu = useResource(fetcher);
  const [groupId, setGroupId] = useState<number | null>(null);
  const [query, setQuery] = useState("");
  const [cart, setCart] = useState<CartLine[]>([]);
  const [selectionCode, setSelectionCode] = useState(() => {
    const existing = storedSelection(selectionKey);
    if (existing) return existing;
    const code = newSelectionCode();
    rememberSelection(selectionKey, code);
    return code;
  });
  const [error, setError] = useState<string | null>(null);
  const [adding, setAdding] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  // Reused across retries so a lost response cannot create a second order.
  const submitRequestId = useRef<string | null>(null);
  const hydratedFor = useRef<string | null>(null);

  const loadHolds = useCallback(async () => {
    const params = new URLSearchParams({
      selection_code: selectionCode,
      include_expired: "true",
    });
    if (orderId !== null) params.set("order_id", String(orderId));
    const payload = await apiFetch<Hold[] | Hold>(
      `/sales/holds?${params.toString()}`,
    );
    return { selectionCode, holds: Array.isArray(payload) ? payload : [] };
  }, [selectionCode, orderId]);
  const restored = useResource(loadHolds);

  // The selection belongs to a table/order key. Move to another key => fresh draft.
  useEffect(() => {
    const existing = storedSelection(selectionKey);
    const code = existing ?? newSelectionCode();
    if (!existing) rememberSelection(selectionKey, code);
    setSelectionCode(code);
    setCart([]);
    submitRequestId.current = null;
    hydratedFor.current = null;
  }, [selectionKey]);

  // Reload/back must bring the server-side cart back, not start a second selection.
  useEffect(() => {
    if (restored.status !== "ready") return;
    if (restored.data.selectionCode !== selectionCode) return;
    if (hydratedFor.current === selectionCode) return;
    hydratedFor.current = selectionCode;
    if (restored.data.holds.length === 0) return;
    setCart((previous) =>
      previous.length > 0
        ? previous
        : restored.data.holds.map((hold) => ({
            MaMon: hold.MaMon,
            TenMon: hold.TenMon ?? `Món #${hold.MaMon}`,
            DonGia: hold.DonGia ?? 0,
            SoLuong: hold.SoLuong,
            GhiChu: hold.GhiChu ?? "",
            holdId: hold.MaGiuCho,
            RequestLineId: requestId(),
            expired: hold.TrangThai === "Hết hạn",
          })),
    );
  }, [restored, selectionCode]);

  if (menu.status === "loading") return <LoadingState rows={6} />;
  if (menu.status === "error")
    return <ErrorState message={menu.message} onRetry={menu.reload} />;

  const { tables, dishes, groups, names, order } = menu.data;
  const tableName =
    tableId === null
      ? "Mang về"
      : (tables.find((t) => t.MaBan === tableId)?.TenBan ?? `Bàn #${tableId}`);
  const sent = (order?.lines ?? []).filter((l) => l.TrangThai !== "Đã hủy");
  const sentDisplay = sent.map((l) => ({
    key: `line-${l.MaChiTietOrder}`,
    MaMon: l.MaMon,
    SoLuong: l.SoLuong,
    DonGia: l.DonGia,
    TrangThai: l.TrangThai,
  }));
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

  async function addDish(dish: Dish) {
    if (dish.GiaHienTai == null || adding === dish.MaMon) return;
    setError(null);
    setAdding(dish.MaMon);
    try {
      const existing = cart.find((l) => l.MaMon === dish.MaMon);
      if (existing) {
        await resize(existing, existing.SoLuong + 1);
        return;
      }
      const hold = await apiFetch<{
        MaGiuCho: number;
        SoLuong?: number;
        DonGia?: number | null;
      }>("/sales/holds", {
        method: "POST",
        body: {
          selection_code: selectionCode,
          table_id: tableId,
          order_id: orderId,
          dish_id: dish.MaMon,
          quantity: 1,
        },
      });
      setCart((prev) => {
        if (prev.some((l) => l.MaMon === dish.MaMon)) return prev;
        return [
          ...prev,
          {
            MaMon: dish.MaMon,
            TenMon: dish.TenMon,
            DonGia: hold.DonGia ?? dish.GiaHienTai ?? 0,
            SoLuong: hold.SoLuong ?? 1,
            GhiChu: "",
            holdId: hold.MaGiuCho,
            RequestLineId: requestId(),
          },
        ];
      });
    } catch (e: unknown) {
      setError(
        messageOf(e, "Không giữ được món. Kiểm tra tồn kho rồi thử lại."),
      );
    } finally {
      setAdding(null);
    }
  }

  function updateLine(dishId: number, patch: Partial<CartLine>) {
    setCart((prev) =>
      prev.map((l) => (l.MaMon === dishId ? { ...l, ...patch } : l)),
    );
  }

  async function resize(line: CartLine, quantity: number) {
    if (line.expired) {
      // An expired hold cannot be patched: reserve the new quantity with today's
      // price/recipe and drop the stale one, so the cashier can keep adjusting.
      const hold = await apiFetch<{
        MaGiuCho: number;
        SoLuong?: number;
        DonGia?: number | null;
      }>("/sales/holds", {
        method: "POST",
        body: {
          selection_code: selectionCode,
          table_id: tableId,
          order_id: orderId,
          dish_id: line.MaMon,
          quantity,
        },
      });
      await apiFetch(`/sales/holds/${line.holdId}`, { method: "DELETE" }).catch(
        () => undefined,
      );
      updateLine(line.MaMon, {
        holdId: hold.MaGiuCho,
        SoLuong: hold.SoLuong ?? quantity,
        DonGia: hold.DonGia ?? line.DonGia,
        expired: false,
      });
      return;
    }
    const updated = await apiFetch<{ MaGiuCho: number; SoLuong: number }>(
      `/sales/holds/${line.holdId}`,
      { method: "PATCH", body: { quantity } },
    );
    updateLine(line.MaMon, { SoLuong: updated.SoLuong });
  }

  async function step(line: CartLine, delta: number) {
    const next = line.SoLuong + delta;
    setError(null);
    try {
      if (next <= 0) {
        await apiFetch(`/sales/holds/${line.holdId}`, { method: "DELETE" });
        setCart((prev) => prev.filter((l) => l.MaMon !== line.MaMon));
      } else {
        await resize(line, next);
      }
    } catch (e: unknown) {
      setError(messageOf(e, "Không cập nhật được số lượng giữ chỗ."));
    }
  }

  async function syncQuantity(line: CartLine) {
    try {
      await resize(line, line.SoLuong);
    } catch (e: unknown) {
      setError(messageOf(e, "Không cập nhật được số lượng giữ chỗ."));
    }
  }

  async function cancelSelection() {
    if (
      !window.confirm(
        "Hủy toàn bộ món chưa gửi của lượt chọn này? Các món đã gửi bếp không bị ảnh hưởng.",
      )
    ) {
      return;
    }
    setError(null);
    setCancelling(true);
    try {
      await apiFetch("/sales/holds/release", {
        method: "POST",
        body: { selection_code: selectionCode, order_id: orderId },
      });
      setCart([]);
      submitRequestId.current = null;
      toast.success("Đã hủy lượt chọn và giải phóng nguyên liệu đang giữ.");
    } catch (e: unknown) {
      setError(messageOf(e, "Không hủy được lượt chọn. Thử lại."));
    } finally {
      setCancelling(false);
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
    submitRequestId.current ??= requestId();

    // FR-SALE-05: an expired hold is re-checked on submit; the cashier must confirm
    // using today's price/recipe instead of the backend renewing it silently.
    async function send(confirmExpired: boolean): Promise<{
      id: number;
      rejected: { MaMon: number; reason: string }[];
    }> {
      if (orderId === null) {
        const created = await apiFetch<CreatedOrder>("/sales/orders", {
          method: "POST",
          body: {
            MaBan: tableId,
            LoaiDon: tableId === null ? "Mang về" : "Tại chỗ",
            request_id: submitRequestId.current,
            XacNhanHetHan: confirmExpired,
            lines: cart.map((l) => ({
              MaMon: l.MaMon,
              SoLuong: l.SoLuong,
              GhiChu: l.GhiChu || null,
              hold_id: l.holdId,
              request_line_id: l.RequestLineId,
            })),
          },
        });
        return { id: created.MaOrder, rejected: created.rejected ?? [] };
      }
      // The backend validates every line before committing any of them.
      await apiFetch(`/sales/orders/${orderId}/lines/bulk`, {
        method: "POST",
        body: {
          XacNhanHetHan: confirmExpired,
          lines: cart.map((l) => ({
            dish_id: l.MaMon,
            quantity: l.SoLuong,
            note: l.GhiChu || null,
            hold_id: l.holdId,
            request_line_id: l.RequestLineId,
          })),
        },
      });
      return { id: orderId, rejected: [] };
    }

    try {
      let id: number;
      let rejected: { MaMon: number; reason: string }[] = [];
      try {
        const result = await send(false);
        id = result.id;
        rejected = result.rejected;
      } catch (e: unknown) {
        const message = messageOf(e, "");
        // A changed price/recipe needs the same confirmation as an expired hold.
        const needsConfirmation =
          message.includes("hết hạn") ||
          message.includes("thay đổi") ||
          message.includes("Xác nhận dùng giá");
        if (
          !needsConfirmation ||
          !window.confirm(
            `${message}\n\nDùng giá và định lượng hiện tại để gửi?`,
          )
        ) {
          throw e;
        }
        const result = await send(true);
        id = result.id;
        rejected = result.rejected;
      }
      if (rejected.length > 0) {
        toast.error(
          `Không gửi được ${rejected.length} món: ${rejected
            .map((line) => `#${line.MaMon} (${line.reason})`)
            .join(", ")}`,
        );
      }
      setCart([]);
      submitRequestId.current = null;
      if (typeof window !== "undefined") {
        window.sessionStorage.removeItem(selectionKey);
      }
      toast.success(`Đã gửi món của ${tableName} xuống bếp.`);
      // FR-SALE-32: a failed kitchen print must be visible now, not only after the
      // cashier happens to open the order again.
      const tickets = await apiFetch<{
        items?: { LoiIn?: string | null; TrangThaiIn?: string }[];
      }>(`/sales/orders/${id}/tickets`).catch(() => ({ items: [] }));
      const printProblem = (tickets.items ?? []).some(
        (ticket) => ticket.LoiIn || ticket.TrangThaiIn === "Chưa rõ kết quả",
      );
      if (printProblem) {
        toast.warning(
          "Phiếu bếp chưa in được. Mở order để kiểm tra và bấm in lại.",
        );
        onSent(id, "pay");
        return;
      }
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
            className="flex max-w-full flex-wrap gap-1 border-b border-border"
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
                  disabled={d.GiaHienTai == null || adding === d.MaMon}
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
                  {d.SoSuatKhaDung != null && (
                    <span className="text-[11px] text-subtle">
                      Còn {d.SoSuatKhaDung} suất
                    </span>
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
          {cart.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={cancelSelection}
              disabled={cancelling || submitting}
            >
              <Trash2 aria-hidden />
              Hủy lượt chọn
            </Button>
          )}
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
                        {l.expired && (
                          <p className="text-xs font-medium text-warning-fg">
                            Hết thời gian giữ — gửi lại để dùng giá hiện tại
                          </p>
                        )}
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
                        onBlur={() => void syncQuantity(l)}
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
