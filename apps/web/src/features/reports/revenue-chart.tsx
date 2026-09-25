"use client";

import { ChartColumn } from "lucide-react";
import { useCallback, useState } from "react";

import {
  EmptyState,
  ErrorState,
  LoadingState,
  StatCard,
} from "@/components/page-states";
import { Badge } from "@/components/ui/badge";
import { Bars } from "@/features/reports/chart";
import { GranularityPicker } from "@/features/reports/period-picker";
import { ReportTable } from "@/features/reports/report-table";
import { TopDishes } from "@/features/reports/top-dishes";
import { apiFetch } from "@/lib/api-client";
import { formatDate, formatNumber, formatVnd } from "@/lib/format";
import { useResource } from "@/lib/use-resource";
import { cn } from "@/lib/utils";

type RevenueBucket = {
  key: string | number | null;
  DoanhThu: string;
  SoDon: number;
};

type RevenueResponse = {
  total: string;
  provisional: string;
  SoDon: number;
  items: RevenueBucket[];
  period?: { start: string; end: string; granularity: string };
};

const GROUP_BY_OPTIONS = [
  { value: "period", label: "Mốc thời gian" },
  { value: "table", label: "Bàn" },
  { value: "payment_method", label: "Phương thức thanh toán" },
];

/** `2026-09-10` → `10/09`; other bucket keys (month, week number) print as they are. */
function bucketLabel(key: string | number | null, groupBy: string): string {
  if (groupBy === "table") return key === null ? "Không có bàn" : `Bàn ${key}`;
  const text = String(key ?? "");
  if (groupBy === "payment_method") return text;
  const match = /^\d{4}-(\d{2})-(\d{2})$/.exec(text);
  return match ? `${match[2]}/${match[1]}` : text;
}

export function RevenueChart() {
  const [granularity, setGranularity] = useState("month");
  const [groupBy, setGroupBy] = useState("period");
  const fetchRevenue = useCallback(
    () =>
      apiFetch<RevenueResponse>(
        `/reports/revenue?granularity=${granularity}&group_by=${groupBy}`,
      ),
    [granularity, groupBy],
  );
  const revenue = useResource(fetchRevenue);

  const picker = (
    <GranularityPicker value={granularity} onChange={setGranularity} />
  );

  const groupPicker = (
    <div
      role="group"
      aria-label="Nhóm theo"
      className="inline-flex gap-0.5 rounded-control bg-surface-sunken p-[3px]"
    >
      {GROUP_BY_OPTIONS.map((option) => (
        <button
          key={option.value}
          type="button"
          aria-pressed={groupBy === option.value}
          onClick={() => setGroupBy(option.value)}
          className={cn(
            "h-8 rounded-md px-3 font-medium transition-colors",
            groupBy === option.value
              ? "bg-surface text-ink shadow-sm shadow-ink/10"
              : "text-muted hover:text-ink",
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  );

  if (revenue.status === "loading")
    return (
      <div className="space-y-4">
        {picker}
        <LoadingState />
      </div>
    );
  if (revenue.status === "error")
    return (
      <div className="space-y-4">
        {picker}
        <ErrorState message={revenue.message} onRetry={revenue.reload} />
      </div>
    );

  const data = revenue.data;
  const provisional = Number(data.provisional);
  const average = data.SoDon > 0 ? Number(data.total) / data.SoDon : 0;
  const chartItems = data.items.map((item) => ({
    key: item.key ?? "",
    label: bucketLabel(item.key, groupBy),
    value: Number(item.DoanhThu) || 0,
  }));
  const peak = Math.max(...chartItems.map((item) => item.value), 0);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        {picker}
        {data.period ? (
          <p className="text-muted tabular-nums">
            {formatDate(data.period.start)} đến {formatDate(data.period.end)}
          </p>
        ) : null}
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Doanh thu"
          value={formatVnd(data.total)}
          badge={
            provisional > 0 ? (
              <Badge tone="warning">Chưa chốt</Badge>
            ) : undefined
          }
          hint={
            provisional > 0
              ? `Trong đó ${formatVnd(provisional)} là số tạm tính, đang chờ đối soát.`
              : "Đã đối soát đầy đủ"
          }
        />
        <StatCard label="Số đơn" value={formatNumber(data.SoDon ?? 0)} />
        <StatCard
          label="Trung bình mỗi đơn"
          value={formatVnd(Math.round(average))}
        />
        <StatCard
          label="Số mốc có doanh thu"
          value={formatNumber(
            data.items.filter((i) => Number(i.DoanhThu) > 0).length,
          )}
          hint={`Trên ${data.items.length} mốc trong kỳ`}
        />
      </div>

      {data.items.length === 0 ? (
        <EmptyState
          icon={ChartColumn}
          title="Chưa có dữ liệu trong kỳ"
          description="Chọn kỳ dài hơn, hoặc kiểm tra xem đã có hóa đơn nào được thanh toán chưa."
        />
      ) : (
        <div className="grid gap-3 xl:grid-cols-[minmax(0,1.7fr)_minmax(0,1fr)]">
          <section className="space-y-3 rounded-container border border-border bg-surface p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-[15px] font-semibold">Doanh thu theo</h2>
              {groupPicker}
            </div>
            <Bars
              items={chartItems}
              ariaLabel={`Biểu đồ doanh thu theo ${GROUP_BY_OPTIONS.find((o) => o.value === groupBy)?.label.toLowerCase()}, cao nhất ${formatVnd(peak)}`}
              tickFormat={(t) => `${formatNumber(t / 1_000_000)}tr`}
              tooltipFormat={(item) =>
                `${item.label}: ${formatVnd(item.value)}`
              }
            />
          </section>
          <TopDishes granularity={granularity} />
          <section className="space-y-3 xl:col-span-2">
            <h2 className="text-[15px] font-semibold">Chi tiết</h2>
            <ReportTable
              headers={["Mốc", "Số đơn", "Doanh thu"]}
              rows={data.items.map((item) => [
                bucketLabel(item.key, groupBy),
                formatNumber(item.SoDon),
                formatVnd(item.DoanhThu),
              ])}
              pageSize={10}
            />
          </section>
        </div>
      )}
    </div>
  );
}
