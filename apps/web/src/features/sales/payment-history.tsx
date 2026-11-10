"use client";

import { useCallback } from "react";

import {
  ErrorState,
  LoadingState,
  StatusBadge,
} from "@/components/page-states";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { apiFetch } from "@/lib/api-client";
import { formatDateTime, formatVnd } from "@/lib/format";
import { useResource } from "@/lib/use-resource";

type Payment = {
  MaGiaoDich: number;
  PhuongThuc: string;
  TrangThai: string;
  SoTien: number;
  ThoiDiemTao: string | null;
  MaThamChieuNganHang: string | null;
  AnhChungTu: string | null;
};

/** FR-SALE-25: every payment attempt of the order, with its bank reference and outcome. */
export function PaymentHistory({ orderId }: { orderId: number }) {
  const load = useCallback(
    () => apiFetch<{ items: Payment[] }>(`/sales/orders/${orderId}/payments`),
    [orderId],
  );
  const payments = useResource(load);

  return (
    <section className="space-y-3 rounded-container border border-border bg-surface p-4">
      <h2 className="text-sm font-bold">Lịch sử thanh toán</h2>
      {payments.status === "loading" ? (
        <LoadingState rows={2} />
      ) : payments.status === "error" ? (
        <ErrorState message={payments.message} onRetry={payments.reload} />
      ) : payments.data.items.length === 0 ? (
        <p className="text-muted">Order chưa có giao dịch thanh toán nào.</p>
      ) : (
        <Table>
          <caption className="sr-only">Lịch sử thanh toán</caption>
          <TableHeader>
            <TableRow>
              <TableHead>Giao dịch</TableHead>
              <TableHead>Thời điểm</TableHead>
              <TableHead>Phương thức</TableHead>
              <TableHead className="text-right">Số tiền</TableHead>
              <TableHead>Mã tham chiếu ngân hàng</TableHead>
              <TableHead>Kết quả</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {payments.data.items.map((payment) => (
              <TableRow key={payment.MaGiaoDich}>
                <TableCell className="tabular-nums">
                  #{payment.MaGiaoDich}
                </TableCell>
                <TableCell className="tabular-nums">
                  {formatDateTime(payment.ThoiDiemTao)}
                </TableCell>
                <TableCell>{payment.PhuongThuc}</TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatVnd(payment.SoTien)}
                </TableCell>
                <TableCell>
                  {payment.MaThamChieuNganHang ?? "—"}
                  {payment.AnhChungTu ? " · có chứng từ" : ""}
                </TableCell>
                <TableCell>
                  <StatusBadge status={payment.TrangThai} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </section>
  );
}
