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
  today,
} from "@/features/reports/period-picker";
import { ReportTable } from "@/features/reports/report-table";
import { apiFetch } from "@/lib/api-client";
import { formatNumber, formatVnd } from "@/lib/format";
import { useResource } from "@/lib/use-resource";

type Figures = { DoanhThu: string; SoDon: number; GiaVon: string };

type Change = {
  ChenhLechTuyetDoi: string;
  PhanTramChenhLech: string | null;
  GhiChu?: string | null;
};

type ComparisonResponse = {
  left: Figures;
  right: Figures;
  doanh_thu: Change;
  chi_phi: Change;
};

/** A month (`2026-09`) or an inclusive range of Business Dates (`from..to`). */
type PeriodChoice = {
  kind: "month" | "range";
  month: string;
  from: string;
  to: string;
};

function toParam(choice: PeriodChoice): string {
  return choice.kind === "month"
    ? choice.month
    : `${choice.from}..${choice.to}`;
}

function isComplete(choice: PeriodChoice): boolean {
  return (
    choice.kind === "month" ||
    (choice.from !== "" && choice.to !== "" && choice.from <= choice.to)
  );
}

function ChangeBadge({ change }: { change: Change }) {
  if (change.PhanTramChenhLech === null)
    return (
      <Badge tone="neutral">
        {change.GhiChu ?? "Không xác định tỷ lệ phần trăm"}
      </Badge>
    );
  const value = Number(change.PhanTramChenhLech);
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

function ChangeCard({ label, change }: { label: string; change: Change }) {
  return (
    <div className="grid gap-1.5 rounded-container border border-border bg-surface p-4">
      <span className="text-muted">{label}</span>
      <ChangeBadge change={change} />
      <span className="text-xs text-muted tabular-nums">
        Chênh lệch tuyệt đối: {formatVnd(change.ChenhLechTuyetDoi)}
      </span>
    </div>
  );
}

function PeriodInput({
  label,
  value,
  onChange,
}: {
  label: string;
  value: PeriodChoice;
  onChange: (value: PeriodChoice) => void;
}) {
  return (
    <fieldset className="flex flex-wrap items-end gap-2">
      <legend className="sr-only">{label}</legend>
      <label className="grid gap-1 text-xs text-subtle">
        <span>{label}</span>
        <select
          aria-label={`${label}: kiểu kỳ`}
          value={value.kind}
          onChange={(e) =>
            onChange({ ...value, kind: e.target.value as PeriodChoice["kind"] })
          }
          className="h-9 rounded-control border border-border-strong bg-surface px-3 text-sm text-ink"
        >
          <option value="month">Tháng</option>
          <option value="range">Khoảng ngày</option>
        </select>
      </label>
      {value.kind === "month" ? (
        <MonthPicker
          value={value.month}
          onChange={(month) => onChange({ ...value, month })}
          label="Tháng"
        />
      ) : (
        <>
          <label className="grid gap-1 text-xs text-subtle">
            <span>{label}: từ ngày</span>
            <input
              type="date"
              value={value.from}
              onChange={(e) => onChange({ ...value, from: e.target.value })}
              className="h-9 rounded-control border border-border-strong bg-surface px-3 text-sm text-ink"
            />
          </label>
          <label className="grid gap-1 text-xs text-subtle">
            <span>{label}: đến ngày</span>
            <input
              type="date"
              value={value.to}
              onChange={(e) => onChange({ ...value, to: e.target.value })}
              className="h-9 rounded-control border border-border-strong bg-surface px-3 text-sm text-ink"
            />
          </label>
        </>
      )}
    </fieldset>
  );
}

export function ComparisonReport() {
  const [right, setRight] = useState<PeriodChoice>(() => ({
    kind: "month",
    month: currentMonth(),
    from: today(),
    to: today(),
  }));
  const [left, setLeft] = useState<PeriodChoice>(() => ({
    kind: "month",
    month: previousMonth(currentMonth()),
    from: today(),
    to: today(),
  }));
  const leftParam = toParam(left);
  const rightParam = toParam(right);
  const ready = isComplete(left) && isComplete(right);
  const fetchComparison = useCallback(
    () =>
      ready
        ? apiFetch<ComparisonResponse>(
            `/reports/comparison?left=${encodeURIComponent(leftParam)}&right=${encodeURIComponent(rightParam)}`,
          )
        : Promise.reject(
            new Error("Chọn đủ ngày bắt đầu và kết thúc cho khoảng ngày."),
          ),
    [ready, leftParam, rightParam],
  );
  const comparison = useResource(fetchComparison);

  const toolbar = (
    <div className="flex flex-wrap items-end gap-4">
      <PeriodInput label="Kỳ gốc" value={left} onChange={setLeft} />
      <PeriodInput label="Kỳ so sánh" value={right} onChange={setRight} />
    </div>
  );

  if (!ready)
    return (
      <div className="space-y-4">
        {toolbar}
        <p role="alert" className="text-danger-fg">
          Chọn đủ ngày bắt đầu và kết thúc (ngày bắt đầu không sau ngày kết
          thúc) cho khoảng ngày.
        </p>
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
    { key: "left", label: leftParam, value: Number(data.left.DoanhThu) },
    { key: "right", label: rightParam, value: Number(data.right.DoanhThu) },
  ];

  return (
    <div className="space-y-4">
      {toolbar}
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label={`Doanh thu kỳ gốc (${leftParam})`}
          value={formatVnd(data.left.DoanhThu)}
        />
        <StatCard
          label={`Doanh thu kỳ so sánh (${rightParam})`}
          value={formatVnd(data.right.DoanhThu)}
        />
        <ChangeCard label="Chênh lệch doanh thu" change={data.doanh_thu} />
        <ChangeCard label="Chênh lệch chi phí" change={data.chi_phi} />
      </div>
      <section className="space-y-3 rounded-container border border-border bg-surface p-4">
        <h2 className="text-[15px] font-bold">Doanh thu hai kỳ</h2>
        <Bars
          items={chartItems}
          ariaLabel={`Biểu đồ so sánh doanh thu kỳ ${leftParam} và kỳ ${rightParam}`}
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
              leftParam,
              formatVnd(data.left.DoanhThu),
              formatVnd(data.left.GiaVon),
              formatNumber(data.left.SoDon),
            ],
            [
              rightParam,
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
