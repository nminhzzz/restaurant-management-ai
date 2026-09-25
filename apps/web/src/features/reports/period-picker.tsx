"use client";

import { cn } from "@/lib/utils";

export const GRANULARITIES = [
  { value: "day", label: "Ngày" },
  { value: "week", label: "Tuần" },
  { value: "month", label: "Tháng" },
  { value: "year", label: "Năm" },
];

/** `2026-09` for the current calendar month, the format `/reports/*?month=` expects. */
export function currentMonth(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

/** The calendar month right before `month` (`"2026-01"` → `"2025-12"`). */
export function previousMonth(month: string): string {
  const [year, mon] = month.split("-").map(Number);
  const date = new Date(year, mon - 2, 1);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
}

export function GranularityPicker({
  value,
  onChange,
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div
      role="group"
      aria-label="Kỳ báo cáo"
      className="inline-flex gap-0.5 rounded-control bg-surface-sunken p-[3px]"
    >
      {GRANULARITIES.map((option) => (
        <button
          key={option.value}
          type="button"
          aria-pressed={value === option.value}
          onClick={() => onChange(option.value)}
          className={cn(
            "h-8 rounded-md px-3 font-medium transition-colors",
            value === option.value
              ? "bg-surface text-ink shadow-sm shadow-ink/10"
              : "text-muted hover:text-ink",
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

export function MonthPicker({
  value,
  onChange,
  label = "Tháng báo cáo",
}: {
  value: string;
  onChange: (value: string) => void;
  label?: string;
}) {
  return (
    <label className="grid gap-1 text-xs text-subtle">
      <span>{label}</span>
      <input
        type="month"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-9 rounded-control border border-border bg-surface px-3 text-sm text-ink focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
      />
    </label>
  );
}
