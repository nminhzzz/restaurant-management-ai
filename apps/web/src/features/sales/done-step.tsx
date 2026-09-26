"use client";

import { CircleCheck } from "lucide-react";
import { useCallback } from "react";

import { ErrorState, LoadingState } from "@/components/page-states";
import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api-client";
import { formatVnd } from "@/lib/format";
import { useResource } from "@/lib/use-resource";

import { InvoicePreview } from "./payment-panel";

type Invoice = Parameters<typeof InvoicePreview>[0]["invoice"];

export function DoneStep({
  orderId,
  change,
  onFinish,
}: {
  orderId: number;
  change: number | null;
  onFinish: () => void;
}) {
  const fetcher = useCallback(
    () => apiFetch<Invoice>(`/sales/orders/${orderId}/invoice`),
    [orderId],
  );
  const invoice = useResource(fetcher);

  if (invoice.status === "loading") return <LoadingState rows={3} />;
  if (invoice.status === "error")
    return <ErrorState message={invoice.message} onRetry={invoice.reload} />;

  const data = invoice.data;
  return (
    <section className="mx-auto grid max-w-lg justify-items-center gap-4 rounded-container border border-border bg-surface p-7 text-center">
      <span className="grid size-14 place-items-center rounded-container bg-success-subtle text-success-fg">
        <CircleCheck className="size-7" aria-hidden />
      </span>
      <h2 className="text-2xl font-bold tracking-tight">Đã thanh toán</h2>
      <dl className="grid w-full grid-cols-[auto_1fr] gap-x-4 gap-y-2 rounded-control bg-surface-sunken p-4 text-left">
        <dt className="text-muted">Số hoá đơn</dt>
        <dd className="text-right font-mono font-semibold">{data.SoHoaDon}</dd>
        <dt className="text-muted">Phương thức</dt>
        <dd className="text-right font-semibold">
          {data.PhuongThucThanhToan ?? "—"}
        </dd>
        <dt className="text-muted">Tổng tiền</dt>
        <dd className="text-right font-semibold tabular-nums">
          {formatVnd(data.TongTien)}
        </dd>
        {change !== null && (
          <>
            <dt className="text-muted">Tiền thối</dt>
            <dd className="text-right font-semibold tabular-nums">
              {formatVnd(change)}
            </dd>
          </>
        )}
      </dl>
      <div className="w-full text-left">
        <InvoicePreview invoice={data} onReprint={() => invoice.reload()} />
      </div>
      <Button size="pos" onClick={onFinish}>
        Về sơ đồ bàn
      </Button>
    </section>
  );
}
