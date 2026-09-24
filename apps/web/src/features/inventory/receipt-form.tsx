"use client";
import { useState } from "react";
export function ReceiptForm({ onSubmit }: { onSubmit?: (lines: unknown) => void }) {
  const [purchaseUnit, setPurchaseUnit] = useState("");
  const [conversionFactor, setConversionFactor] = useState("");
  return (
    <form onSubmit={(e) => { e.preventDefault(); onSubmit?.({ purchase_unit: purchaseUnit, conversion_factor: conversionFactor }); }}>
      <input aria-label="Đơn vị mua" value={purchaseUnit} onChange={(e) => setPurchaseUnit(e.target.value)} />
      <input aria-label="Hệ số quy đổi" type="number" value={conversionFactor} onChange={(e) => setConversionFactor(e.target.value)} />
      <button type="submit">Tạo phiếu nhập</button>
    </form>
  );
}
