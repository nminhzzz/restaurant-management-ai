"use client";

import {
  Banknote,
  CircleAlert,
  CircleCheck,
  Copy,
  FileText,
  Lock,
  Printer,
  QrCode,
  Receipt,
  RefreshCw,
  TimerReset,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";

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
import { useAction } from "@/lib/use-action";
import { useResource } from "@/lib/use-resource";
import { cn } from "@/lib/utils";

import { FieldsDialog, type FieldValues } from "./fields-dialog";
import { ProvisionalBillDialog } from "./provisional-bill";

type OrderLine = {
  MaChiTietOrder: number;
  MaMon: number;
  TenMon?: string | null;
  SoLuong: number;
  DonGia: number;
  TrangThai: string;
};

type Order = {
  MaOrder: number;
  MaOrderHienThi: string;
  TrangThai: string;
  TongTien?: number;
  DaKhoa?: boolean;
  lines?: OrderLine[];
};

type Payment = {
  MaGiaoDich: number;
  PhuongThuc: string;
  TrangThai: string;
  ThoiDiemTaoQR?: string | null;
  ThoiDiemHetHan?: string | null;
  MaThamChieuNganHang?: string | null;
  MaGiaoDichNganHang?: string | null;
  AnhChungTu?: string | null;
  TrangThaiNgoaiLe?: string | null;
  SoTienNgoaiLe?: number | null;
  qr_image_url?: string;
  payment_code?: string;
  bank_code?: string;
  bank_account?: string;
  account_name?: string;
};

type InvoiceDetail = {
  SoHoaDon: string;
  MaOrderHienThi?: string | null;
  TenNhaHang?: string | null;
  DiaChi?: string | null;
  ThoiDiemXuat?: string | null;
  PhuongThucThanhToan?: string | null;
  TongTien: number;
  SoLanIn: number;
  lines?: { MaMon: number; TenMon: string; SoLuong: number; DonGia: number }[];
};

const QR_LIVE = "Chờ xác nhận";
const QR_EXPIRED = "Hết hạn";
const QR_VERIFYING = "Chờ xác minh thanh toán";

const ORDER_OPEN = "Đang mở";
const ORDER_QR_WAITING = "Chờ xác nhận thanh toán";
const ORDER_VERIFYING = "Chờ xác minh thanh toán";
const ORDER_CLOSED_UNPAID = "Đóng – chưa thu được tiền";

const DRAFT_STATUSES = [ORDER_OPEN, ORDER_QR_WAITING, ORDER_VERIFYING];

function messageOf(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback;
}

async function loadDetail(orderId: number) {
  const [order, payments] = await Promise.all([
    apiFetch<Order>(`/sales/orders/${orderId}`),
    apiFetch<{ items: Payment[] }>(`/sales/orders/${orderId}/payments`).catch(
      () => ({ items: [] }),
    ),
  ]);
  const all = payments.items ?? [];
  // The newest QR attempt decides what the cashier sees; older ones are history.
  const latestQr =
    all
      .filter((p) => p.PhuongThuc === "QR")
      .sort((a, b) => b.MaGiaoDich - a.MaGiaoDich)[0] ?? null;
  return { order, latestQr };
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

type DialogKind = "verify" | "note" | "confirm" | "reopen" | "close" | null;

export function PaymentPanel({
  orderId,
  onPaid,
  onOrderChanged,
}: {
  orderId: number;
  onPaid?: (summary: { change: number | null }) => void;
  /** Called after the order's status may have changed, so sibling views reload. */
  onOrderChanged?: () => void;
}) {
  const fetcher = useCallback(() => loadDetail(orderId), [orderId]);
  const detail = useResource(fetcher);
  const reload = detail.reload;
  const action = useAction();

  const [remaining, setRemaining] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reason, setReason] = useState("");
  const [guestsLeft, setGuestsLeft] = useState(false);
  const [invoice, setInvoice] = useState<InvoiceDetail | null>(null);
  const [method, setMethod] = useState<"cash" | "qr">("cash");
  const [given, setGiven] = useState("");
  const [dialog, setDialog] = useState<DialogKind>(null);
  const [billOpen, setBillOpen] = useState(false);
  const isManager = loadSession()?.role === "MANAGER";

  const qr = detail.status === "ready" ? detail.data.latestQr : null;
  const notifyChanged = onOrderChanged;

  const refresh = useCallback(() => {
    reload();
    notifyChanged?.();
  }, [reload, notifyChanged]);

  useEffect(() => {
    if (!qr?.ThoiDiemHetHan || qr.TrangThai !== QR_LIVE) return;
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

  const qrId = qr?.MaGiaoDich;
  const qrStatus = qr?.TrangThai;
  useEffect(() => {
    // A live QR can be paid; a QR waiting for verification can still be paid in full
    // by the guest (FR-SALE-20), so both are polled.
    if (
      qrId === undefined ||
      (qrStatus !== QR_LIVE && qrStatus !== QR_VERIFYING)
    )
      return;
    const id = setInterval(async () => {
      try {
        const list = await apiFetch<{ items: Payment[] }>(
          `/sales/orders/${orderId}/payments`,
        );
        const current = list.items.find((p) => p.MaGiaoDich === qrId);
        if (!current || current.TrangThai === qrStatus) return;
        if (current.TrangThai === "Thành công") onPaid?.({ change: null });
        else refresh();
      } catch {
        // A dropped poll is retried on the next tick.
      }
    }, 3000);
    return () => clearInterval(id);
  }, [qrId, qrStatus, orderId, onPaid, refresh]);

  if (detail.status === "loading") return <LoadingState rows={3} />;
  if (detail.status === "error")
    return <ErrorState message={detail.message} onRetry={detail.reload} />;

  const { order } = detail.data;
  const lines = order.lines ?? [];
  const total =
    order.TongTien ??
    lines
      .filter((l) => l.TrangThai !== "Đã hủy")
      .reduce((sum, l) => sum + l.DonGia * l.SoLuong, 0);
  const expired = remaining === "Hết hạn" || qr?.TrangThai === QR_EXPIRED;
  const live = qr?.TrangThai === QR_LIVE && !expired;
  const verifying = order.TrangThai === ORDER_VERIFYING;
  const settled = order.TrangThai === "Đã thanh toán";
  const locked = order.DaKhoa ?? order.TrangThai !== ORDER_OPEN;
  const payable =
    order.TrangThai === ORDER_OPEN || order.TrangThai === ORDER_QR_WAITING;
  // A live QR keeps the cashier out of the cash tab: the server refuses cash until the
  // QR is cancelled, so the screen says so up front.
  const qrLocksCash = live;
  // Stay on the QR tab while the order is waiting for it, so the expiry and the
  // "Yêu cầu xác minh" action do not vanish when the countdown ends.
  const activeMethod: "cash" | "qr" =
    qrLocksCash ||
    order.TrangThai === ORDER_QR_WAITING ||
    remaining === QR_EXPIRED
      ? "qr"
      : method;
  const canVerify =
    !!qr && (qr.TrangThai === QR_LIVE || qr.TrangThai === QR_EXPIRED);

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
      refresh();
      await loadInvoice();
      onPaid?.({ change: digits(given) - total });
    }, "Thanh toán tiền mặt thất bại.");

  const createQr = () =>
    run(async () => {
      await apiFetch(`/sales/orders/${orderId}/pay/qr`, {
        method: "POST",
        body: {},
      });
      setInvoice(null);
      setRemaining(null);
      refresh();
    }, "Không tạo được mã QR.");

  const checkQr = () => {
    if (!qr) return;
    return run(async () => {
      const result = await apiFetch<{ TrangThai: string }>(
        `/sales/payments/${qr.MaGiaoDich}/check`,
        { method: "POST", body: {} },
      );
      if (result.TrangThai === "Thành công") onPaid?.({ change: null });
      else if (result.TrangThai !== qr.TrangThai) refresh();
      else setMessage("Chưa thấy giao dịch. Chờ thêm hoặc kiểm tra lại sau.");
    }, "Không kiểm tra được giao dịch.");
  };

  const copyTransferContent = async () => {
    if (!qr?.payment_code) return;
    try {
      await navigator.clipboard.writeText(qr.payment_code);
      toast.success("Đã sao chép nội dung chuyển khoản.");
    } catch {
      toast.error("Không sao chép được. Hãy đọc nội dung cho khách.");
    }
  };

  const cancelQr = () => {
    if (!qr) return;
    return run(async () => {
      await apiFetch(`/sales/payments/${qr.MaGiaoDich}/cancel`, {
        method: "POST",
        body: {},
      });
      setRemaining(null);
      setMessage("Đã hủy giao dịch QR.");
      refresh();
    }, "Hủy QR thất bại.");
  };

  const cancelOrder = () =>
    run(async () => {
      await apiFetch(`/sales/orders/${orderId}/cancel`, {
        method: "POST",
        body: { LyDoHuy: reason, KhachDaRoiDi: guestsLeft },
      });
      setReason("");
      setGuestsLeft(false);
      setMessage("Đã hủy order.");
      refresh();
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

  function closeDialog() {
    setDialog(null);
    action.clearError();
  }

  async function submitDialog(values: FieldValues) {
    if (!qr || !dialog) return;
    const base = `/sales/payments/${qr.MaGiaoDich}`;
    const optional = (value: string) => (value === "" ? undefined : value);
    const plans = {
      verify: {
        path: `${base}/verification`,
        body: {
          MaGiaoDichNganHang: optional(values.MaGiaoDichNganHang),
          AnhChungTu: optional(values.AnhChungTu),
          GhiChu: optional(values.GhiChu),
        },
        done: "Đã chuyển order sang chờ xác minh thanh toán.",
      },
      note: {
        path: `${base}/verification-notes`,
        body: {
          GhiChu: values.GhiChu,
          MaGiaoDichNganHang: optional(values.MaGiaoDichNganHang),
          AnhChungTu: optional(values.AnhChungTu),
        },
        done: "Đã lưu ghi chú xác minh.",
      },
      confirm: {
        path: `${base}/confirm-received`,
        body: {
          GhiChu: optional(values.GhiChu),
          MaGiaoDichNganHang: optional(values.MaGiaoDichNganHang),
        },
        done: "Đã xác nhận nhận tiền.",
      },
      reopen: {
        path: `${base}/reopen`,
        body: { LyDo: values.LyDo, KetQuaXuLy: values.KetQuaXuLy },
        done: "Đã mở lại thanh toán, order về trạng thái đang mở.",
      },
      close: {
        path: `${base}/close-unpaid`,
        body: { LyDo: values.LyDo, KetQuaXuLy: values.KetQuaXuLy },
        done: "Đã đóng order chưa thu được tiền.",
      },
    } as const;
    const plan = plans[dialog];
    const result = await action.run(
      () => apiFetch(plan.path, { method: "POST", body: plan.body }),
      plan.done,
    );
    if (result === undefined) return;
    closeDialog();
    if (dialog === "confirm") {
      refresh();
      await loadInvoice();
      onPaid?.({ change: null });
    } else {
      refresh();
    }
  }

  const reference = qr?.MaGiaoDichNganHang ?? qr?.MaThamChieuNganHang ?? null;

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
        <div className="flex items-center gap-2">
          {DRAFT_STATUSES.includes(order.TrangThai) && lines.length > 0 && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setBillOpen(true)}
            >
              <FileText />
              Phiếu tạm tính
            </Button>
          )}
          <StatusBadge status={order.TrangThai} />
        </div>
      </header>

      {lines.length > 0 && (
        <ul className="divide-y divide-border">
          {lines.map((l) => (
            <li
              key={l.MaChiTietOrder}
              className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-3 gap-y-1 px-4 py-2.5"
            >
              <span className="font-medium">
                {l.TenMon ?? `Món #${l.MaMon}`}
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

        {locked && (
          <p className="flex items-center gap-1.5 text-xs text-subtle">
            <Lock className="size-3.5 shrink-0" aria-hidden />
            Order đã khóa, không thể thêm, sửa hay hủy món.
          </p>
        )}

        {payable && (
          <div
            role="radiogroup"
            aria-label="Phương thức thanh toán"
            className="grid grid-cols-2 gap-2"
          >
            {(
              [
                [
                  "cash",
                  "Tiền mặt",
                  "Nhập tiền khách đưa, tính tiền thối",
                  Banknote,
                ],
                [
                  "qr",
                  "QR chuyển khoản",
                  "Khách quét mã, hệ thống tự xác nhận",
                  QrCode,
                ],
              ] as const
            ).map(([value, title, hint, Icon]) => {
              const disabled = value === "cash" && qrLocksCash;
              return (
                <label
                  key={value}
                  aria-disabled={disabled}
                  className={cn(
                    "grid cursor-pointer gap-1 rounded-container border px-3.5 py-3 has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-primary",
                    activeMethod === value
                      ? "border-ink bg-surface-sunken ring-1 ring-ink"
                      : "border-border-strong bg-surface",
                    disabled && "cursor-not-allowed opacity-50",
                  )}
                >
                  <input
                    type="radio"
                    name={`method-${orderId}`}
                    value={value}
                    checked={activeMethod === value}
                    disabled={disabled}
                    onChange={() => setMethod(value)}
                    className="sr-only"
                  />
                  <span className="flex items-center gap-2 text-[15px] font-bold">
                    <Icon className="size-4" aria-hidden />
                    {title}
                  </span>
                  <span className="text-xs text-muted">{hint}</span>
                </label>
              );
            })}
          </div>
        )}
        {payable && qrLocksCash && (
          <p className="text-xs text-muted">
            Đang có giao dịch QR. Hủy QR để chuyển sang tiền mặt.
          </p>
        )}

        {payable && activeMethod === "cash" && (
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
                {digits(given) >= total
                  ? formatVnd(digits(given) - total)
                  : "—"}
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

        {payable && activeMethod === "qr" && !live && (
          <Button
            size="pos"
            className="w-full"
            onClick={createQr}
            disabled={locked && order.TrangThai !== ORDER_QR_WAITING}
          >
            <QrCode />
            Tạo mã QR
          </Button>
        )}

        {payable &&
          activeMethod === "qr" &&
          qr &&
          qr.TrangThai !== "Đã hủy" && (
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
                    <dd className="font-mono font-semibold">
                      {qr.bank_account}
                    </dd>
                    <dt className="text-muted">Chủ tài khoản</dt>
                    <dd className="font-semibold">{qr.account_name}</dd>
                    <dt className="text-muted">Nội dung</dt>
                    <dd className="flex items-center gap-2 font-mono text-base font-bold">
                      {qr.payment_code}
                      <Button
                        type="button"
                        variant="secondary"
                        size="icon"
                        className="h-11 w-11 shrink-0"
                        aria-label="Sao chép nội dung chuyển khoản"
                        onClick={copyTransferContent}
                      >
                        <Copy className="size-4" aria-hidden />
                      </Button>
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
                {canVerify && (
                  <Button size="sm" onClick={() => setDialog("verify")}>
                    Yêu cầu xác minh
                  </Button>
                )}
              </div>
            </div>
          )}

        {verifying && (
          <div className="space-y-3 rounded-control border border-warning bg-warning-subtle p-4 text-warning-fg">
            <p className="font-semibold">Đang chờ xác minh thanh toán</p>
            <p className="text-sm">
              Khách báo đã chuyển khoản nhưng hệ thống chưa nhận được tiền.
              Order vẫn bị khóa. Nếu khách chuyển đủ số tiền, order tự xác nhận.
            </p>
            {qr && (reference || qr.AnhChungTu) && (
              <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-sm">
                {reference && (
                  <>
                    <dt>Mã giao dịch ngân hàng</dt>
                    <dd className="font-mono font-semibold">{reference}</dd>
                  </>
                )}
                {qr.AnhChungTu && (
                  <>
                    <dt>Chứng từ</dt>
                    <dd className="font-semibold">{qr.AnhChungTu}</dd>
                  </>
                )}
              </dl>
            )}
            <div className="flex flex-wrap gap-2">
              <Button
                size="sm"
                variant="secondary"
                onClick={() => setDialog("note")}
              >
                Thêm ghi chú xác minh
              </Button>
              <Button size="sm" variant="secondary" onClick={checkQr}>
                <RefreshCw />
                Kiểm tra lại
              </Button>
              {isManager && (
                <>
                  <Button size="sm" onClick={() => setDialog("confirm")}>
                    Xác nhận đã nhận tiền
                  </Button>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => setDialog("reopen")}
                  >
                    Mở lại thanh toán
                  </Button>
                  <Button
                    size="sm"
                    variant="outlineDanger"
                    onClick={() => setDialog("close")}
                  >
                    Đóng order chưa thu được tiền
                  </Button>
                </>
              )}
            </div>
            {!isManager && (
              <p className="text-xs">
                Chỉ quản lý được xác nhận nhận tiền, mở lại thanh toán hoặc đóng
                order.
              </p>
            )}
          </div>
        )}

        {order.TrangThai === ORDER_CLOSED_UNPAID && (
          <p className="rounded-control bg-surface-sunken p-3 text-sm text-muted">
            Order đã đóng, chưa thu được tiền. Nếu khoản chuyển khoản đến sau,
            quản lý xử lý trong danh sách ngoại lệ thanh toán.
          </p>
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

      {isManager && order.TrangThai === ORDER_OPEN && !live && (
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
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={guestsLeft}
              onChange={(e) => setGuestsLeft(e.target.checked)}
            />
            Khách đã rời đi
          </label>
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

      <ProvisionalBillDialog
        orderId={orderId}
        open={billOpen}
        onOpenChange={setBillOpen}
      />

      <FieldsDialog
        open={dialog === "verify"}
        onOpenChange={(open) => !open && closeDialog()}
        title="Yêu cầu xác minh thanh toán"
        description="Khách nói đã chuyển khoản nhưng hệ thống chưa nhận được. Nhập mã giao dịch ngân hàng hoặc ghi chú."
        fields={[
          { name: "MaGiaoDichNganHang", label: "Mã giao dịch ngân hàng" },
          { name: "AnhChungTu", label: "Chứng từ (ảnh hoặc đường dẫn)" },
          { name: "GhiChu", label: "Ghi chú", multiline: true },
        ]}
        requireOneOf={["MaGiaoDichNganHang", "GhiChu"]}
        confirmLabel="Gửi yêu cầu xác minh"
        pending={action.pending}
        error={action.error}
        onSubmit={submitDialog}
      />
      <FieldsDialog
        open={dialog === "note"}
        onOpenChange={(open) => !open && closeDialog()}
        title="Ghi chú xác minh"
        fields={[
          {
            name: "GhiChu",
            label: "Kết quả kiểm tra",
            required: true,
            multiline: true,
          },
          { name: "MaGiaoDichNganHang", label: "Mã giao dịch ngân hàng" },
          { name: "AnhChungTu", label: "Chứng từ bổ sung" },
        ]}
        confirmLabel="Lưu ghi chú"
        pending={action.pending}
        error={action.error}
        onSubmit={submitDialog}
      />
      <FieldsDialog
        open={dialog === "confirm"}
        onOpenChange={(open) => !open && closeDialog()}
        title="Xác nhận đã nhận tiền"
        description="Hệ thống sẽ ghi nhận thanh toán thành công và xuất một hóa đơn."
        fields={[
          { name: "MaGiaoDichNganHang", label: "Mã giao dịch ngân hàng" },
          { name: "GhiChu", label: "Ghi chú", multiline: true },
        ]}
        confirmLabel="Xác nhận đã nhận tiền"
        pending={action.pending}
        error={action.error}
        onSubmit={submitDialog}
      />
      <FieldsDialog
        open={dialog === "reopen"}
        onOpenChange={(open) => !open && closeDialog()}
        title="Mở lại thanh toán"
        description="Order trở về trạng thái đang mở để thu tiền lại. Giao dịch cũ được giữ làm lịch sử."
        fields={[
          { name: "LyDo", label: "Lý do", required: true, multiline: true },
          {
            name: "KetQuaXuLy",
            label: "Kết quả xử lý",
            required: true,
            multiline: true,
          },
        ]}
        confirmLabel="Mở lại thanh toán"
        pending={action.pending}
        error={action.error}
        onSubmit={submitDialog}
      />
      <FieldsDialog
        open={dialog === "close"}
        onOpenChange={(open) => !open && closeDialog()}
        title="Đóng order chưa thu được tiền"
        description="Order đóng không có hóa đơn và không tính vào doanh thu; kho vẫn giữ mức đã trừ."
        fields={[
          { name: "LyDo", label: "Lý do", required: true, multiline: true },
          {
            name: "KetQuaXuLy",
            label: "Kết quả xử lý",
            required: true,
            multiline: true,
          },
        ]}
        confirmLabel="Đóng order"
        danger
        pending={action.pending}
        error={action.error}
        onSubmit={submitDialog}
      />
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
