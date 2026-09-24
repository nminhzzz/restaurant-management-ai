"use client";
import { useState } from "react";

export function PriceScheduler({ dishId }: { dishId: number }) {
  const [date, setDate] = useState("");
  const [error, setError] = useState<string | null>(null);
  const today = new Date().toISOString().slice(0, 10);
  const handleChange = (v: string) => {
    setDate(v);
    if (v && v <= today) {
      setError("Business Date phải là một Business Date trong tương lai");
    } else {
      setError(null);
    }
  };
  void dishId;
  return (
    <div>
      <label htmlFor="bd">Business Date áp dụng</label>
      <input
        id="bd"
        type="date"
        value={date}
        onChange={(e) => handleChange(e.target.value)}
      />
      {error && <p>{error}</p>}
      <button disabled={!!error}>Lưu</button>
    </div>
  );
}
