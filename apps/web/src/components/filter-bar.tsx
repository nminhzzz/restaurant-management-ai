"use client";

import { Search, X } from "lucide-react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

const selectClass =
  "h-9 rounded-control border border-border bg-surface px-3 text-ink focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none";

/** Row of filters above a table; shows "Xóa bộ lọc" only while a filter is active. */
export function FilterBar({
  children,
  active = false,
  onReset,
  className,
}: {
  children: ReactNode;
  active?: boolean;
  onReset?: () => void;
  className?: string;
}) {
  return (
    <div
      role="search"
      className={cn("flex flex-wrap items-end gap-2", className)}
    >
      {children}
      {active && onReset ? (
        <Button variant="ghost" onClick={onReset}>
          <X />
          Xóa bộ lọc
        </Button>
      ) : null}
    </div>
  );
}

export function SearchFilter({
  label,
  value,
  onChange,
  className,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  className?: string;
}) {
  return (
    <div className={cn("relative w-full sm:w-64", className)}>
      <Search
        className="absolute top-2.5 left-2.5 size-4 text-subtle"
        aria-hidden
      />
      <Input
        type="search"
        aria-label={label}
        placeholder={label}
        className="pl-8"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}

/** Native select: reliable on tablets and in tests. `""` means "no filter". */
export function SelectFilter({
  label,
  value,
  onChange,
  options,
  allLabel,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: readonly { value: string; label: string }[];
  allLabel: string;
}) {
  return (
    <select
      aria-label={label}
      className={selectClass}
      value={value}
      onChange={(e) => onChange(e.target.value)}
    >
      <option value="">{allLabel}</option>
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}

/** From/to Business Date pair, ISO `YYYY-MM-DD` strings, empty = open-ended. */
export function DateRangeFilter({
  from,
  to,
  onChange,
}: {
  from: string;
  to: string;
  onChange: (range: { from: string; to: string }) => void;
}) {
  return (
    <div className="flex items-center gap-1.5">
      <Input
        type="date"
        aria-label="Từ ngày"
        className="w-40"
        value={from}
        max={to || undefined}
        onChange={(e) => onChange({ from: e.target.value, to })}
      />
      <span className="text-subtle">đến</span>
      <Input
        type="date"
        aria-label="Đến ngày"
        className="w-40"
        value={to}
        min={from || undefined}
        onChange={(e) => onChange({ from, to: e.target.value })}
      />
    </div>
  );
}
