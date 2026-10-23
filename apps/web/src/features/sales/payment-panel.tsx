"use client";

import {
  Banknote,
  CircleAlert,
  CircleCheck,
  Copy,
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
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, apiFetch } from "@/lib/api-client";
import { escapeHtml, printDocument } from "@/lib/print";
import { formatDateTime, formatVnd } from "@/lib/format";
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
  ThoiDiemTao?: string | null;
  SoTien?: number;
  MaThamChieuNganHang?: string | null;
  AnhChungTu?: string | null;
  qr_image_url?: string;
  payment_code?: string;
  bank_code?: string;
  bank_account?: string;
  account_name?: string;
  simulated?: boolean;
};

type ProvisionalInvoice = {
  TieuDe: string;
  MaOrderHienThi?: string | null;
  TenNhaHang?: string | null;
  DiaChi?: string | null;
  TongTien: number;
  lines?: Array<{
    MaMon: number;
    TenMon: string;
    SoLuong: number;
    DonGia: number;
    ThanhTien: number;
  }>;
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
// A QR moving to any of these while polling means the reconciliation UI (which
// keys off the order status) needs a fresh order, not just a fresh QR object.
const NON_SUCCESS_STATUSES = ["Chờ đối soát", "Hết hạn", "Đã hủy"];

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
  const [busy, setBusy] = useState(false);
  const [reason, setReason] = useState("");
  const [bankRef, setBankRef] = useState("");
  const [verifyOpen, setVerifyOpen] = useState(false);
  const [verifyMode, setVerifyMode] = useState<"request" | "reference">(
    "request",
  );
  const [verifyRef, setVerifyRef] = useState("");
  const [verifyNote, setVerifyNote] = useState("");
  const [verifyEvidence, setVerifyEvidence] = useState("");
  const [verifyError, setVerifyError] = useState<string | null>(null);
  const [managerAction, setManagerAction] = useState<
    "reopen" | "close" | "check" | null
  >(null);
  const [actionReason, setActionReason] = useState("");
  const [actionOutcome, setActionOutcome] = useState("");
  const [actionNote, setActionNote] = useState("");
  const [invoice, setInvoice] = useState<InvoiceDetail | null>(null);
  const [printingProvisional, setPrintingProvisional] = useState(false);
  const [method, setMethod] = useState<"cash" | "qr">("cash");
  const [given, setGiven] = useState("");
  const isManager = loadSession()?.role === "MANAGER";

  const latestQr = detail.status === "ready" ? detail.data.latestQr : null;
  const qr = qrOverride ?? latestQr;

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
        if (current.TrangThai === "Thành công") {
          onPaid?.({ change: null });
        } else if (
          current.TrangThai !== qr.TrangThai &&
          NON_SUCCESS_STATUSES.includes(current.TrangThai)
        ) {
          // The reconciliation UI and buttons key off the order status, so a
          // status-only QR update isn't enough — reload the order too.
          await detail.reload();
        }
        if (current.TrangThai !== qr.TrangThai) setQr({ ...qr, ...current });
      } catch {
        // A dropped poll is retried on the next tick.
      }
    }, 3000);
    return () => clearInterval(id);
    // `detail` is a fresh object every render; only its stable `reload` matters here.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [qr, orderId, onPaid, detail.reload]);

  async function printProvisional() {
    setPrintingProvisional(true);
    try {
      const bill = await apiFetch<ProvisionalInvoice>(
        `/sales/orders/${orderId}/provisional-invoice`,
      );
      const rows = (bill.lines ?? [])
        .map(
          (line) =>
            `<tr><td>${escapeHtml(line.TenMon)} × ${line.SoLuong}</td>` +
            `<td class="num">${line.ThanhTien.toLocaleString("vi-VN")} ₫</td></tr>`,
        )
        .join("");
      const printed = printDocument(
        bill.TieuDe,
        `<div class="notice">${escapeHtml(bill.TieuDe)}</div>` +
          `<h1>${escapeHtml(bill.TenNhaHang ?? "Nhà hàng")}</h1>` +
          `<p class="muted">${escapeHtml(bill.DiaChi ?? "")}</p>` +
          `<p class="muted">Order ${escapeHtml(bill.MaOrderHienThi ?? orderId)}</p>` +
          `<table>${rows}</table>` +
          `<div class="total"><span>Tổng cộng</span>` +
          `<span>${bill.TongTien.toLocaleString("vi-VN")} ₫</span></div>`,
      );
      if (!printed) setMessage("Trình duyệt chặn cửa sổ in phiếu tạm tính.");
    } catch {
      setMessage("Không lấy được phiếu tạm tính.");
    } finally {
      setPrintingProvisional(false);
    }
  }

  // A paid order only needs its invoice; load it once the order settles so a
  // reload never shows the cash/QR controls again.
  const settledNow =
    detail.status === "ready" &&
    detail.data.order.TrangThai === "Đã thanh toán";
  useEffect(() => {
    if (!settledNow) return;
    let cancelled = false;
    apiFetch<InvoiceDetail>(`/sales/orders/${orderId}/invoice`)
      .then((data) => {
        if (!cancelled) setInvoice(data);
      })
      .catch(() => {
        // The "Xem hóa đơn" button stays available if this call fails.
      });
    return () => {
      cancelled = true;
    };
  }, [settledNow, orderId]);

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
  const verifying = order.TrangThai === "Chờ xác minh thanh toán";
  const closedUnpaid = order.TrangThai === "Đóng – chưa thu được tiền";
  const settled = order.TrangThai === "Đã thanh toán";
  const locked = order.TrangThai !== "Đang mở";
  // Only a QR that's still actionable (live, reconciliation or verification)
  // should keep the cashier out of the cash tab — an expired/cancelled QR can't
  // be cancelled through the API, so locking cash on it would strand the order.
  const qrLocksCash = live || reconciling || verifying || closedUnpaid;
  const activeMethod: "cash" | "qr" = qrLocksCash ? "qr" : method;

  async function run(action: () => Promise<void>, fallback: string) {
    setError(null);
    setMessage(null);
    setBusy(true);
    try {
      await action();
    } catch (e: unknown) {
      setError(messageOf(e, fallback));
    } finally {
      setBusy(false);
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
      await detail.reload();
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
      setQr({ ...qr, TrangThai: "Đã hủy" });
      setRemaining(null);
      setMessage("Đã hủy giao dịch QR.");
      await detail.reload();
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

  const requestVerification = () => {
    setVerifyMode("request");
    setVerifyRef("");
    setVerifyNote("");
    setVerifyEvidence("");
    setVerifyError(null);
    setVerifyOpen(true);
  };

  const addEvidence = () => {
    setVerifyMode("reference");
    setVerifyRef(qr?.MaThamChieuNganHang ?? "");
    setVerifyNote("");
    setVerifyEvidence(qr?.AnhChungTu ?? "");
    setVerifyError(null);
    setVerifyOpen(true);
  };

  const submitVerification = () => {
    if (!qr) return;
    if (!verifyRef.trim()) {
      setVerifyError("Nhập mã giao dịch ngân hàng/ví do khách cung cấp.");
      return;
    }
    return run(async () => {
      if (verifyMode === "reference") {
        await apiFetch(`/sales/payments/${qr.MaGiaoDich}/reference`, {
          method: "POST",
          body: {
            reference: verifyRef.trim(),
            evidence: verifyEvidence || null,
          },
        });
        setMessage("Đã bổ sung mã giao dịch/bằng chứng.");
        setVerifyOpen(false);
        await detail.reload();
        return;
      }
      const result = await apiFetch<{ TrangThai: string }>(
        `/sales/payments/${qr.MaGiaoDich}/request-verification`,
        {
          method: "POST",
          body: {
            reference: verifyRef.trim(),
            note: verifyNote.trim() || null,
            evidence: verifyEvidence || null,
          },
        },
      );
      setQr({ ...qr, TrangThai: result.TrangThai });
      setMessage("Đã ghi nhận khách báo chuyển tiền; chờ quản lý xác minh.");
      setVerifyOpen(false);
      setQr(null);
      setRemaining(null);
      await detail.reload();
    }, "Không gửi được yêu cầu xác minh.");
  };

  const readEvidence = (file: File | undefined) => {
    if (!file) return;
    if (file.size > 1_500_000) {
      setVerifyError("Ảnh xác nhận tối đa 1,5 MB.");
      return;
    }
    const reader = new FileReader();
    reader.onload = () => setVerifyEvidence(String(reader.result ?? ""));
    reader.onerror = () => setVerifyError("Không đọc được ảnh xác nhận.");
    reader.readAsDataURL(file);
  };

  const reopenPayment = () => {
    setActionReason("");
    setActionOutcome("");
    setManagerAction("reopen");
  };

  const applyLatePayment = () => {
    if (!qr) return;
    return run(async () => {
      await apiFetch(`/sales/payments/${qr.MaGiaoDich}/apply-late`, {
        method: "POST",
        body: {},
      });
      setMessage("Đã áp dụng khoản tiền đến muộn và phát hành hóa đơn.");
      setQr(null);
      setRemaining(null);
      await detail.reload();
      await loadInvoice();
      onPaid?.({ change: null });
    }, "Không áp dụng được khoản tiền đến muộn.");
  };

  const closeUnpaid = () => {
    setActionReason("");
    setActionOutcome("");
    setManagerAction("close");
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

  const resolve = (outcome: "received" | "not_received", note?: string) => {
    if (!qr) return;
    let receivedAmount: number | undefined;
    if (outcome === "received") {
      // P1: confirming receipt must state how much actually arrived.
      const raw = window.prompt(
        `Số tiền thực nhận (tổng order ${total.toLocaleString("vi-VN")} ₫):`,
        String(total),
      );
      if (raw === null) return;
      receivedAmount = Number(raw);
      if (!Number.isFinite(receivedAmount)) {
        setMessage("Số tiền không hợp lệ.");
        return;
      }
    }
    return run(async () => {
      await apiFetch(`/sales/payments/${qr.MaGiaoDich}/resolve`, {
        method: "POST",
        body: {
          outcome,
          ...(note ? { note } : {}),
          ...(receivedAmount !== undefined
            ? { received_amount: receivedAmount }
            : {}),
        },
      });
      setMessage(
        outcome === "received"
          ? "Đã xác nhận nhận được tiền."
          : "Đã ghi nhận không có giao dịch.",
      );
      setQr(null);
      setRemaining(null);
      await detail.reload();
      if (outcome === "received") {
        await loadInvoice();
        onPaid?.({ change: null });
      }
    }, "Không xử lý được đối soát.");
  };

  const submitManagerAction = () => {
    if (!qr || !managerAction) return;
    if (managerAction === "check") {
      if (!actionNote.trim()) return;
      return run(async () => {
        await apiFetch(`/sales/payments/${qr.MaGiaoDich}/resolve`, {
          method: "POST",
          body: { outcome: "not_received", note: actionNote.trim() },
        });
        setMessage("Đã lưu kết quả kiểm tra; order vẫn chờ xác minh.");
        setManagerAction(null);
        await detail.reload();
      }, "Không lưu được kết quả kiểm tra.");
    }
    if (!actionReason.trim() || !actionOutcome.trim()) return;
    const isClose = managerAction === "close";
    return run(
      async () => {
        await apiFetch(
          isClose
            ? `/sales/orders/${orderId}/close-unpaid`
            : `/sales/payments/${qr.MaGiaoDich}/reopen`,
          {
            method: "POST",
            body: {
              reason: actionReason.trim(),
              outcome: actionOutcome.trim(),
            },
          },
        );
        setMessage(
          isClose
            ? "Đã đóng order ở trạng thái chưa thu được tiền."
            : "Đã mở lại order để thu tiền lần khác.",
        );
        setManagerAction(null);
        setQr(null);
        setRemaining(null);
        await detail.reload();
      },
      isClose ? "Không đóng được order." : "Không mở lại được thanh toán.",
    );
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
      // The reprint command must actually reach the printer, not only refresh the preview.
      window.print();
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

        {!settled && !closedUnpaid && (
          <Button
            variant="secondary"
            className="w-full"
            onClick={printProvisional}
            disabled={printingProvisional}
          >
            In phiếu tạm tính
          </Button>
        )}

        {!settled && !closedUnpaid && (
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
        {!settled && !closedUnpaid && qrLocksCash && (
          <p className="text-xs text-muted">
            Đang có giao dịch QR. Hủy QR để chuyển sang tiền mặt.
          </p>
        )}

        {!settled && !closedUnpaid && activeMethod === "cash" && (
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

        {!settled && !closedUnpaid && activeMethod === "qr" && !live && (
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

        {!settled &&
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
                  {/* eslint-disable-next-line @next/next/no-img-element -- SePay host or a generated data URI, so next/image does not apply */}
                  <img
                    src={qr.qr_image_url}
                    alt={
                      qr.simulated
                        ? `Mã QR mô phỏng thanh toán ${formatVnd(total)}`
                        : `Mã VietQR thanh toán ${formatVnd(total)}`
                    }
                    className="size-48 rounded-control border border-border bg-white p-2"
                  />
                  <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1.5">
                    {!qr.simulated && (
                      <>
                        <dt className="text-muted">Ngân hàng</dt>
                        <dd className="font-semibold">{qr.bank_code}</dd>
                        <dt className="text-muted">Số tài khoản</dt>
                        <dd className="font-mono font-semibold">
                          {qr.bank_account}
                        </dd>
                        <dt className="text-muted">Chủ tài khoản</dt>
                        <dd className="font-semibold">{qr.account_name}</dd>
                      </>
                    )}
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
                    {qr.simulated
                      ? "Mã QR mô phỏng — không chuyển tiền thật."
                      : "Môi trường thử nghiệm SePay"}
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
                {expired && !reconciling && !verifying && (
                  <Button size="sm" onClick={reportBankTransfer}>
                    Khách báo đã chuyển khoản
                  </Button>
                )}
                {live && !verifying && (
                  <Button size="sm" onClick={requestVerification}>
                    Khách báo đã chuyển tiền
                  </Button>
                )}
              </div>

              {verifying && (
                <div className="space-y-3 border-t border-border pt-3">
                  <p className="text-sm text-muted-fg">
                    Order đang chờ xác minh thanh toán. Không thể thêm món hoặc
                    thu tiền mặt cho tới khi quản lý xử lý.
                  </p>
                  <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-sm">
                    {qr?.SoTien !== undefined && (
                      <>
                        <dt className="text-muted">Số tiền</dt>
                        <dd className="text-right tabular-nums">
                          {formatVnd(qr.SoTien)}
                        </dd>
                      </>
                    )}
                    <dt className="text-muted">Mã giao dịch</dt>
                    <dd className="text-right">
                      {qr?.MaThamChieuNganHang ?? "Chưa nhập"}
                    </dd>
                    <dt className="text-muted">Tạo lúc</dt>
                    <dd className="text-right">
                      {formatDateTime(qr?.ThoiDiemTao ?? null)}
                    </dd>
                  </dl>
                  {qr?.AnhChungTu && (
                    <a
                      href={qr.AnhChungTu}
                      target="_blank"
                      rel="noreferrer"
                      className="text-sm font-semibold text-primary underline"
                    >
                      Xem ảnh xác nhận
                    </a>
                  )}
                  <Button size="sm" variant="secondary" onClick={addEvidence}>
                    Bổ sung bằng chứng
                  </Button>
                  {isManager && (
                    <div className="flex flex-wrap gap-2">
                      <Button size="sm" onClick={() => resolve("received")}>
                        Xác nhận đã nhận tiền
                      </Button>
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => {
                          setActionNote("");
                          setManagerAction("check");
                        }}
                      >
                        Lưu kết quả chưa đủ căn cứ
                      </Button>
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={reopenPayment}
                      >
                        Mở lại thanh toán
                      </Button>
                      <Button
                        size="sm"
                        variant="outlineDanger"
                        onClick={closeUnpaid}
                      >
                        Đóng chưa thu
                      </Button>
                    </div>
                  )}
                </div>
              )}

              {closedUnpaid && (
                <div className="space-y-3 border-t border-border pt-3">
                  <p className="text-sm text-muted-fg">
                    Order đã đóng vì chưa thu được tiền. Khi khoản chuyển đến
                    muộn, quản lý có thể áp dụng một lần và phát hành hóa đơn.
                  </p>
                  {isManager && qr && (
                    <Button size="sm" onClick={applyLatePayment}>
                      Áp dụng khoản đến muộn
                    </Button>
                  )}
                </div>
              )}

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
                  <Button size="sm" variant="secondary" onClick={addEvidence}>
                    Bổ sung bằng chứng
                  </Button>
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

      <Dialog open={verifyOpen} onOpenChange={setVerifyOpen}>
        <DialogContent className="w-[min(28rem,calc(100vw-2rem))]">
          <DialogHeader>
            <DialogTitle>
              {verifyMode === "reference"
                ? "Bổ sung bằng chứng"
                : "Khách báo đã chuyển tiền"}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid gap-1.5">
              <Label htmlFor={`verify-ref-${orderId}`}>
                Mã giao dịch ngân hàng/ví
              </Label>
              <Input
                id={`verify-ref-${orderId}`}
                value={verifyRef}
                onChange={(e) => setVerifyRef(e.target.value)}
                placeholder="Ví dụ: FT2609xxxxx"
              />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor={`verify-note-${orderId}`}>
                Thông tin bổ sung
              </Label>
              <Input
                id={`verify-note-${orderId}`}
                value={verifyNote}
                onChange={(e) => setVerifyNote(e.target.value)}
                placeholder="Ví dụ: khách gửi lúc 19:05"
              />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor={`verify-image-${orderId}`}>
                Ảnh xác nhận (tuỳ chọn)
              </Label>
              <input
                id={`verify-image-${orderId}`}
                type="file"
                accept="image/*"
                className="text-sm"
                onChange={(e) => readEvidence(e.target.files?.[0])}
              />
              {verifyEvidence && (
                <p className="text-xs text-success-fg">Đã đính kèm ảnh.</p>
              )}
            </div>
            {verifyError && (
              <p role="alert" className="text-sm text-danger-fg">
                {verifyError}
              </p>
            )}
          </div>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setVerifyOpen(false)}>
              Đóng
            </Button>
            <Button onClick={submitVerification} disabled={busy}>
              {verifyMode === "reference"
                ? "Lưu bằng chứng"
                : "Gửi yêu cầu xác minh"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={managerAction !== null}
        onOpenChange={(open) => !open && setManagerAction(null)}
      >
        <DialogContent className="w-[min(28rem,calc(100vw-2rem))]">
          <DialogHeader>
            <DialogTitle>
              {managerAction === "check"
                ? "Lưu kết quả kiểm tra"
                : managerAction === "close"
                  ? "Đóng order chưa thu được tiền"
                  : "Mở lại thanh toán"}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {managerAction === "check" ? (
              <div className="grid gap-1.5">
                <Label htmlFor={`check-note-${orderId}`}>
                  Kết quả kiểm tra
                </Label>
                <Input
                  id={`check-note-${orderId}`}
                  value={actionNote}
                  onChange={(e) => setActionNote(e.target.value)}
                  placeholder="Ví dụ: chưa thấy giao dịch trên sao kê"
                />
              </div>
            ) : (
              <>
                <div className="grid gap-1.5">
                  <Label htmlFor={`action-reason-${orderId}`}>Lý do</Label>
                  <Input
                    id={`action-reason-${orderId}`}
                    value={actionReason}
                    onChange={(e) => setActionReason(e.target.value)}
                    placeholder="Ví dụ: khách xác nhận chưa chuyển"
                  />
                </div>
                <div className="grid gap-1.5">
                  <Label htmlFor={`action-outcome-${orderId}`}>
                    Kết quả xử lý bên ngoài
                  </Label>
                  <Input
                    id={`action-outcome-${orderId}`}
                    value={actionOutcome}
                    onChange={(e) => setActionOutcome(e.target.value)}
                    placeholder="Ví dụ: đã thống nhất thu lại bằng tiền mặt"
                  />
                </div>
              </>
            )}
          </div>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setManagerAction(null)}>
              Đóng
            </Button>
            <Button
              onClick={submitManagerAction}
              disabled={
                busy ||
                (managerAction === "check"
                  ? actionNote.trim() === ""
                  : actionReason.trim() === "" || actionOutcome.trim() === "")
              }
            >
              Lưu
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
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
          {invoice.ThoiDiemXuat && (
            <p className="text-xs text-subtle">
              Xuất lúc {formatDateTime(invoice.ThoiDiemXuat)}
            </p>
          )}
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
