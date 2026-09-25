"use client";

import { Ban } from "lucide-react";
import { useCallback, useState } from "react";

import {
  EmptyState,
  ErrorState,
  LoadingState,
  StatCard,
} from "@/components/page-states";
import { Bars } from "@/features/reports/chart";
import { currentMonth, MonthPicker } from "@/features/reports/period-picker";
import { ReportTable } from "@/features/reports/report-table";
import { apiFetch } from "@/lib/api-client";
import { formatNumber, formatVnd } from "@/lib/format";
import { useResource } from "@/lib/use-resource";

type CancelledOrder = {
  MaOrder: number;
  MaOrderHienThi: string | null;
  TongTien: string;
  LyDoHuy: string | null;
};

type CancelledResponse = {
  SoLuong: number;
  TongGiaTri: string;
  items: CancelledOrder[];
};

const NO_REASON = "Không ghi lý do";

function byReason(
  items: CancelledOrder[],
): { reason: string; count: number; total: number }[] {
  const groups = new Map<string, { count: number; total: number }>();
  for (const item of items) {
    const reason = item.LyDoHuy?.trim() || NO_REASON;
    const group = groups.get(reason) ?? { count: 0, total: 0 };
    group.count += 1;
    group.total += Number(item.TongTien);
    groups.set(reason, group);
  }
  return [...groups.entries()]
    .map(([reason, group]) => ({ reason, ...group }))
    .sort((a, b) => b.count - a.count);
}

export function CancelledReport() {
  const [month, setMonth] = useState(currentMonth);
  const fetchCancelled = useCallback(
    () =>
      apiFetch<CancelledResponse>(`/reports/cancelled-orders?month=${month}`),
    [month],
  );
  const cancelled = useResource(fetchCancelled);

  const toolbar = <MonthPicker value={month} onChange={setMonth} />;

  if (cancelled.status === "loading")
    return (
      <div className="space-y-4">
        {toolbar}
        <LoadingState />
      </div>
    );
  if (cancelled.status === "error")
    return (
      <div className="space-y-4">
        {toolbar}
        <ErrorState message={cancelled.message} onRetry={cancelled.reload} />
      </div>
    );

  const data = cancelled.data;

  return (
    <div className="space-y-4">
      {toolbar}
      <div className="grid gap-3 sm:grid-cols-2">
        <StatCard label="Số order bị hủy" value={formatNumber(data.SoLuong)} />
        <StatCard
          label="Tổng giá trị order hủy"
          value={formatVnd(data.TongGiaTri)}
        />
      </div>

      {data.items.length === 0 ? (
        <EmptyState
          icon={Ban}
          title="Không có order nào bị hủy trong tháng"
          description="Chọn tháng khác để xem lại."
        />
      ) : (
        <>
          {(() => {
            const reasons = byReason(data.items);
            return (
              <section className="space-y-3 rounded-container border border-border bg-surface p-4">
                <h2 className="text-[15px] font-semibold">Lý do hủy</h2>
                <Bars
                  items={reasons.map((r) => ({
                    key: r.reason,
                    label: r.reason,
                    value: r.count,
                  }))}
                  ariaLabel="Biểu đồ số order hủy theo lý do"
                  tickFormat={(t) => formatNumber(t)}
                  tooltipFormat={(item) =>
                    `${item.label}: ${formatNumber(item.value)} order`
                  }
                  colorAt={(_, isPeak) =>
                    isPeak ? "var(--color-danger)" : "var(--color-chart-5)"
                  }
                />
                <ReportTable
                  headers={["Lý do", "Số order", "Giá trị"]}
                  rows={reasons.map((r) => [
                    r.reason,
                    formatNumber(r.count),
                    formatVnd(r.total),
                  ])}
                />
              </section>
            );
          })()}
          <section className="space-y-3">
            <h2 className="text-[15px] font-semibold">Danh sách order hủy</h2>
            <ReportTable
              headers={["Order", "Giá trị", "Lý do"]}
              rows={data.items.map((item) => [
                item.MaOrderHienThi ?? `#${item.MaOrder}`,
                formatVnd(item.TongTien),
                item.LyDoHuy?.trim() || NO_REASON,
              ])}
            />
          </section>
        </>
      )}
    </div>
  );
}
