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
  left: { DoanhThu: string; GiaVon: string; SoDon: number };
  right: { DoanhThu: string; GiaVon: string; SoDon: number };
  change_percent: string | null;
  change_cost_percent: string | null;
};

function signedVnd(difference: number): string {
  if (difference === 0) return formatVnd(0);
  const sign = difference > 0 ? "+" : "−";
  return `${sign}${formatVnd(Math.abs(difference))}`;
}

function ChangeBadge({
  changePercent,
  difference,
}: {
  changePercent: string | null;
  difference: number;
}) {
  if (changePercent === null)
    return (
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone="neutral">Không xác định tỷ lệ phần trăm</Badge>
        <span className="font-semibold tabular-nums">
          {signedVnd(difference)}
        </span>
      </div>
    );
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

function periodLabel(from: string, to: string): string {
  return from === to ? from : `${from} – ${to}`;
}

export function ComparisonReport() {
  const thisMonth = currentMonth();
  const lastMonth = previousMonth(thisMonth);
  const [leftFrom, setLeftFrom] = useState(lastMonth);
  const [leftTo, setLeftTo] = useState(lastMonth);
  const [rightFrom, setRightFrom] = useState(thisMonth);
  const [rightTo, setRightTo] = useState(thisMonth);
  const left = periodLabel(leftFrom, leftTo);
  const right = periodLabel(rightFrom, rightTo);
  const fetchComparison = useCallback(
    () =>
      apiFetch<ComparisonResponse>(
        "/reports/comparison" +
          `?left_from=${leftFrom}&left_to=${leftTo}` +
          `&right_from=${rightFrom}&right_to=${rightTo}`,
      ),
    [leftFrom, leftTo, rightFrom, rightTo],
  );
  const comparison = useResource(fetchComparison);

  const toolbar = (
    <div className="flex flex-wrap items-end gap-4">
      <div className="flex items-end gap-2">
        <MonthPicker
          value={leftFrom}
          onChange={setLeftFrom}
          label="Kỳ gốc từ"
        />
        <MonthPicker value={leftTo} onChange={setLeftTo} label="đến" />
      </div>
      <div className="flex items-end gap-2">
        <MonthPicker
          value={rightFrom}
          onChange={setRightFrom}
          label="Kỳ so sánh từ"
        />
        <MonthPicker value={rightTo} onChange={setRightTo} label="đến" />
      </div>
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
          <ChangeBadge
            changePercent={data.change_percent}
            difference={
              Number(data.right.DoanhThu) - Number(data.left.DoanhThu)
            }
          />
        </div>
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <StatCard
          label={`Giá vốn kỳ gốc (${left})`}
          value={formatVnd(data.left.GiaVon)}
        />
        <StatCard
          label={`Giá vốn kỳ so sánh (${right})`}
          value={formatVnd(data.right.GiaVon)}
        />
        <div className="grid gap-1.5 rounded-container border border-border bg-surface p-4">
          <span className="text-muted">Chênh lệch giá vốn</span>
          <ChangeBadge
            changePercent={data.change_cost_percent}
            difference={Number(data.right.GiaVon) - Number(data.left.GiaVon)}
          />
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
          headers={["Kỳ", "Doanh thu", "Giá vốn", "Số đơn"]}
          rows={[
            [
              left,
              formatVnd(data.left.DoanhThu),
              formatVnd(data.left.GiaVon),
              formatNumber(data.left.SoDon),
            ],
            [
              right,
              formatVnd(data.right.DoanhThu),
              formatVnd(data.right.GiaVon),
              formatNumber(data.right.SoDon),
            ],
          ]}
          pageSize={10}
        />
      </section>
    </div>
  );
}
