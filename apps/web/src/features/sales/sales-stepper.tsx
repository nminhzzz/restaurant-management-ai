import { Check } from "lucide-react";

import { cn } from "@/lib/utils";

import type { SalesStep } from "./types";

const STEPS: { key: Exclude<SalesStep, "done">; label: string }[] = [
  { key: "floor", label: "Chọn bàn" },
  { key: "order", label: "Gọi món" },
  { key: "pay", label: "Thanh toán" },
];
const ORDER: SalesStep[] = ["floor", "order", "pay", "done"];

export function SalesStepper({
  current,
  enabled,
  onGo,
}: {
  current: SalesStep;
  enabled: Record<Exclude<SalesStep, "done">, boolean>;
  onGo: (step: Exclude<SalesStep, "done">) => void;
}) {
  const index = ORDER.indexOf(current);
  return (
    <ol
      aria-label="Các bước bán hàng"
      className="flex overflow-hidden rounded-control border border-border-strong bg-surface"
    >
      {STEPS.map((step, i) => {
        const isCurrent = i === Math.min(index, 2);
        const done = i < index;
        return (
          <li
            key={step.key}
            className="not-first:border-l not-first:border-border"
          >
            <button
              type="button"
              aria-current={isCurrent ? "step" : undefined}
              disabled={!enabled[step.key]}
              onClick={() => onGo(step.key)}
              className={cn(
                "flex h-11 items-center gap-2.5 px-4 font-semibold text-muted disabled:cursor-not-allowed disabled:opacity-50",
                isCurrent && "bg-surface-sunken text-ink",
              )}
            >
              <span
                className={cn(
                  "grid size-[22px] place-items-center rounded-badge bg-surface-sunken text-xs font-bold ring-1 ring-border",
                  isCurrent && "bg-primary text-white ring-0",
                  done && "bg-success-subtle text-success-fg ring-0",
                )}
              >
                {done ? <Check className="size-3.5" aria-hidden /> : i + 1}
              </span>
              {step.label}
            </button>
          </li>
        );
      })}
    </ol>
  );
}
