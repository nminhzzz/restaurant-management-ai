import { CircleAlert, type LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { statusTone } from "@/lib/status";

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <header className="flex flex-wrap items-end justify-between gap-3">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight text-balance">
          {title}
        </h1>
        {description ? <p className="text-muted">{description}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
    </header>
  );
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: {
  icon: LucideIcon;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "grid justify-items-center gap-2 rounded-container border border-dashed border-border-strong bg-surface px-5 py-10 text-center",
        className,
      )}
    >
      <span className="grid size-11 place-items-center rounded-control bg-surface-sunken text-muted ring-1 ring-border ring-inset">
        <Icon className="size-5" aria-hidden />
      </span>
      <p className="text-base font-bold">{title}</p>
      {description ? (
        <p className="max-w-[40ch] text-muted">{description}</p>
      ) : null}
      {action ? <div className="mt-2">{action}</div> : null}
    </div>
  );
}

/** Skeleton shaped like a table; the visually hidden text keeps the state readable. */
export function LoadingState({ rows = 4 }: { rows?: number }) {
  return (
    <div
      role="status"
      className="space-y-3 rounded-container border border-border bg-surface p-4"
    >
      <span className="sr-only">Đang tải…</span>
      <Skeleton className="h-4 w-1/3" />
      {Array.from({ length: rows }, (_, index) => (
        <Skeleton key={index} className="h-9 w-full" />
      ))}
    </div>
  );
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div
      role="alert"
      className="flex flex-wrap items-center gap-3 rounded-container bg-danger-subtle px-4 py-3 text-danger-fg shadow-[inset_4px_0_0_0_var(--color-danger)]"
    >
      <CircleAlert className="size-4 shrink-0" aria-hidden />
      <p className="flex-1">{message}</p>
      {onRetry ? (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          Thử lại
        </Button>
      ) : null}
    </div>
  );
}

export function StatCard({
  label,
  value,
  hint,
  badge,
}: {
  label: string;
  value: string;
  hint?: ReactNode;
  badge?: ReactNode;
}) {
  return (
    <div className="grid gap-1.5 rounded-container border border-border bg-surface p-4">
      <div className="flex items-center justify-between gap-2 text-[11px] leading-4 font-bold tracking-wider text-subtle uppercase">
        <span>{label}</span>
        {badge}
      </div>
      <p className="text-[28px] leading-9 font-bold tracking-tight tabular-nums">
        {value}
      </p>
      {hint ? <p className="text-xs text-muted">{hint}</p> : null}
    </div>
  );
}

export function StatusBadge({ status }: { status: string }) {
  return <Badge tone={statusTone(status)}>{status}</Badge>;
}
