"use client";

import { UtensilsCrossed } from "lucide-react";
import { useCallback, useState } from "react";

import { EmptyState, ErrorState, LoadingState } from "@/components/page-states";
import { Bars } from "@/features/reports/chart";
import { GranularityPicker } from "@/features/reports/period-picker";
import { ReportTable } from "@/features/reports/report-table";
import { apiFetch } from "@/lib/api-client";
import { formatNumber, formatVnd } from "@/lib/format";
import { useResource } from "@/lib/use-resource";
import { cn } from "@/lib/utils";

type DishRank = {
  MaMon: number;
  TenMon: string;
  SoLuong: number;
  DoanhThu: string;
};

type DishRankResponse = { items: DishRank[] };

const ORDER_BY_OPTIONS = [
  { value: "quantity", label: "Số lượng" },
  { value: "revenue", label: "Doanh thu" },
];

function metric(dish: DishRank, orderBy: string): number {
  return orderBy === "revenue" ? Number(dish.DoanhThu) : dish.SoLuong;
}

export function DishRanking() {
  const [granularity, setGranularity] = useState("month");
  const [orderBy, setOrderBy] = useState("quantity");
  const fetchRanking = useCallback(
    () =>
      apiFetch<DishRankResponse>(
        `/reports/dishes?granularity=${granularity}&order_by=${orderBy}`,
      ),
    [granularity, orderBy],
  );
  const ranking = useResource(fetchRanking);

  const orderPicker = (
    <div
      role="group"
      aria-label="Xếp hạng theo"
      className="inline-flex gap-0.5 rounded-control border border-border-strong bg-surface p-[3px]"
    >
      {ORDER_BY_OPTIONS.map((option) => (
        <button
          key={option.value}
          type="button"
          aria-pressed={orderBy === option.value}
          onClick={() => setOrderBy(option.value)}
          className={cn(
            "h-8 rounded-badge px-3 font-semibold transition-colors",
            orderBy === option.value
              ? "bg-primary text-white"
              : "text-muted hover:text-ink",
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  );

  const toolbar = (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <GranularityPicker value={granularity} onChange={setGranularity} />
      {orderPicker}
    </div>
  );

  if (ranking.status === "loading")
    return (
      <div className="space-y-4">
        {toolbar}
        <LoadingState />
      </div>
    );
  if (ranking.status === "error")
    return (
      <div className="space-y-4">
        {toolbar}
        <ErrorState message={ranking.message} onRetry={ranking.reload} />
      </div>
    );

  const items = ranking.data.items;
  if (items.length === 0)
    return (
      <div className="space-y-4">
        {toolbar}
        <EmptyState
          icon={UtensilsCrossed}
          title="Chưa có món nào được bán trong kỳ"
          description="Chọn kỳ dài hơn để xem xếp hạng món ăn."
        />
      </div>
    );

  const metricLabel = orderBy === "revenue" ? "doanh thu" : "số lượng";
  const top = items.slice(0, 10);
  const least = [...items].slice(-10).reverse();

  const chartItems = (dishes: DishRank[]) =>
    dishes.map((dish) => ({
      key: dish.MaMon,
      label:
        dish.TenMon.length > 10 ? `${dish.TenMon.slice(0, 9)}…` : dish.TenMon,
      value: metric(dish, orderBy),
    }));

  const tickFormat = (v: number) =>
    orderBy === "revenue"
      ? `${formatNumber(v / 1_000_000)}tr`
      : formatNumber(v);
  const tooltipFormat =
    (dishes: DishRank[]) =>
    (item: { key: string | number; label: string; value: number }) => {
      const dish = dishes.find((d) => d.MaMon === item.key);
      return `${dish?.TenMon ?? item.label}: ${orderBy === "revenue" ? formatVnd(item.value) : formatNumber(item.value)}`;
    };

  return (
    <div className="space-y-4">
      {toolbar}
      <div className="grid gap-3 xl:grid-cols-2">
        <section className="space-y-3 rounded-container border border-border bg-surface p-4">
          <h2 className="text-[15px] font-bold">
            Bán chạy nhất theo {metricLabel}
          </h2>
          <Bars
            items={chartItems(top)}
            ariaLabel={`Biểu đồ món bán chạy nhất theo ${metricLabel}`}
            tickFormat={tickFormat}
            tooltipFormat={tooltipFormat(top)}
          />
        </section>
        <section className="space-y-3 rounded-container border border-border bg-surface p-4">
          <h2 className="text-[15px] font-bold">
            Bán chậm nhất theo {metricLabel}
          </h2>
          <Bars
            items={chartItems(least)}
            ariaLabel={`Biểu đồ món bán chậm nhất theo ${metricLabel}`}
            tickFormat={tickFormat}
            tooltipFormat={tooltipFormat(least)}
            colorAt={() => "var(--color-chart-5)"}
          />
        </section>
      </div>
      <section className="space-y-3">
        <h2 className="text-[15px] font-bold">Chi tiết xếp hạng</h2>
        <ReportTable
          headers={["Món", "Số lượng", "Doanh thu"]}
          rows={items.map((dish) => [
            dish.TenMon,
            formatNumber(dish.SoLuong),
            formatVnd(dish.DoanhThu),
          ])}
          pageSize={10}
          searchLabel="Tìm món"
          searchColumn={0}
        />
      </section>
    </div>
  );
}
