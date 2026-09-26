"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export const PAGE_SIZES = [10, 20, 50] as const;

/** Page numbers with gaps: 1 … 4 5 6 … 12. `null` marks a gap. */
export function pageWindow(page: number, pageCount: number): (number | null)[] {
  if (pageCount <= 7) {
    return Array.from({ length: pageCount }, (_, i) => i + 1);
  }
  const pages = new Set([1, pageCount, page - 1, page, page + 1]);
  const sorted = [...pages]
    .filter((p) => p >= 1 && p <= pageCount)
    .sort((a, b) => a - b);
  const out: (number | null)[] = [];
  for (const p of sorted) {
    const previous = out[out.length - 1];
    if (typeof previous === "number" && p - previous > 1) out.push(null);
    out.push(p);
  }
  return out;
}

/**
 * Footer of a paginated table: "Hiển thị 21–40 trên 68", rows per page, page buttons.
 * Works for client- and server-side paging alike; the caller owns the state.
 */
export function DataPagination({
  page,
  pageSize,
  total,
  onPageChange,
  onPageSizeChange,
  className,
}: {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  className?: string;
}) {
  const pageCount = Math.max(1, Math.ceil(total / pageSize));
  const current = Math.min(page, pageCount);
  const first = total === 0 ? 0 : (current - 1) * pageSize + 1;
  const last = Math.min(current * pageSize, total);

  return (
    <nav
      aria-label="Phân trang"
      className={cn(
        "flex flex-wrap items-center justify-between gap-3 text-muted",
        className,
      )}
    >
      <p className="tabular-nums">
        Hiển thị {first}–{last} trên {total}
      </p>
      <div className="flex flex-wrap items-center gap-3">
        {onPageSizeChange ? (
          <label className="flex items-center gap-2">
            Số dòng
            <select
              aria-label="Số dòng mỗi trang"
              className="h-9 rounded-control border border-border-strong bg-surface px-2 text-ink hover:border-ink focus-visible:border-primary focus-visible:ring-1 focus-visible:ring-primary focus-visible:outline-none"
              value={pageSize}
              onChange={(e) => onPageSizeChange(Number(e.target.value))}
            >
              {PAGE_SIZES.map((size) => (
                <option key={size} value={size}>
                  {size}
                </option>
              ))}
            </select>
          </label>
        ) : null}
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            aria-label="Trang trước"
            disabled={current <= 1}
            onClick={() => onPageChange(current - 1)}
          >
            <ChevronLeft />
          </Button>
          {pageWindow(current, pageCount).map((p, index) =>
            p === null ? (
              <span key={`gap-${index}`} aria-hidden className="px-1">
                …
              </span>
            ) : (
              <Button
                key={p}
                variant={p === current ? "primary" : "ghost"}
                size="icon"
                aria-label={`Trang ${p}`}
                aria-current={p === current ? "page" : undefined}
                className="tabular-nums"
                onClick={() => onPageChange(p)}
              >
                {p}
              </Button>
            ),
          )}
          <Button
            variant="ghost"
            size="icon"
            aria-label="Trang sau"
            disabled={current >= pageCount}
            onClick={() => onPageChange(current + 1)}
          >
            <ChevronRight />
          </Button>
        </div>
      </div>
    </nav>
  );
}
