"use client";

import { Printer } from "lucide-react";
import { useCallback } from "react";

import { ErrorState, LoadingState } from "@/components/page-states";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { apiFetch } from "@/lib/api-client";
import { formatDateTime, formatVnd } from "@/lib/format";
import { useResource } from "@/lib/use-resource";

import type { ProvisionalBill } from "./types";

function BillBody({ orderId }: { orderId: number }) {
  const fetcher = useCallback(
    () =>
      apiFetch<ProvisionalBill>(`/sales/orders/${orderId}/provisional-bill`),
    [orderId],
  );
  const bill = useResource(fetcher);

  if (bill.status === "loading") return <LoadingState rows={3} />;
  if (bill.status === "error")
    return <ErrorState message={bill.message} onRetry={bill.reload} />;

  const data = bill.data;
  return (
    <div className="space-y-3">
      <div
        id="provisional-bill-print-area"
        className="space-y-3 rounded-control border border-border bg-canvas p-4 print:border-0 print:bg-white print:p-0"
      >
        <div className="text-center">
          <p className="font-semibold">{data.TenNhaHang ?? "Nhà hàng"}</p>
          {data.DiaChi && <p className="text-xs text-muted">{data.DiaChi}</p>}
          <p className="mt-1 font-bold">{data.TieuDe}</p>
          <p className="text-xs text-subtle">
            {data.MaOrderHienThi}
            {data.TenBan ? ` · ${data.TenBan}` : ""} ·{" "}
            {formatDateTime(data.ThoiDiemIn)}
          </p>
        </div>
        <ul className="divide-y divide-border">
          {data.lines.map((line, index) => (
            <li
              key={`${line.MaMon}-${index}`}
              className="flex justify-between gap-2 py-1.5 text-sm"
            >
              <span>
                {line.TenMon} × {line.SoLuong}
              </span>
              <span className="tabular-nums">{formatVnd(line.ThanhTien)}</span>
            </li>
          ))}
        </ul>
        <div className="flex justify-between border-t border-border pt-2 font-semibold">
          <span>Tổng tạm tính</span>
          <span className="tabular-nums">{formatVnd(data.TongTien)}</span>
        </div>
      </div>
      <Button size="sm" onClick={() => window.print()}>
        <Printer />
        In phiếu tạm tính
      </Button>
    </div>
  );
}

/** FR-SALE-21: the guests check the bill before paying; creates no invoice. */
export function ProvisionalBillDialog({
  orderId,
  open,
  onOpenChange,
}: {
  orderId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-[min(28rem,calc(100vw-2rem))]">
        <DialogHeader>
          <DialogTitle>Phiếu tạm tính</DialogTitle>
        </DialogHeader>
        {open && <BillBody orderId={orderId} />}
      </DialogContent>
    </Dialog>
  );
}
