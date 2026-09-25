"use client";

import { Clock } from "lucide-react";
import { useCallback, useState } from "react";

import { EmptyState, ErrorState, LoadingState } from "@/components/page-states";
import { Bars } from "@/features/reports/chart";
import { GranularityPicker } from "@/features/reports/period-picker";
import { ReportTable } from "@/features/reports/report-table";
import { apiFetch } from "@/lib/api-client";
import { formatNumber, formatVnd } from "@/lib/format";
import { useResource } from "@/lib/use-resource";

type HourBucket = { ThoiDiem: number; SoDon: number; DoanhThu: string };
type WeekdayBucket = { Thu: number; SoDon: number };
type HourlyResponse = { items: HourBucket[]; by_weekday: WeekdayBucket[] };

const WEEKDAY_LABELS: Record<number, string> = {
  1: "Thứ 2",
  2: "Thứ 3",
  3: "Thứ 4",
  4: "Thứ 5",
  5: "Thứ 6",
  6: "Thứ 7",
  7: "Chủ nhật",
};

/** Business Date runs 06:00 → 06:00, so the chart starts at 6h and wraps to 5h. */
function businessHourOrder(items: HourBucket[]): HourBucket[] {
  const byHour = new Map(items.map((item) => [item.ThoiDiem, item]));
  const hours = [
    ...Array.from({ length: 18 }, (_, i) => i + 6),
    ...Array.from({ length: 6 }, (_, i) => i),
  ];
  return hours.map(
    (hour) => byHour.get(hour) ?? { ThoiDiem: hour, SoDon: 0, DoanhThu: "0" },
  );
}

export function HourlyReport() {
  const [granularity, setGranularity] = useState("month");
  const fetchHourly = useCallback(
    () => apiFetch<HourlyResponse>(`/reports/hours?granularity=${granularity}`),
    [granularity],
  );
  const hourly = useResource(fetchHourly);

  const toolbar = (
    <GranularityPicker value={granularity} onChange={setGranularity} />
  );

  if (hourly.status === "loading")
    return (
      <div className="space-y-4">
        {toolbar}
        <LoadingState />
      </div>
    );
  if (hourly.status === "error")
    return (
      <div className="space-y-4">
        {toolbar}
        <ErrorState message={hourly.message} onRetry={hourly.reload} />
      </div>
    );

  const data = hourly.data;
  const hasOrders =
    data.items.some((item) => item.SoDon > 0) ||
    data.by_weekday.some((item) => item.SoDon > 0);

  if (!hasOrders)
    return (
      <div className="space-y-4">
        {toolbar}
        <EmptyState
          icon={Clock}
          title="Chưa có đơn nào trong kỳ"
          description="Chọn kỳ dài hơn để xem phân bố theo khung giờ."
        />
      </div>
    );

  const hours = businessHourOrder(data.items);
  const hourItems = hours.map((item) => ({
    key: item.ThoiDiem,
    label: `${item.ThoiDiem}h`,
    value: item.SoDon,
  }));

  const weekdays = [...data.by_weekday].sort((a, b) => a.Thu - b.Thu);
  const weekdayItems = weekdays.map((item) => ({
    key: item.Thu,
    label: WEEKDAY_LABELS[item.Thu] ?? String(item.Thu),
    value: item.SoDon,
  }));

  return (
    <div className="space-y-4">
      {toolbar}
      <div className="grid gap-3 xl:grid-cols-2">
        <section className="space-y-3 rounded-container border border-border bg-surface p-4">
          <h2 className="text-[15px] font-semibold">Số đơn theo khung giờ</h2>
          <Bars
            items={hourItems}
            ariaLabel="Biểu đồ số đơn theo khung giờ trong ngày, từ 6 giờ tới 5 giờ hôm sau"
            tickFormat={(t) => formatNumber(t)}
            tooltipFormat={(item) =>
              `${item.label}: ${formatNumber(item.value)} đơn`
            }
          />
        </section>
        <section className="space-y-3 rounded-container border border-border bg-surface p-4">
          <h2 className="text-[15px] font-semibold">
            Số đơn theo ngày trong tuần
          </h2>
          <Bars
            items={weekdayItems}
            ariaLabel="Biểu đồ số đơn theo ngày trong tuần"
            tickFormat={(t) => formatNumber(t)}
            tooltipFormat={(item) =>
              `${item.label}: ${formatNumber(item.value)} đơn`
            }
          />
        </section>
      </div>
      <section className="space-y-3">
        <h2 className="text-[15px] font-semibold">Chi tiết theo khung giờ</h2>
        <ReportTable
          headers={["Khung giờ", "Số đơn", "Doanh thu"]}
          rows={hours.map((item) => [
            `${item.ThoiDiem}h`,
            formatNumber(item.SoDon),
            formatVnd(item.DoanhThu),
          ])}
        />
      </section>
    </div>
  );
}
