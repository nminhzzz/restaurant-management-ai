"use client";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";
export function StockTable() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    apiFetch<any>("/inventory/stock")
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
        {items.map((it: any) => (
          <tr key={it.MaNguyenLieu}>
            <td>{it.TenNguyenLieu}</td>
            <td>{it.CanhBaoTonThap ? "Cảnh báo" : "OK"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
