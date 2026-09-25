"use client";

import { useCallback, useEffect, useState } from "react";

import { ApiError, apiFetch } from "@/lib/api-client";
import { loadSession } from "@/lib/session";

type OrderLine = {
  MaChiTietOrder: number;
  MaMon: number;
  SoLuong: number;
  DonGia: number;
  TrangThai: string;
};

type Order = {
  MaOrder: number;
  MaOrderHienThi: string;
  TrangThai: string;
  lines?: OrderLine[];
};

type Qr = {
  MaGiaoDich: number;
  TrangThai: string;
  ThoiDiemTaoQR?: string;
  ThoiDiemHetHan?: string;
};

type InvoiceResult = {
  invoice: { SoHoaDon: string; TongTien: number };
  MaHoaDon: number;
};

function messageOf(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback;
}

function formatVnd(amount: number): string {
  return `${amount.toLocaleString("vi-VN")}đ`;
}

export function PaymentPanel({ orderId }: { orderId: number }) {
  const [order, setOrder] = useState<Order | null>(null);
  const [qr, setQr] = useState<Qr | null>(null);
  const [remaining, setRemaining] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reason, setReason] = useState("");
  const isManager = loadSession()?.role === "MANAGER";

  const refreshOrder = useCallback(() => {
    apiFetch<Order>(`/sales/orders/${orderId}`)
      .then(setOrder)
      .catch(() => setOrder(null));
  }, [orderId]);

  useEffect(() => {
    refreshOrder();
  }, [refreshOrder]);

  useEffect(() => {
    if (!qr?.ThoiDiemHetHan) return;
    const end = new Date(qr.ThoiDiemHetHan).getTime();
    const tick = () => {
      const diff = end - Date.now();
      if (diff <= 0) {
        setRemaining("Hết hạn");
        return;
      }
      const m = Math.floor(diff / 60000);
      const s = Math.floor((diff % 60000) / 1000);
      setRemaining(
        `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`,
      );
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [qr]);

  const lines = order?.lines ?? [];
  const total = lines.reduce((sum, l) => sum + l.DonGia * l.SoLuong, 0);
  const expired = remaining === "Hết hạn";
  const live = qr?.TrangThai === "Chờ xác nhận" && !expired;
  const locked = order !== null && order.TrangThai !== "Đang mở";

  async function run(action: () => Promise<void>, fallback: string) {
    setError(null);
    setMessage(null);
    try {
      await action();
    } catch (e: unknown) {
      setError(messageOf(e, fallback));
    }
  }

  const payCash = () =>
    run(async () => {
      const result = await apiFetch<InvoiceResult>(
        `/sales/orders/${orderId}/pay/cash`,
        { method: "POST", body: {} },
      );
      setMessage(
        `Đã thu tiền mặt — hóa đơn ${result.invoice.SoHoaDon}, ${formatVnd(result.invoice.TongTien)}`,
      );
      refreshOrder();
    }, "Thanh toán tiền mặt thất bại.");

  const createQr = () =>
    run(async () => {
      setQr(
        await apiFetch<Qr>(`/sales/orders/${orderId}/pay/qr`, {
          method: "POST",
          body: {},
        }),
      );
    }, "Không tạo được mã QR.");

  const cancelQr = () => {
    if (!qr) return;
    return run(async () => {
      await apiFetch(`/sales/payments/${qr.MaGiaoDich}/cancel`, {
        method: "POST",
        body: {},
      });
      setQr({ ...qr, TrangThai: "Đã hủy" });
      setRemaining(null);
      setMessage("Đã hủy giao dịch QR.");
    }, "Hủy QR thất bại.");
  };

  const cancelOrder = () =>
    run(async () => {
      await apiFetch(`/sales/orders/${orderId}/cancel`, {
        method: "POST",
        body: { reason },
      });
      setReason("");
      setMessage("Đã hủy order.");
      refreshOrder();
    }, "Hủy order thất bại.");

  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold">Thanh toán</h2>

      {order === null ? (
        <p className="text-sm text-slate-500">Không tải được order.</p>
      ) : (
        <>
          <p>
            Order <strong>{order.MaOrderHienThi}</strong>
          </p>
          <p>
            Trạng thái: {order.TrangThai} · Tổng tiền: {formatVnd(total)}
          </p>
          {lines.length > 0 && (
            <ul className="list-inside list-disc text-sm">
              {lines.map((l) => (
                <li key={l.MaChiTietOrder}>
                  Món {l.MaMon} × {l.SoLuong} —{" "}
                  {formatVnd(l.DonGia * l.SoLuong)} ({l.TrangThai})
                </li>
              ))}
            </ul>
          )}
        </>
      )}

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={payCash}
          disabled={locked}
          className="min-h-11 rounded bg-emerald-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          Thanh toán tiền mặt
        </button>
        <button
          type="button"
          onClick={createQr}
          disabled={!!live || locked}
          className="min-h-11 rounded border px-4 py-2 text-sm disabled:opacity-50"
        >
          Thanh toán QR
        </button>
        <button
          type="button"
          onClick={cancelQr}
          disabled={!live}
          className="min-h-11 rounded border px-4 py-2 text-sm disabled:opacity-50"
        >
          Hủy QR
        </button>
        <button
          type="button"
          onClick={createQr}
          disabled={!!live || locked}
          className="min-h-11 rounded border px-4 py-2 text-sm disabled:opacity-50"
        >
          Tạo mã QR mới
        </button>
      </div>

      {remaining && <p>{remaining}</p>}
      {qr && <p>{qr.TrangThai}</p>}

      {isManager && !locked && (
        <div className="flex flex-wrap items-end gap-2">
          <label className="text-sm">
            Lý do hủy order
            <input
              aria-label="Lý do hủy order"
              className="mt-1 block min-h-11 rounded border px-3 py-2"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
          </label>
          <button
            type="button"
            onClick={cancelOrder}
            disabled={reason.trim() === ""}
            className="min-h-11 rounded border border-red-300 px-4 py-2 text-sm text-red-700 disabled:opacity-50"
          >
            Hủy toàn bộ order
          </button>
        </div>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}
      {message && <p className="text-sm text-emerald-600">{message}</p>}
    </section>
  );
}
