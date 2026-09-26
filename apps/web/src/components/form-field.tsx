import { CircleAlert } from "lucide-react";
import type { ReactNode } from "react";

import { Label } from "@/components/ui/label";

/**
 * Label above, control in the middle, error (or help) below — tokens.md §6. The control
 * must carry `id={id}`; pass `aria-invalid`/`aria-describedby={`${id}-message`}` on it
 * when `error` is set.
 */
export function FormField({
  id,
  label,
  error,
  help,
  children,
}: {
  id: string;
  label: string;
  error?: string | null;
  help?: string;
  children: ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      {children}
      {error ? (
        <p
          id={`${id}-message`}
          className="flex items-center gap-1 text-xs font-semibold text-danger-fg"
        >
          <CircleAlert className="size-3.5 shrink-0" aria-hidden />
          {error}
        </p>
      ) : help ? (
        <p id={`${id}-message`} className="text-xs text-subtle">
          {help}
        </p>
      ) : null}
    </div>
  );
}
