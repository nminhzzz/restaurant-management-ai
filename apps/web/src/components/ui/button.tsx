import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

// Design tokens §6: primary for the main action, secondary for cancel/back, ghost for
// icons, danger for destructive calls; h-11 is the tablet/POS size (NFR-13).
const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-control text-sm font-semibold transition-[color,background-color,border-color,transform] active:translate-y-px focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50 [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        primary: "bg-primary text-white hover:bg-primary-hover",
        secondary:
          "border border-border-strong bg-surface text-ink hover:border-ink hover:bg-surface-sunken",
        ghost: "text-muted hover:bg-surface-sunken hover:text-ink",
        danger: "bg-danger text-white hover:bg-danger-hover",
        outlineDanger:
          "border border-danger bg-surface text-danger-fg hover:bg-danger-subtle",
      },
      size: {
        default: "h-9 px-4",
        sm: "h-8 px-3 text-xs",
        pos: "h-11 px-5",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: { variant: "primary", size: "default" },
  },
);

export function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & { asChild?: boolean }) {
  const Component = asChild ? Slot : "button";
  return (
    <Component
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  );
}

export { buttonVariants };
