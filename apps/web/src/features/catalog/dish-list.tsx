"use client";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";

type Dish = { MaMon: number; TenMon: string; TrangThai: string };

export function DishList() {
  const [loading, setLoading] = useState(true);
  const [dishes, setDishes] = useState<Dish[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<{ items: Dish[] }>("/catalog/dishes")
      .then((d) => {
        setDishes(d.items);
        setLoading(false);
      })
      .catch((e: Error) => {
        setError(e.message);
        setLoading(false);
      });
  }, []);

  if (loading) return <p>Đang tải…</p>;
  if (error) return <p className="text-red-600">{error}</p>;
  if (!dishes || dishes.length === 0)
    return (
      <div>
        <p>Chưa có món nào</p>
        <button>Thêm món</button>
      </div>
    );
  return (
    <ul>
      {dishes.map((d) => (
        <li key={d.MaMon}>{d.TenMon}</li>
      ))}
    </ul>
  );
}
