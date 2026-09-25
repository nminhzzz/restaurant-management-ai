"use client";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";

type Qr = { MaGiaoDich: number; TrangThai: string; ThoiDiemTaoQR?: string; ThoiDiemHetHan?: string };

export function PaymentPanel({ orderId }: { orderId: number }) {
  const [qr, setQr] = useState<Qr | null>(null);
  const [remaining, setRemaining] = useState<string | null>(null);
  const [expired, setExpired] = useState(false);

  useEffect(() => {
    // fetch existing qr if any
    apiFetch<Qr>(`/sales/orders/${orderId}/pay/qr`).catch(() => null);
  }, [orderId]);

  async function createQr() {
    const data = await apiFetch<Qr>("/sales/orders/" + orderId + "/pay/qr", { method: "POST", body: {} });
    setQr(data);
    if (data.ThoiDiemHetHan) {
      const end = new Date(data.ThoiDiemHetHan).getTime();
      const tick = () => {
        const diff = end - Date.now();
        if (diff <= 0) { setExpired(true); setRemaining("Hết hạn"); }
        else {
          const m = Math.floor(diff / 60000);
          const s = Math.floor((diff % 60000) / 1000);
          setRemaining(`${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}`);
        }
      };
      tick();
      const id = setInterval(tick, 1000);
      return () => clearInterval(id);
    }
  }

  const live = qr?.TrangThai === "Chờ xác nhận" && !expired;

  return (
    <div className="space-y-2">
      <button onClick={createQr} disabled={!!live}>Thanh toán QR</button>
      <button disabled={!!live}>Tạo mã QR mới</button>
      {remaining && <p>{remaining}</p>}
      {expired && <p>Hết hạn</p>}
      {qr && <p>{qr.TrangThai}</p>}
    </div>
  );
}
