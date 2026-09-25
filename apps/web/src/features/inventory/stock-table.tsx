"use client";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";

type StockRow = {
  MaNguyenLieu: number;
  TenNguyenLieu: string;
  CanhBaoTonThap: boolean;
};

export function StockTable() {
  const [items, setItems] = useState<StockRow[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    apiFetch<{ items: StockRow[] }>("/inventory/stock")
      .then((d) => {
        setItems(d.items || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);
  if (loading) return <p>Đang tải…</p>;
  if (!items.length)
    return (
      <div>
        <p>Chưa có tồn kho</p>
        <button>Nhập kho</button>
      </div>
    );
  return (
    <table>
      <tbody>
        {items.map((it) => (
          <tr
            key={it.MaNguyenLieu}
            className={it.CanhBaoTonThap ? "bg-red-100" : ""}
            data-testid={it.CanhBaoTonThap ? "alert-row" : "ok-row"}
          >
            <td>{it.TenNguyenLieu}</td>
            <td>{it.CanhBaoTonThap ? "Cảnh báo" : "OK"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
