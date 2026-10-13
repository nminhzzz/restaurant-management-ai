"use client";

import { Hourglass } from "lucide-react";

import {
  EmptyState,
  ErrorState,
  LoadingState,
  StatCard,
} from "@/components/page-states";
import { ReportTable } from "@/features/reports/report-table";
import { apiFetch } from "@/lib/api-client";
import { formatDateTime, formatNumber, formatVnd } from "@/lib/format";
import { useResource } from "@/lib/use-resource";

type UnsettledOrder = {
  MaOrder: number;
  MaOrderHienThi: string | null;
  GiaTriOrder: string;
  ThoiDiemBatDauCho: string | null;
  SoPhutDaCho: number | null;
  KetQuaXuLyGanNhat: string | null;
};

type UnsettledResponse = {
  SoLuong: number;
  TongGiaTri: string;
  items: UnsettledOrder[];
};

const loadUnsettled = () => apiFetch<UnsettledResponse>("/reports/unsettled");

/** FR-REP-02: orders waiting for payment verification are listed apart from revenue. */
export function UnsettledReport() {
  const unsettled = useResource(loadUnsettled);

  if (unsettled.status === "loading") return <LoadingState />;
  if (unsettled.status === "error")
    return (
      <ErrorState message={unsettled.message} onRetry={unsettled.reload} />
    );

  const data = unsettled.data;
  return (
    <div className="space-y-4">
      <p className="text-muted">
        Các order đang chờ xác minh thanh toán. Chưa có hóa đơn nên chưa tính
        vào doanh thu.
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        <StatCard
          label="Order chờ xác minh"
          value={formatNumber(data.SoLuong)}
        />
        <StatCard label="Tổng giá trị" value={formatVnd(data.TongGiaTri)} />
      </div>
      {data.items.length === 0 ? (
        <EmptyState
          icon={Hourglass}
          title="Không có order nào chờ xác minh"
          description="Order chuyển khoản chưa khớp sẽ hiện ở đây."
        />
      ) : (
        <ReportTable
          headers={[
            "Order",
            "Giá trị",
            "Bắt đầu chờ",
            "Đã chờ",
            "Kết quả xử lý gần nhất",
          ]}
          rows={data.items.map((item) => [
            item.MaOrderHienThi ?? `#${item.MaOrder}`,
            formatVnd(item.GiaTriOrder),
            formatDateTime(item.ThoiDiemBatDauCho),
            item.SoPhutDaCho === null ? "" : `${item.SoPhutDaCho} phút`,
            item.KetQuaXuLyGanNhat ?? "",
          ])}
          pageSize={10}
        />
      )}
    </div>
  );
}
