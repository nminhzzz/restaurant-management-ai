import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

export function Input({ className, type, ...props }: ComponentProps<"input">) {
  return (
    <input
      type={type}
      className={cn(
        "flex h-9 w-full rounded-control border border-border-strong bg-surface px-3 py-1 text-sm text-ink placeholder:text-subtle hover:border-ink focus-visible:border-primary focus-visible:ring-1 focus-visible:ring-primary focus-visible:outline-none aria-invalid:border-danger aria-invalid:ring-1 aria-invalid:ring-danger disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
}

export function Textarea({ className, ...props }: ComponentProps<"textarea">) {
  return (
    <textarea
      className={cn(
        "flex w-full rounded-control border border-border-strong bg-surface px-3 py-2 text-sm text-ink placeholder:text-subtle hover:border-ink focus-visible:border-primary focus-visible:ring-1 focus-visible:ring-primary focus-visible:outline-none aria-invalid:border-danger aria-invalid:ring-1 aria-invalid:ring-danger disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
}
