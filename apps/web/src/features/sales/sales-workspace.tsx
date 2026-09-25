"use client";

import { ReceiptText } from "lucide-react";
import { useState } from "react";

import { EmptyState, PageHeader } from "@/components/page-states";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { OrderDetail } from "@/features/sales/order-detail";
import { OrderLookup } from "@/features/sales/order-lookup";
import { OrderScreen } from "@/features/sales/order-screen";
import { PaymentPanel } from "@/features/sales/payment-panel";

export function SalesWorkspace() {
  const [tab, setTab] = useState("order");
  const [orderId, setOrderId] = useState<number | null>(null);

  function payNow(id: number) {
    setOrderId(id);
    setTab("payment");
  }

  return (
    <div className="space-y-5">
      <PageHeader title="Bán hàng" />
      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="order" className="h-9 px-4">
            Gọi món
          </TabsTrigger>
          <TabsTrigger value="payment" className="h-9 px-4">
            Thanh toán
          </TabsTrigger>
        </TabsList>
        <TabsContent
          value="order"
          forceMount
          className="data-[state=inactive]:hidden"
        >
          <OrderScreen onOrderCreated={setOrderId} onPayNow={payNow} />
        </TabsContent>
        <TabsContent value="payment">
          <div className="grid items-start gap-5 lg:grid-cols-[360px_minmax(0,1fr)]">
            <OrderLookup onSelect={setOrderId} selectedId={orderId} />
            {orderId === null ? (
              <EmptyState
                icon={ReceiptText}
                title="Chưa chọn order"
                description="Tra cứu theo mã order, hoặc gửi một order mới rồi bấm Thanh toán."
              />
            ) : (
              <div className="space-y-5">
                <OrderDetail key={`detail-${orderId}`} orderId={orderId} />
                <PaymentPanel key={`payment-${orderId}`} orderId={orderId} />
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
