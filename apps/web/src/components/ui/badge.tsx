import { cva, type VariantProps } from "class-variance-authority";
import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

// Design tokens §2: one semantic colour per state, never more than one accent a screen.
const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
  {
    variants: {
      tone: {
        neutral: "bg-surface-sunken text-muted",
        primary: "bg-primary-subtle text-primary-subtle-fg",
        success: "bg-success-subtle text-success-fg",
        warning: "bg-warning-subtle text-warning-fg",
        danger: "bg-danger-subtle text-danger-fg",
        muted: "border border-dashed border-border-strong text-subtle",
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
