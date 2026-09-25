"use client";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";
import { loadSession } from "@/lib/session";

type Dish = { MaMon: number; TenMon: string; TrangThai?: string; status?: string };

export function OrderScreen() {
  const [dishes, setDishes] = useState<Dish[]>([]);
  const [loading, setLoading] = useState(true);
  const session = loadSession();
  const isManager = session?.role === "MANAGER";

  useEffect(() => {
    apiFetch<{ items: Dish[] }>("/catalog/dishes").then((d) => {
      const filtered = (d.items || []).filter((x) => (x.TrangThai || x.status) !== "Hết nguyên liệu");
      setDishes(filtered);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) return <p>Đang tải…</p>;

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Gọi món</h2>
      <ul>
        {dishes.map((d) => <li key={d.MaMon}>{d.TenMon}</li>)}
      </ul>
      <div className="flex gap-2">
        <input aria-label="Số lượng" type="number" inputMode="numeric" className="min-h-11 rounded border px-3 py-2" />
        {isManager && <button>Hủy toàn bộ order</button>}
      </div>
    </div>
  );
}
