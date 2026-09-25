"use client";

import { useState } from "react";

import { ApiError, apiFetch } from "@/lib/api-client";

type OrderRow = {
  MaOrder: number;
  MaOrderHienThi: string | null;
  MaBan: number | null;
  BusinessDate: string;
  TrangThai: string;
};

export function OrderLookup({
  onSelect,
}: {
  onSelect?: (orderId: number) => void;
} = {}) {
  const [code, setCode] = useState("");
  const [rows, setRows] = useState<OrderRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function search() {
    setError(null);
    try {
      const data = await apiFetch<{ items: OrderRow[]; total: number }>(
        `/sales/orders?code=${encodeURIComponent(code)}`,
      );
      setRows(data.items);
    } catch (e: unknown) {
      setError(e instanceof ApiError ? e.message : "Không tra cứu được.");
      setRows([]);
    }
  }

  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold">Tra cứu order</h2>
      <div className="flex flex-wrap items-end gap-2">
        <label className="text-sm">
          Mã order
          <input
            aria-label="Mã order"
            className="mt-1 block min-h-11 rounded border px-3 py-2"
            value={code}
            onChange={(e) => setCode(e.target.value)}
          />
        </label>
        <button
          type="button"
          onClick={search}
          className="min-h-11 rounded border px-4 py-2 text-sm"
        >
          Tìm
        </button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {rows.length > 0 && (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left">
              <th>Mã</th>
              <th>Bàn</th>
              <th>Business date</th>
              <th>Trạng thái</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {rows.map((o) => (
              <tr key={o.MaOrder}>
                <td>{o.MaOrderHienThi}</td>
                <td>{o.MaBan ?? "Mang về"}</td>
                <td>{o.BusinessDate}</td>
                <td>{o.TrangThai}</td>
                <td>
                  <button
                    type="button"
                    onClick={() => onSelect?.(o.MaOrder)}
                    aria-label={`Chọn ${o.MaOrderHienThi}`}
                  >
                    Chọn
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
