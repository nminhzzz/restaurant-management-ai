"use client";

import { useCallback } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api-client";
import { formatNumber } from "@/lib/format";
import { useResource } from "@/lib/use-resource";

type DishRank = { MaMon: number; TenMon: string; SoLuong: number };

export function TopDishes({ granularity }: { granularity: string }) {
  const fetchRanking = useCallback(
    () =>
      apiFetch<{ items?: DishRank[] }>(
        `/reports/dishes?granularity=${granularity}&order_by=quantity`,
      ).then((d) =>
        (d.items ?? [])
          .filter((item) => typeof item.TenMon === "string")
          .slice(0, 5),
      ),
    [granularity],
  );
  const ranking = useResource(fetchRanking);

  return (
    <section className="space-y-3 rounded-container border border-border bg-surface p-4">
      <div className="flex items-baseline justify-between">
        <h2 className="text-[15px] font-semibold">Món bán chạy</h2>
        <span className="text-xs text-subtle">Số phần</span>
      </div>
      {ranking.status === "loading" ? (
        <div className="space-y-3" role="status">
          <span className="sr-only">Đang tải món bán chạy</span>
          {Array.from({ length: 5 }, (_, i) => (
            <Skeleton key={i} className="h-7" />
          ))}
        </div>
      ) : ranking.status === "error" ? (
        <p className="text-danger-fg">{ranking.message}</p>
      ) : ranking.data.length === 0 ? (
        <p className="text-muted">Chưa có món nào được bán trong kỳ.</p>
      ) : (
        <ol className="space-y-3">
          {ranking.data.map((dish, index) => (
            <li
              key={dish.MaMon}
              className="grid grid-cols-[20px_minmax(0,1fr)_auto] items-center gap-x-2.5 gap-y-1"
            >
              <span className="text-xs text-subtle tabular-nums">
                {index + 1}
              </span>
              <span className="truncate">{dish.TenMon}</span>
              <span className="font-medium tabular-nums">
                {formatNumber(dish.SoLuong)}
              </span>
              <span
                aria-hidden
                className="col-start-2 col-end-4 h-1.5 rounded-full bg-chart-1/85"
                style={{
                  width: `${(dish.SoLuong / Math.max(ranking.data[0].SoLuong, 1)) * 100}%`,
                }}
              />
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
