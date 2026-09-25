"use client";

import { useEffect, useState } from "react";

import { ApiError, apiFetch } from "@/lib/api-client";

type Dish = {
  MaMon: number;
  TenMon: string;
  TrangThai?: string;
  GiaHienTai?: number | null;
};

type DiningTable = { MaBan: number; TenBan: string };

type CartLine = {
  MaMon: number;
  TenMon: string;
  SoLuong: number;
  GhiChu: string;
};

type CreatedOrder = {
  MaOrder: number;
  MaOrderHienThi: string;
  rejected?: { MaMon: number; reason: string }[];
};

function messageOf(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback;
}

export function OrderScreen({
  onOrderCreated,
}: {
  onOrderCreated?: (orderId: number) => void;
} = {}) {
  const [tables, setTables] = useState<DiningTable[]>([]);
  const [dishes, setDishes] = useState<Dish[]>([]);
  const [loading, setLoading] = useState(true);
  const [tableId, setTableId] = useState("");
  const [orderType, setOrderType] = useState("Tại chỗ");
  const [cart, setCart] = useState<CartLine[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    Promise.all([
      apiFetch<DiningTable[]>("/catalog/tables"),
      apiFetch<{ items: Dish[] }>("/catalog/dishes"),
    ])
      .then(([tableRows, dishPage]) => {
        setTables(Array.isArray(tableRows) ? tableRows : []);
        setDishes(
          (dishPage.items || []).filter(
            (d) => d.TrangThai !== "Hết nguyên liệu",
          ),
        );
        setLoading(false);
      })
      .catch((e: unknown) => {
        setError(messageOf(e, "Không tải được danh mục."));
        setLoading(false);
      });
  }, []);

  function addDish(dish: Dish) {
    setCart((prev) => {
      const existing = prev.find((l) => l.MaMon === dish.MaMon);
      if (existing) {
        return prev.map((l) =>
          l.MaMon === dish.MaMon ? { ...l, SoLuong: l.SoLuong + 1 } : l,
        );
      }
      return [
        ...prev,
        { MaMon: dish.MaMon, TenMon: dish.TenMon, SoLuong: 1, GhiChu: "" },
      ];
    });
  }

  function updateLine(dishId: number, patch: Partial<CartLine>) {
    setCart((prev) =>
      prev.map((l) => (l.MaMon === dishId ? { ...l, ...patch } : l)),
    );
  }

  function removeLine(dishId: number) {
    setCart((prev) => prev.filter((l) => l.MaMon !== dishId));
  }

  async function submit() {
    setError(null);
    setNotice(null);
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
      const created = await apiFetch<CreatedOrder>("/sales/orders", {
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
      const skipped = created.rejected?.length ?? 0;
      setNotice(
        `Đã tạo ${created.MaOrderHienThi}` +
          (skipped > 0 ? ` — bỏ qua ${skipped} món thiếu tồn kho` : ""),
      );
      setCart([]);
      onOrderCreated?.(created.MaOrder);
    } catch (e: unknown) {
      setError(messageOf(e, "Không gửi được order."));
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <p>Đang tải…</p>;

  return (
    <section className="space-y-4">
      <h2 className="text-lg font-semibold">Gọi món</h2>

      <div className="flex flex-wrap items-end gap-3">
        <label className="text-sm">
          Loại đơn
          <select
            aria-label="Loại đơn"
            className="mt-1 block min-h-11 rounded border px-3 py-2"
            value={orderType}
            onChange={(e) => setOrderType(e.target.value)}
          >
            <option value="Tại chỗ">Tại chỗ</option>
            <option value="Mang về">Mang về</option>
          </select>
        </label>
        {orderType === "Tại chỗ" && (
          <label className="text-sm">
            Bàn
            <select
              aria-label="Bàn"
              className="mt-1 block min-h-11 rounded border px-3 py-2"
              value={tableId}
              onChange={(e) => setTableId(e.target.value)}
            >
              <option value="">— chọn bàn —</option>
              {tables.map((t) => (
                <option key={t.MaBan} value={String(t.MaBan)}>
                  {t.TenBan}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        {dishes.map((d) => (
          <button
            key={d.MaMon}
            type="button"
            onClick={() => addDish(d)}
            className="min-h-11 rounded border px-3 py-2 text-sm hover:bg-slate-100"
          >
            {d.TenMon}
            {typeof d.GiaHienTai === "number"
              ? ` · ${d.GiaHienTai.toLocaleString("vi-VN")}đ`
              : ""}
          </button>
        ))}
        {dishes.length === 0 && (
          <p className="text-sm">Không có món nào bán được.</p>
        )}
      </div>

      {cart.length > 0 && (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left">
              <th>Món</th>
              <th>Số lượng</th>
              <th>Ghi chú</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {cart.map((l) => (
              <tr key={l.MaMon}>
                <td>{l.TenMon}</td>
                <td>
                  <input
                    aria-label={`Số lượng ${l.TenMon}`}
                    type="number"
                    inputMode="numeric"
                    min={1}
                    className="min-h-11 w-20 rounded border px-2 py-1"
                    value={l.SoLuong}
                    onChange={(e) =>
                      updateLine(l.MaMon, {
                        SoLuong: Math.max(1, Number(e.target.value)),
                      })
                    }
                  />
                </td>
                <td>
                  <input
                    aria-label={`Ghi chú ${l.TenMon}`}
                    className="min-h-11 rounded border px-2 py-1"
                    value={l.GhiChu}
                    onChange={(e) =>
                      updateLine(l.MaMon, { GhiChu: e.target.value })
                    }
                  />
                </td>
                <td>
                  <button type="button" onClick={() => removeLine(l.MaMon)}>
                    Bỏ
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <button
        type="button"
        onClick={submit}
        disabled={submitting}
        className="min-h-11 rounded bg-amber-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        Gửi order
      </button>

      {error && <p className="text-sm text-red-600">{error}</p>}
      {notice && <p className="text-sm text-emerald-600">{notice}</p>}
    </section>
  );
}
