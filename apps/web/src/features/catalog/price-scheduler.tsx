"use client";
import { CircleAlert } from "lucide-react";
import { useState } from "react";

import { FormField } from "@/components/form-field";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/api-client";
import { useAction } from "@/lib/use-action";

/**
 * Schedules a future price (FR-CAT-20). `BusinessDateApDung` is optional: leaving it
 * blank asks the API for the next Business Date.
 */
export function PriceScheduler({
  dishId,
  onScheduled,
}: {
  dishId: number;
  onScheduled?: () => void;
}) {
  const [date, setDate] = useState("");
  const [price, setPrice] = useState("");
  const [error, setError] = useState<string | null>(null);
  const { run, pending } = useAction();
  const today = new Date().toISOString().slice(0, 10);

  const handleChange = (v: string) => {
    setDate(v);
    if (v && v <= today) {
      setError("Business Date phải là một Business Date trong tương lai");
    } else {
      setError(null);
    }
  };

  const priceValue = Number(price);
  const canSave = !error && price.trim() !== "" && priceValue > 0 && !pending;

  function handleSave() {
    void run(async () => {
      const body: { Gia: number; BusinessDateApDung?: string } = {
        Gia: priceValue,
      };
      if (date) body.BusinessDateApDung = date;
      const result = await apiFetch(
        `/catalog/dishes/${dishId}/prices/schedule`,
        { method: "POST", body },
      );
      onScheduled?.();
      setDate("");
      setPrice("");
      return result;
    }, "Đã lên lịch giá mới.");
  }

  return (
    <div className="flex flex-wrap items-start gap-3">
      <FormField id="gia" label="Giá mới">
        <Input
          id="gia"
          type="number"
          min={0}
          value={price}
          onChange={(e) => setPrice(e.target.value)}
        />
      </FormField>
      <div className="space-y-1.5">
        <Label htmlFor="bd">Business Date áp dụng</Label>
        <Input
          id="bd"
          type="date"
          className={error ? "border-danger" : undefined}
          aria-invalid={error !== null}
          aria-describedby={error ? "bd-error" : undefined}
          value={date}
          onChange={(e) => handleChange(e.target.value)}
        />
        {error && (
          <p
            id="bd-error"
            className="flex items-center gap-1 text-xs text-danger-fg"
          >
            <CircleAlert className="size-3.5" aria-hidden />
            {error}
          </p>
        )}
      </div>
      <Button className="mt-6" disabled={!canSave} onClick={handleSave}>
        Lưu
      </Button>
    </div>
  );
}
