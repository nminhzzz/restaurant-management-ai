"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useState } from "react";

import { PageHeader } from "@/components/page-states";

import { DoneStep } from "./done-step";
import { FloorStep } from "./floor-step";
import { OrderDetail } from "./order-detail";
import { OrderStep } from "./order-step";
import { PaymentPanel } from "./payment-panel";
import { SalesStepper } from "./sales-stepper";
import type { SalesStep } from "./types";

const STEPS: SalesStep[] = ["floor", "order", "pay", "done"];

function numberParam(value: string | null): number | null {
  const n = Number(value);
  return value !== null && Number.isInteger(n) && n > 0 ? n : null;
}

export function SalesWorkspace() {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const [change, setChange] = useState<number | null>(null);

  const tableId = numberParam(params.get("table"));
  const orderId = numberParam(params.get("order"));
  const requested = (params.get("step") ?? "floor") as SalesStep;
  // A step that lacks what it needs falls back to the floor instead of rendering empty.
  const step: SalesStep =
    STEPS.includes(requested) &&
    (requested === "floor" || requested === "order" || orderId !== null)
      ? requested
      : "floor";

  const go = useCallback(
    (
      next: SalesStep,
      table: number | null = tableId,
      order: number | null = orderId,
    ) => {
      const query = new URLSearchParams();
      if (next !== "floor") {
        query.set("step", next);
        if (table !== null) query.set("table", String(table));
        if (order !== null) query.set("order", String(order));
      }
      const text = query.toString();
      router.replace(text ? `${pathname}?${text}` : pathname);
    },
    [router, pathname, tableId, orderId],
  );

  // PaymentPanel's polling effect depends on this callback, so it must stay
  // referentially stable across renders or the 3-second poll restarts each time.
  const handlePaid = useCallback(
    (summary: { change: number | null }) => {
      setChange(summary.change);
      go("done", tableId, orderId);
    },
    [go, tableId, orderId],
  );

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <PageHeader title="Bán hàng" />
        <SalesStepper
          current={step}
          enabled={{
            floor: true,
            order: step !== "floor" && step !== "done",
            pay: orderId !== null && step !== "done",
          }}
          onGo={(next) => go(next)}
        />
      </div>

      {step === "floor" && (
        <FloorStep
          onNewOrder={(table) => go("order", table, null)}
          onAddMore={(order, table) => go("order", table, order)}
          onPay={(order, table) => go("pay", table, order)}
        />
      )}
      {step === "order" && (
        <OrderStep
          tableId={tableId}
          orderId={orderId}
          onBack={() => go("floor")}
          onSent={(order, next) =>
            next === "pay" ? go("pay", tableId, order) : go("floor")
          }
        />
      )}
      {step === "pay" && orderId !== null && (
        <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
          <OrderDetail key={`detail-${orderId}`} orderId={orderId} />
          <PaymentPanel
            key={`payment-${orderId}`}
            orderId={orderId}
            onPaid={handlePaid}
          />
        </div>
      )}
      {step === "done" && orderId !== null && (
        <DoneStep
          orderId={orderId}
          change={change}
          onFinish={() => go("floor")}
        />
      )}
    </div>
  );
}
