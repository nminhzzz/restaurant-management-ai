"use client";

import {
  Banknote,
  CircleAlert,
  CircleCheck,
  Printer,
  QrCode,
  Receipt,
  RefreshCw,
  TimerReset,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import {
  ErrorState,
  LoadingState,
  StatusBadge,
} from "@/components/page-states";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, apiFetch } from "@/lib/api-client";
import { formatVnd } from "@/lib/format";
import { loadSession } from "@/lib/session";
import { cn } from "@/lib/utils";
import { useResource } from "@/lib/use-resource";

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

type Payment = {
  MaGiaoDich: number;
  PhuongThuc: string;
  TrangThai: string;
  ThoiDiemTaoQR?: string | null;
  ThoiDiemHetHan?: string | null;
  MaThamChieuNganHang?: string | null;
  qr_image_url?: string;
  payment_code?: string;
  bank_code?: string;
  bank_account?: string;
  account_name?: string;
};

type InvoiceDetail = {
  SoHoaDon: string;
  TenNhaHang?: string | null;
  DiaChi?: string | null;
  ThoiDiemXuat?: string | null;
  PhuongThucThanhToan?: string | null;
  TongTien: number;
  SoLanIn: number;
  lines?: { MaMon: number; TenMon: string; SoLuong: number; DonGia: number }[];
};

function messageOf(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback;
}

async function loadDetail(orderId: number) {
  const [order, dishes, payments] = await Promise.all([
    apiFetch<Order>(`/sales/orders/${orderId}`),
    apiFetch<{ items?: { MaMon: number; TenMon: string }[] }>(
      "/catalog/dishes?size=200",
    ).catch(() => ({ items: [] })),
    apiFetch<{ items: Payment[] }>(`/sales/orders/${orderId}/payments`).catch(
      () => ({ items: [] }),
    ),
  ]);
  const names = new Map((dishes.items ?? []).map((d) => [d.MaMon, d.TenMon]));
  const latestQr =
    (payments.items ?? []).find((p) => p.PhuongThuc === "QR") ?? null;
  return { order, names, latestQr };
}

const ROUNDING = [50_000, 100_000, 500_000];

/** Exact amount first, then the next round notes a customer is likely to hand over. */
export function quickAmounts(total: number): number[] {
  const values = new Set<number>([total]);
  for (const step of ROUNDING) values.add(Math.ceil(total / step) * step);
  return [...values].filter((v) => v >= total).sort((a, b) => a - b);
}

function digits(value: string): number {
  return Number(value.replace(/\D/g, "")) || 0;
}

