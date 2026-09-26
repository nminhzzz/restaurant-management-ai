import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

/** Placeholder while data loads (tokens §7: pulse, never a full-screen spinner). */
export function Skeleton({ className, ...props }: ComponentProps<"div">) {
  return (
    <div
      className={cn(
        "rounded-badge motion-safe:animate-pulse bg-surface-sunken",
        className,
      )}
      {...props}
    />
  );
}

export function TableSkeleton({
  rows = 4,
  cols = 3,
}: {
  rows?: number;
  cols?: number;
}) {
  return (
    <div className="space-y-2 rounded-container border border-border bg-surface p-3">
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div
          key={rowIndex}
          className="grid gap-3"
          style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}
        >
          {Array.from({ length: cols }).map((__, colIndex) => (
            <Skeleton key={colIndex} className="h-5" />
          ))}
        </div>
      ))}
    </div>
  );
}
