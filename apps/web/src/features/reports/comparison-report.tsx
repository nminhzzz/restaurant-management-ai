"use client";

import { Minus, TrendingDown, TrendingUp } from "lucide-react";
import { useCallback, useState } from "react";

import { ErrorState, LoadingState, StatCard } from "@/components/page-states";
import { Badge } from "@/components/ui/badge";
import { Bars } from "@/features/reports/chart";
import {
  currentMonth,
  MonthPicker,
  previousMonth,
} from "@/features/reports/period-picker";
import { ReportTable } from "@/features/reports/report-table";
import { apiFetch } from "@/lib/api-client";
import { formatNumber, formatVnd } from "@/lib/format";
import { useResource } from "@/lib/use-resource";

type ComparisonResponse = {
  left: { DoanhThu: string; SoDon: number };
  right: { DoanhThu: string; SoDon: number };
  change_percent: string | null;
};

function ChangeBadge({ changePercent }: { changePercent: string | null }) {
  if (changePercent === null)
    return <Badge tone="neutral">Không có kỳ gốc để so sánh</Badge>;
  const value = Number(changePercent);
  if (value > 0)
    return (
      <Badge tone="success">
        <TrendingUp className="mr-1 size-3.5" aria-hidden />
        Tăng {formatNumber(value)}%
      </Badge>
    );
  if (value < 0)
    return (
      <Badge tone="danger">
        <TrendingDown className="mr-1 size-3.5" aria-hidden />
        Giảm {formatNumber(Math.abs(value))}%
      </Badge>
    );
  return (
    <Badge tone="neutral">
      <Minus className="mr-1 size-3.5" aria-hidden />
      Không đổi
    </Badge>
  );
}

export function ComparisonReport() {
  const [right, setRight] = useState(currentMonth);
  const [left, setLeft] = useState(() => previousMonth(currentMonth()));
  const fetchComparison = useCallback(
    () =>
      apiFetch<ComparisonResponse>(
        `/reports/comparison?left=${left}&right=${right}`,
      ),
    [left, right],
  );
  const comparison = useResource(fetchComparison);

  const toolbar = (
    <div className="flex flex-wrap items-end gap-4">
      <MonthPicker value={left} onChange={setLeft} label="Kỳ gốc" />
      <MonthPicker value={right} onChange={setRight} label="Kỳ so sánh" />
    </div>
  );

  if (comparison.status === "loading")
    return (
      <div className="space-y-4">
        {toolbar}
        <LoadingState />
      </div>
    );
  if (comparison.status === "error")
    return (
      <div className="space-y-4">
        {toolbar}
        <ErrorState message={comparison.message} onRetry={comparison.reload} />
      </div>
    );

  const data = comparison.data;
  const chartItems = [
    { key: "left", label: left, value: Number(data.left.DoanhThu) },
    { key: "right", label: right, value: Number(data.right.DoanhThu) },
  ];

  return (
    <div className="space-y-4">
      {toolbar}
      <div className="grid gap-3 sm:grid-cols-3">
        <StatCard
          label={`Doanh thu kỳ gốc (${left})`}
          value={formatVnd(data.left.DoanhThu)}
        />
        <StatCard
          label={`Doanh thu kỳ so sánh (${right})`}
          value={formatVnd(data.right.DoanhThu)}
        />
        <div className="grid gap-1.5 rounded-container border border-border bg-surface p-4">
          <span className="text-muted">Chênh lệch doanh thu</span>
          <ChangeBadge changePercent={data.change_percent} />
        </div>
      </div>
      <section className="space-y-3 rounded-container border border-border bg-surface p-4">
        <h2 className="text-[15px] font-bold">Doanh thu hai kỳ</h2>
        <Bars
          items={chartItems}
          ariaLabel={`Biểu đồ so sánh doanh thu kỳ ${left} và kỳ ${right}`}
          tickFormat={(t) => `${formatNumber(t / 1_000_000)}tr`}
          tooltipFormat={(item) => `${item.label}: ${formatVnd(item.value)}`}
          colorAt={(index) =>
            index === 0 ? "var(--color-chart-2)" : "var(--color-chart-1)"
          }
        />
      </section>
      <section className="space-y-3">
        <h2 className="text-[15px] font-bold">Chi tiết</h2>
        <ReportTable
          headers={["Kỳ", "Doanh thu", "Số đơn"]}
          rows={[
            [
              left,
              formatVnd(data.left.DoanhThu),
              formatNumber(data.left.SoDon),
            ],
            [
              right,
              formatVnd(data.right.DoanhThu),
              formatNumber(data.right.SoDon),
            ],
          ]}
          pageSize={10}
        />
      </section>
    </div>
  );
}
