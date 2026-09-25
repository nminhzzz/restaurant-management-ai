"use client";
import { useState } from "react";
import { apiFetch } from "@/lib/api-client";

export function OrderLookup() {
  const [code, setCode] = useState("");
  const [result, setResult] = useState<unknown>(null);
  async function search() {
    const data = await apiFetch<{ items: unknown[]; total: number }>("/sales/orders?code=" + encodeURIComponent(code));
    setResult(data);
  }
  return (
    <div>
      <input aria-label="Mã order" value={code} onChange={(e) => setCode(e.target.value)} />
      <button onClick={search}>Tìm</button>
      {result ? <pre>{JSON.stringify(result)}</pre> : null}
    </div>
  );
}
