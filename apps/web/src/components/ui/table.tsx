import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

export function Table({ className, ...props }: ComponentProps<"table">) {
  return (
    <div className="overflow-x-auto rounded-container border border-border bg-surface">
      <table className={cn("w-full text-sm", className)} {...props} />
    </div>
  );
}

export function TableHeader({ className, ...props }: ComponentProps<"thead">) {
  return <thead className={cn("bg-surface-sunken", className)} {...props} />;
}

export function TableBody({ className, ...props }: ComponentProps<"tbody">) {
  return (
    <tbody className={cn("divide-y divide-border", className)} {...props} />
  );
}

export function TableRow({ className, ...props }: ComponentProps<"tr">) {
  return <tr className={cn("hover:bg-canvas", className)} {...props} />;
}

export function TableHead({ className, ...props }: ComponentProps<"th">) {
  return (
    <th
      scope="col"
      className={cn(
        "px-3 py-2 text-left text-xs font-medium tracking-wide text-subtle uppercase",
        className,
      )}
      {...props}
    />
  );
}

export function TableCell({ className, ...props }: ComponentProps<"td">) {
  return <td className={cn("px-3 py-2 text-ink", className)} {...props} />;
}

export function TableCaption({
  className,
  ...props
}: ComponentProps<"caption">) {
  return (
    <caption
      className={cn("px-3 py-2 text-xs text-subtle", className)}
      {...props}
    />
  );
}

export function TableEmpty({
  colSpan,
  children,
}: {
  colSpan: number;
  children: string;
}) {
  return (
    <tr>
      <td
        colSpan={colSpan}
        className="px-3 py-6 text-center text-sm text-subtle"
      >
        {children}
      </td>
    </tr>
  );
}