export function PaymentPanel({
  orderId,
  onPaid,
}: {
  orderId: number;
  onPaid?: (summary: { change: number | null }) => void;
}) {
  const fetcher = useCallback(() => loadDetail(orderId), [orderId]);
  const detail = useResource(fetcher);

  const [qrOverride, setQr] = useState<Payment | null>(null);
  const [remaining, setRemaining] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reason, setReason] = useState("");
  const [bankRef, setBankRef] = useState("");
  const [invoice, setInvoice] = useState<InvoiceDetail | null>(null);
  const [method, setMethod] = useState<"cash" | "qr">("cash");
  const [given, setGiven] = useState("");
  const isManager = loadSession()?.role === "MANAGER";

  const latestQr = detail.status === "ready" ? detail.data.latestQr : null;
  const qr = qrOverride ?? latestQr;
  // An order that already has a live or reconciling QR payment opens straight
  // into the QR pane, so its transaction card is visible without a manual pick.
  const activeMethod: "cash" | "qr" =
    qr && qr.TrangThai !== "Đã hủy" ? "qr" : method;

  useEffect(() => {
    if (!qr?.ThoiDiemHetHan || qr.TrangThai !== "Chờ xác nhận") return;
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

  useEffect(() => {
    if (!qr || qr.TrangThai !== "Chờ xác nhận") return;
    const id = setInterval(async () => {
      try {
        const list = await apiFetch<{ items: Payment[] }>(
          `/sales/orders/${orderId}/payments`,
        );
        const current = list.items.find((p) => p.MaGiaoDich === qr.MaGiaoDich);
        if (!current) return;
        if (current.TrangThai === "Thành công") onPaid?.({ change: null });
        if (current.TrangThai !== qr.TrangThai) setQr({ ...qr, ...current });
      } catch {
        // A dropped poll is retried on the next tick.
      }
    }, 3000);
    return () => clearInterval(id);
  }, [qr, orderId, onPaid]);

  if (detail.status === "loading") return <LoadingState rows={3} />;
  if (detail.status === "error")
    return <ErrorState message={detail.message} onRetry={detail.reload} />;

  const { order, names } = detail.data;
  const lines = order.lines ?? [];
  const total = lines
    .filter((l) => l.TrangThai !== "Đã hủy")
    .reduce((sum, l) => sum + l.DonGia * l.SoLuong, 0);
  const expired = remaining === "Hết hạn" || qr?.TrangThai === "Hết hạn";
  const live = qr?.TrangThai === "Chờ xác nhận" && !expired;
  const reconciling = order.TrangThai === "Chờ đối soát";
  const settled = order.TrangThai === "Đã thanh toán";
  const locked = order.TrangThai !== "Đang mở";

  async function run(action: () => Promise<void>, fallback: string) {
    setError(null);
    setMessage(null);
    try {
      await action();
    } catch (e: unknown) {
      setError(messageOf(e, fallback));
    }
  }

  async function loadInvoice() {
    await run(async () => {
      setInvoice(
        await apiFetch<InvoiceDetail>(`/sales/orders/${orderId}/invoice`),
      );
    }, "Không tải được hóa đơn.");
  }

  const payCash = () =>
    run(async () => {
      await apiFetch(`/sales/orders/${orderId}/pay/cash`, {
        method: "POST",
        body: {},
      });
      setMessage("Đã thu tiền mặt.");
      await detail.reload();
      await loadInvoice();
      onPaid?.({ change: digits(given) - total });
    }, "Thanh toán tiền mặt thất bại.");

  const createQr = () =>
    run(async () => {
      setQr(
        await apiFetch<Payment>(`/sales/orders/${orderId}/pay/qr`, {
          method: "POST",
          body: {},
        }),
      );
      setInvoice(null);
    }, "Không tạo được mã QR.");

  const checkQr = () => {
    if (!qr) return;
    return run(async () => {
      const result = await apiFetch<{ TrangThai: string }>(
        `/sales/payments/${qr.MaGiaoDich}/check`,
        { method: "POST", body: {} },
      );
      setQr({ ...qr, TrangThai: result.TrangThai });
      if (result.TrangThai === "Thành công") onPaid?.({ change: null });
      else setMessage("Chưa thấy giao dịch. Chờ thêm hoặc kiểm tra lại sau.");
    }, "Không kiểm tra được giao dịch.");
  };

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

  const reportBankTransfer = () => {
    if (!qr) return;
    return run(async () => {
      await apiFetch(`/sales/orders/${orderId}/reconcile`, {
        method: "POST",
        body: { payment_id: qr.MaGiaoDich },
      });
      setMessage("Đã chuyển order sang chờ đối soát.");
      await detail.reload();
    }, "Không đối soát được giao dịch.");
  };

  const saveBankRef = () => {
    if (!qr) return;
    return run(async () => {
      await apiFetch(`/sales/payments/${qr.MaGiaoDich}/reference`, {
        method: "POST",
        body: { reference: bankRef },
      });
      setMessage("Đã lưu mã tham chiếu ngân hàng.");
    }, "Không lưu được mã tham chiếu.");
  };

  const resolve = (outcome: "received" | "not_received") => {
    if (!qr) return;
    return run(async () => {
      await apiFetch(`/sales/payments/${qr.MaGiaoDich}/resolve`, {
        method: "POST",
        body: { outcome },
      });
      setMessage(
        outcome === "received"
          ? "Đã xác nhận nhận được tiền."
          : "Đã ghi nhận không có giao dịch.",
      );
      await detail.reload();
      if (outcome === "received") await loadInvoice();
    }, "Không xử lý được đối soát.");
  };

  const cancelOrder = () =>
    run(async () => {
      await apiFetch(`/sales/orders/${orderId}/cancel`, {
        method: "POST",
        body: { reason },
      });
      setReason("");
      setMessage("Đã hủy order.");
      detail.reload();
    }, "Hủy order thất bại.");

  const reprintInvoice = () =>
    run(async () => {
      setInvoice(
        await apiFetch<InvoiceDetail>(
          `/sales/orders/${orderId}/invoice/reprint`,
          {
            method: "POST",
            body: {},
          },
        ),
      );
    }, "In lại hóa đơn thất bại.");

  return (
    <section
      aria-label="Thanh toán"
      className="rounded-container border border-border bg-surface print:hidden"
    >
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-border p-4">
        <div>
          <p className="text-xs text-subtle">Order</p>
          <p className="font-mono text-base font-medium">
            {order.MaOrderHienThi}
          </p>
        </div>
        <StatusBadge status={order.TrangThai} />
      </header>

      {lines.length > 0 && (
        <ul className="divide-y divide-border">
          {lines.map((l) => (
            <li
              key={l.MaChiTietOrder}
              className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-3 gap-y-1 px-4 py-2.5"
            >
              <span className="font-medium">
                {names.get(l.MaMon) ?? `Món #${l.MaMon}`}
                <span className="ml-1.5 font-normal text-muted tabular-nums">
                  × {l.SoLuong}
                </span>
              </span>
              <span className="text-right tabular-nums">
                {formatVnd(l.DonGia * l.SoLuong)}
              </span>
              <span>
                <StatusBadge status={l.TrangThai} />
              </span>
            </li>
          ))}
        </ul>
      )}

      <div className="space-y-4 border-t border-border p-4">
        <div className="flex items-baseline justify-between">
          <span className="text-muted">Tổng tiền</span>
          <span className="text-2xl font-bold tracking-tight tabular-nums">
            {formatVnd(total)}
          </span>
        </div>

        <div
          role="radiogroup"
          aria-label="Phương thức thanh toán"
          className="grid grid-cols-2 gap-2"
        >
          {(
            [
              ["cash", "Tiền mặt", "Nhập tiền khách đưa, tính tiền thối", Banknote],
              ["qr", "QR chuyển khoản", "Khách quét mã, hệ thống tự xác nhận", QrCode],
            ] as const
          ).map(([value, title, hint, Icon]) => (
            <label
              key={value}
              className={cn(
                "grid cursor-pointer gap-1 rounded-container border px-3.5 py-3 has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-primary",
                activeMethod === value
                  ? "border-ink bg-surface-sunken ring-1 ring-ink"
                  : "border-border-strong bg-surface",
              )}
            >
              <input
                type="radio"
                name={`method-${orderId}`}
                value={value}
                checked={activeMethod === value}
                onChange={() => setMethod(value)}
                className="sr-only"
              />
              <span className="flex items-center gap-2 text-[15px] font-bold">
                <Icon className="size-4" aria-hidden />
                {title}
              </span>
              <span className="text-xs text-muted">{hint}</span>
            </label>
          ))}
        </div>

        {activeMethod === "cash" && (
          <div className="space-y-3">
            <Label htmlFor={`given-${orderId}`}>Tiền khách đưa</Label>
            <Input
              id={`given-${orderId}`}
              inputMode="numeric"
              className="h-12 text-xl font-bold tabular-nums"
              value={given}
              onChange={(e) => setGiven(e.target.value)}
              placeholder={formatVnd(total)}
            />
            <div className="flex flex-wrap gap-1.5">
              {quickAmounts(total).map((amount) => (
                <Button
                  key={amount}
                  variant="secondary"
                  className="h-11"
                  onClick={() => setGiven(String(amount))}
                >
                  {amount === total ? "Vừa đủ" : formatVnd(amount)}
                </Button>
              ))}
            </div>
            <div className="flex items-baseline justify-between rounded-control bg-surface-sunken px-3.5 py-3">
              <span>Tiền thối</span>
              <span
                data-testid="cash-change"
                className="text-2xl font-bold tabular-nums"
              >
                {digits(given) >= total ? formatVnd(digits(given) - total) : "—"}
              </span>
            </div>
            <Button
              size="pos"
              className="w-full"
              onClick={payCash}
              disabled={locked || digits(given) < total}
            >
              <CircleCheck />
              Xác nhận đã thu {formatVnd(total)}
            </Button>
          </div>
        )}

        {activeMethod === "qr" && !live && (
          <Button
            size="pos"
            className="w-full"
            onClick={createQr}
            disabled={locked || reconciling}
          >
            <QrCode />
            Tạo mã QR
          </Button>
        )}

        {activeMethod === "qr" && qr && qr.TrangThai !== "Đã hủy" && (
          <div className="space-y-3 rounded-control border border-border bg-canvas p-4">
            <div className="flex items-center justify-between gap-2">
              <span className="flex items-center gap-2 font-medium">
                <QrCode className="size-4" aria-hidden />
                Giao dịch QR
              </span>
              <StatusBadge status={qr.TrangThai} />
            </div>
            {qr.qr_image_url && live && (
              <div className="grid gap-4 sm:grid-cols-[192px_minmax(0,1fr)] sm:items-center">
                {/* eslint-disable-next-line @next/next/no-img-element -- external SePay host, no remote host config */}
                <img
                  src={qr.qr_image_url}
                  alt={`Mã VietQR thanh toán ${formatVnd(total)}`}
                  className="size-48 rounded-control border border-border bg-white p-2"
                />
                <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1.5">
                  <dt className="text-muted">Ngân hàng</dt>
                  <dd className="font-semibold">{qr.bank_code}</dd>
                  <dt className="text-muted">Số tài khoản</dt>
                  <dd className="font-mono font-semibold">{qr.bank_account}</dd>
                  <dt className="text-muted">Chủ tài khoản</dt>
                  <dd className="font-semibold">{qr.account_name}</dd>
                  <dt className="text-muted">Nội dung</dt>
                  <dd className="font-mono text-base font-bold">
                    {qr.payment_code}
                  </dd>
                </dl>
                <p className="text-xs font-semibold text-warning-fg sm:col-span-2">
                  Môi trường thử nghiệm SePay
                </p>
              </div>
            )}
            {remaining && (
              <div className="flex items-baseline gap-2">
                <span className="text-muted">Còn hiệu lực</span>
                <span
                  className={
                    expired
                      ? "font-semibold text-danger-fg"
                      : "font-mono text-2xl font-medium tabular-nums"
                  }
                >
                  {remaining}
                </span>
              </div>
            )}
            <div className="flex flex-wrap gap-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={cancelQr}
                disabled={!live}
              >
                Hủy QR
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={checkQr}
                disabled={!live}
              >
                <RefreshCw />
                Kiểm tra lại
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={createQr}
                disabled={!!live || locked}
              >
                <TimerReset />
                Tạo mã QR mới
              </Button>
              {expired && !reconciling && (
                <Button size="sm" onClick={reportBankTransfer}>
                  Khách báo đã chuyển khoản
                </Button>
              )}
            </div>

            {reconciling && (
              <div className="space-y-3 border-t border-border pt-3">
                <div>
                  <Label htmlFor={`bank-ref-${orderId}`}>
                    Mã tham chiếu ngân hàng
                  </Label>
                  <div className="mt-1.5 flex gap-2">
                    <Input
                      id={`bank-ref-${orderId}`}
                      className="h-10 flex-1"
                      placeholder="Ví dụ: FT2609xxxxx"
                      value={bankRef}
                      onChange={(e) => setBankRef(e.target.value)}
                    />
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={saveBankRef}
                      disabled={bankRef.trim() === ""}
                    >
                      Lưu
                    </Button>
                  </div>
                </div>
                {isManager && (
                  <div className="flex flex-wrap gap-2">
                    <Button size="sm" onClick={() => resolve("received")}>
                      Xác nhận đã nhận tiền
                    </Button>
                    <Button
                      size="sm"
                      variant="outlineDanger"
                      onClick={() => resolve("not_received")}
                    >
                      Không có giao dịch
                    </Button>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {error && (
          <p role="alert" className="flex items-start gap-1.5 text-danger-fg">
            <CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
            {error}
          </p>
        )}
        {message && (
          <p role="status" className="flex items-start gap-1.5 text-success-fg">
            <CircleCheck className="mt-0.5 size-4 shrink-0" aria-hidden />
            {message}
          </p>
        )}
      </div>

      {isManager && !locked && !live && (
        <div className="space-y-2 border-t border-border p-4">
          <Label htmlFor={`cancel-reason-${orderId}`}>Lý do hủy order</Label>
          <div className="flex flex-wrap gap-2">
            <Input
              id={`cancel-reason-${orderId}`}
              className="h-11 min-w-0 flex-1"
              placeholder="Ví dụ: khách đổi ý trước khi bếp làm"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
            <Button
              variant="outlineDanger"
              size="pos"
              onClick={cancelOrder}
              disabled={reason.trim() === ""}
            >
              Hủy toàn bộ order
            </Button>
          </div>
        </div>
      )}

      {settled && !invoice && (
        <div className="border-t border-border p-4">
          <Button variant="secondary" size="sm" onClick={loadInvoice}>
            <Receipt />
            Xem hóa đơn
          </Button>
        </div>
      )}

      {invoice && (
        <InvoicePreview invoice={invoice} onReprint={reprintInvoice} />
      )}
    </section>
  );
}

export function InvoicePreview({
  invoice,
  onReprint,
}: {
  invoice: InvoiceDetail;
  onReprint: () => void;
}) {
  return (
    <div className="border-t border-border p-4 print:border-0 print:p-0">
      <div
        id="invoice-print-area"
        className="space-y-3 rounded-control border border-border bg-canvas p-4 print:border-0 print:bg-white print:p-0"
      >
        <div className="text-center">
          <p className="font-semibold">{invoice.TenNhaHang ?? "Nhà hàng"}</p>
          {invoice.DiaChi && (
            <p className="text-xs text-muted">{invoice.DiaChi}</p>
          )}
          <p className="mt-1 text-xs text-subtle">Hóa đơn {invoice.SoHoaDon}</p>
        </div>
        {invoice.lines && (
          <ul className="divide-y divide-border">
            {invoice.lines.map((l) => (
              <li
                key={l.MaMon}
                className="flex justify-between gap-2 py-1.5 text-sm"
              >
                <span>
                  {l.TenMon} × {l.SoLuong}
                </span>
                <span className="tabular-nums">
                  {formatVnd(l.DonGia * l.SoLuong)}
                </span>
              </li>
            ))}
          </ul>
        )}
        <div className="flex justify-between border-t border-border pt-2 font-semibold">
          <span>Tổng cộng</span>
          <span className="tabular-nums">{formatVnd(invoice.TongTien)}</span>
        </div>
        {invoice.PhuongThucThanhToan && (
          <p className="text-xs text-subtle">
            Phương thức: {invoice.PhuongThucThanhToan}
          </p>
        )}
      </div>
      <div className="mt-3 flex gap-2 print:hidden">
        <Button size="sm" onClick={() => window.print()}>
          <Printer />
          In hóa đơn
        </Button>
        <Button size="sm" variant="secondary" onClick={onReprint}>
          In lại
        </Button>
      </div>
    </div>
  );
}
