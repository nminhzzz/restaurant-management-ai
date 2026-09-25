"use client";

import { useEffect, useState } from "react";

import { ReportTable } from "@/features/reports/report-table";
import { apiFetch } from "@/lib/api-client";

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
  period: { start: string; end: string; granularity: string };
};

const GRANULARITIES = [
  { value: "day", label: "Ngày" },
  { value: "week", label: "Tuần" },
  { value: "month", label: "Tháng" },
  { value: "year", label: "Năm" },
];

function vnd(value: string | number): string {
  const amount = Number(value);
  return Number.isFinite(amount)
    ? `${amount.toLocaleString("vi-VN")}đ`
    : String(value);
}

export function RevenueChart() {
  const [data, setData] = useState<RevenueResponse | null>(null);
  const [granularity, setGranularity] = useState("month");

  useEffect(() => {
    apiFetch<RevenueResponse>(`/reports/revenue?granularity=${granularity}`)
      .then(setData)
      .catch(() => setData(null));
  }, [granularity]);

  if (data === null) return <p>Đang tải…</p>;

  const peak = Math.max(...data.items.map((item) => Number(item.DoanhThu)), 0);

  return (
    <section className="space-y-3">
      <div className="flex flex-wrap items-end gap-3">
        <label className="text-sm">
          Kỳ báo cáo
          <select
            aria-label="Kỳ báo cáo"
            className="mt-1 block min-h-11 rounded border px-3 py-2"
            value={granularity}
            onChange={(event) => setGranularity(event.target.value)}
          >
            {GRANULARITIES.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <p>
          Tổng doanh thu: <strong>{vnd(data.total)}</strong> · {data.SoDon} đơn
        </p>
      </div>

      {Number(data.provisional) > 0 && (
        <p className="text-sm text-amber-700">
          Số liệu tạm tính: {vnd(data.provisional)} đang chờ đối soát, chưa phải
          số chốt.
        </p>
      )}

      {data.items.length === 0 ? (
        <p>Chưa có dữ liệu trong kỳ</p>
      ) : (
        <>
          <ReportTable
            headers={["Mốc", "Số đơn", "Doanh thu"]}
            rows={data.items.map((item) => [
              String(item.key ?? ""),
              item.SoDon,
              vnd(item.DoanhThu),
            ])}
          />
          <svg
            role="img"
            aria-label="Biểu đồ doanh thu"
            viewBox={`0 0 ${data.items.length * 40} 120`}
            className="h-40 w-full"
          >
            {data.items.map((item, index) => {
              const height =
                peak > 0 ? (Number(item.DoanhThu) / peak) * 100 : 0;
              return (
                <rect
                  key={String(item.key ?? index)}
                  x={index * 40 + 8}
                  y={110 - height}
                  width={24}
                  height={Math.max(height, 1)}
                  className="fill-amber-500"
                />
              );
            })}
          </svg>
        </>
      )}
    </section>
  );
}
