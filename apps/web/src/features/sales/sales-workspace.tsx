"use client";

import { useState } from "react";

import { OrderLookup } from "@/features/sales/order-lookup";
import { OrderScreen } from "@/features/sales/order-screen";
import { PaymentPanel } from "@/features/sales/payment-panel";

export function SalesWorkspace() {
  const [orderId, setOrderId] = useState<number | null>(null);

  return (
    <div className="space-y-6">
      <OrderScreen onOrderCreated={setOrderId} />
      <OrderLookup onSelect={setOrderId} />
      {orderId === null ? (
        <p className="text-sm text-slate-500">
          Tạo order mới hoặc tra cứu để chọn một order thanh toán.
        </p>
      ) : (
        <PaymentPanel orderId={orderId} />
      )}
    </div>
  );
}
