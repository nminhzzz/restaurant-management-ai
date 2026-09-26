import { cva, type VariantProps } from "class-variance-authority";
import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

// Design tokens §2: one semantic colour per state, never more than one accent a screen.
// The square marker repeats the tone so state still reads when colour is hard to tell apart.
const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-badge px-2 py-0.5 text-xs font-semibold whitespace-nowrap before:size-1.5 before:shrink-0 before:bg-current before:content-['']",
  {
    variants: {
      tone: {
        neutral: "bg-surface-sunken text-muted ring-1 ring-border ring-inset",
        primary: "bg-primary text-white",
        success: "bg-success-subtle text-success-fg",
        warning: "bg-warning-subtle text-warning-fg",
        danger: "bg-danger-subtle text-danger-fg",
        muted:
          "border border-dashed border-border-strong text-subtle before:bg-transparent before:ring-1 before:ring-current",
      },
    },
    defaultVariants: { tone: "neutral" },
  },
);

export function Badge({
  className,
  tone,
  ...props
}: ComponentProps<"span"> & VariantProps<typeof badgeVariants>) {
  return <span className={cn(badgeVariants({ tone }), className)} {...props} />;
}
