import { OrderScreen } from "@/features/sales/order-screen";
import { PaymentPanel } from "@/features/sales/payment-panel";
import { OrderLookup } from "@/features/sales/order-lookup";

export default function SalesPage() {
  return (
    <div className="space-y-6">
      <OrderScreen />
      <OrderLookup />
      <PaymentPanel orderId={1} />
    </div>
  );
}
