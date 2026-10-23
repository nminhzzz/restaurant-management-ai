"use client";

import { Wallet } from "lucide-react";
import { useCallback } from "react";

import {
  EmptyState,
  ErrorState,
  LoadingState,
  StatCard,
} from "@/components/page-states";
import { Bars } from "@/features/reports/chart";
import { ReportTable } from "@/features/reports/report-table";
import { apiFetch } from "@/lib/api-client";
import { formatDateTime, formatNumber, formatVnd } from "@/lib/format";
import { useResource } from "@/lib/use-resource";

type ClosedUnpaidOrder = {
  MaOrder: number;
  MaOrderHienThi: string | null;
  TongTien: string;
  GiaVon: string;
  LyDo: string | null;
  NguoiDong: string | null;
  ThoiDiemDong: string | null;
};

type ClosedUnpaidResponse = {
  SoLuong: number;
  TongGiaTri: string;
  TongGiaVon: string;
  items: ClosedUnpaidOrder[];
};

/** FR-REP-10: orders closed without money, kept apart from cancelled orders. */
export function ClosedUnpaidPanel({
  granularity,
  anchor,
}: {
  granularity: string;
  anchor: string;
}) {
  const fetcher = useCallback(
    () =>
      apiFetch<ClosedUnpaidResponse>(
        `/reports/closed-unpaid?granularity=${granularity}&anchor=${anchor}`,
      ),
    [granularity, anchor],
  );
  const resource = useResource(fetcher);

  if (resource.status === "loading") return <LoadingState rows={2} />;
  if (resource.status === "error")
    return <ErrorState message={resource.message} onRetry={resource.reload} />;

  const data = resource.data;
  if (data.SoLuong === 0) {
    return (
      <EmptyState
        icon={Wallet}
        title="Không có order đóng chưa thu tiền trong kỳ"
        description="Order chỉ vào đây khi quản lý đóng sau khi không thu được tiền."
      />
    );
  }

  return (
    <section className="space-y-3">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-[15px] font-bold">Đóng – chưa thu được tiền</h2>
        <p className="text-sm text-muted">
          {formatNumber(data.SoLuong)} order · giá vốn{" "}
          {formatVnd(data.TongGiaVon)}
        </p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <StatCard label="Số order" value={formatNumber(data.SoLuong)} />
        <StatCard
          label="Tiền chưa thu"
          value={formatVnd(data.TongGiaTri)}
          hint="Không cộng vào doanh thu"
        />
      </div>
      <ReportTable
        headers={[
          "Order",
          "Tiền chưa thu",
          "Giá vốn",
          "Lý do",
          "Người đóng",
          "Thời điểm đóng",
        ]}
        rows={data.items.map((item) => [
          item.MaOrderHienThi ?? `#${item.MaOrder}`,
          formatVnd(item.TongTien),
          formatVnd(item.GiaVon),
          item.LyDo ?? "Không ghi lý do",
          item.NguoiDong ?? "Không xác định",
          formatDateTime(item.ThoiDiemDong),
        ])}
        pageSize={10}
      />
    </section>
  );
}
