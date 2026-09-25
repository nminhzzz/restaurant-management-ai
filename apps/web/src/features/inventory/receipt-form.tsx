"use client";

import { Plus, Trash2 } from "lucide-react";
import { useId, useState } from "react";

import { FormField } from "@/components/form-field";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { apiFetch } from "@/lib/api-client";
import { formatVnd } from "@/lib/format";
import { useAction } from "@/lib/use-action";

import type { IngredientOption, SupplierOption } from "./types";

type DraftLine = {
  key: string;
  ingredientId: string;
  purchaseUnit: string;
  conversionFactor: string;
  quantity: string;
  unitPrice: string;
};

function emptyLine(ingredientId = ""): DraftLine {
  return {
    key: Math.random().toString(36).slice(2),
    ingredientId,
    purchaseUnit: "",
    conversionFactor: "1",
    quantity: "",
    unitPrice: "",
  };
}

/** Dialog body for creating a goods receipt (FR-INV-01). */
export function ReceiptForm({
  ingredients,
  suppliers,
  prefillIngredientId,
  onCreated,
}: {
  ingredients: IngredientOption[];
  suppliers: SupplierOption[];
  prefillIngredientId?: number | null;
  onCreated: () => void;
}) {
  const formId = useId();
  const { run, pending } = useAction();
  const [supplierId, setSupplierId] = useState("");
  const [lines, setLines] = useState<DraftLine[]>([
    emptyLine(prefillIngredientId ? String(prefillIngredientId) : ""),
  ]);
  const [error, setError] = useState<string | null>(null);

  function updateLine(key: string, patch: Partial<DraftLine>) {
    setLines((prev) =>
      prev.map((l) => (l.key === key ? { ...l, ...patch } : l)),
    );
  }

  function lineTotal(line: DraftLine): number {
    const qty = Number(line.quantity) || 0;
    const factor = Number(line.conversionFactor) || 0;
    const price = Number(line.unitPrice) || 0;
    return qty * factor * price;
  }

  const total = lines.reduce((sum, l) => sum + lineTotal(l), 0);

  async function submit() {
    setError(null);
    if (lines.some((l) => !l.ingredientId)) {
      setError("Chọn nguyên liệu cho từng dòng.");
      return;
    }
    if (lines.some((l) => !(Number(l.quantity) > 0))) {
      setError("Số lượng phải lớn hơn 0.");
      return;
    }
    if (lines.some((l) => Number(l.unitPrice) < 0 || l.unitPrice === "")) {
      setError("Nhập đơn giá hợp lệ.");
      return;
    }
    const result = await run(
      () =>
        apiFetch<{ MaPhieuNhap: number }>("/inventory/receipts", {
          method: "POST",
          body: {
            supplier_id: supplierId ? Number(supplierId) : null,
            lines: lines.map((l) => ({
              ingredient_id: Number(l.ingredientId),
              quantity: Number(l.quantity),
              unit_price: Number(l.unitPrice),
              purchase_unit: l.purchaseUnit || null,
              conversion_factor: l.conversionFactor
                ? Number(l.conversionFactor)
                : null,
            })),
          },
        }),
      "Đã tạo phiếu nhập.",
    );
    if (result) onCreated();
  }

  return (
    <div className="space-y-4">
      <FormField id={`${formId}-supplier`} label="Nhà cung cấp">
        <Select value={supplierId} onValueChange={setSupplierId}>
          <SelectTrigger id={`${formId}-supplier`}>
            <SelectValue placeholder="Không chọn" />
          </SelectTrigger>
          <SelectContent>
            {suppliers.map((s) => (
              <SelectItem key={s.MaNhaCungCap} value={String(s.MaNhaCungCap)}>
                {s.TenNhaCungCap}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </FormField>

      <div className="space-y-3">
        {lines.map((line, index) => (
          <div
            key={line.key}
            className="grid grid-cols-2 gap-2 rounded-container border border-border p-3 sm:grid-cols-6"
          >
            <div className="col-span-2 sm:col-span-2">
              <FormField id={`${formId}-ing-${line.key}`} label="Nguyên liệu">
                <Select
                  value={line.ingredientId}
                  onValueChange={(v) =>
                    updateLine(line.key, { ingredientId: v })
                  }
                >
                  <SelectTrigger id={`${formId}-ing-${line.key}`}>
                    <SelectValue placeholder="Chọn" />
                  </SelectTrigger>
                  <SelectContent>
                    {ingredients.map((ing) => (
                      <SelectItem
                        key={ing.MaNguyenLieu}
                        value={String(ing.MaNguyenLieu)}
                      >
                        {ing.TenNguyenLieu} ({ing.DonViTinh})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </FormField>
            </div>
            <FormField id={`${formId}-unit-${line.key}`} label="Đơn vị mua">
              <Input
                id={`${formId}-unit-${line.key}`}
                placeholder="bao, thùng…"
                value={line.purchaseUnit}
                onChange={(e) =>
                  updateLine(line.key, { purchaseUnit: e.target.value })
                }
              />
            </FormField>
            <FormField
              id={`${formId}-factor-${line.key}`}
              label="Hệ số quy đổi"
            >
              <Input
                id={`${formId}-factor-${line.key}`}
                type="number"
                inputMode="decimal"
                min={0}
                value={line.conversionFactor}
                onChange={(e) =>
                  updateLine(line.key, { conversionFactor: e.target.value })
                }
              />
            </FormField>
            <FormField id={`${formId}-qty-${line.key}`} label="Số lượng">
              <Input
                id={`${formId}-qty-${line.key}`}
                type="number"
                inputMode="decimal"
                min={0}
                value={line.quantity}
                onChange={(e) =>
                  updateLine(line.key, { quantity: e.target.value })
                }
              />
            </FormField>
            <div className="col-span-2 flex items-end gap-2 sm:col-span-1">
              <FormField id={`${formId}-price-${line.key}`} label="Đơn giá">
                <Input
                  id={`${formId}-price-${line.key}`}
                  type="number"
                  inputMode="decimal"
                  min={0}
                  value={line.unitPrice}
                  onChange={(e) =>
                    updateLine(line.key, { unitPrice: e.target.value })
                  }
                />
              </FormField>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                aria-label={`Xoá dòng ${index + 1}`}
                disabled={lines.length === 1}
                onClick={() =>
                  setLines((prev) => prev.filter((l) => l.key !== line.key))
                }
              >
                <Trash2 aria-hidden />
              </Button>
            </div>
            <p className="col-span-2 text-xs text-muted tabular-nums sm:col-span-6">
              Thành tiền: {formatVnd(lineTotal(line))}
            </p>
          </div>
        ))}
        <Button
          type="button"
          variant="secondary"
          size="sm"
          onClick={() => setLines((prev) => [...prev, emptyLine()])}
        >
          <Plus aria-hidden />
          Thêm dòng
        </Button>
      </div>

      {error ? (
        <p role="alert" className="text-danger-fg">
          {error}
        </p>
      ) : null}

      <div className="flex items-center justify-between gap-3 border-t border-border pt-4">
        <p className="font-medium">
          Tổng cộng: <span className="tabular-nums">{formatVnd(total)}</span>
        </p>
        <Button onClick={submit} disabled={pending}>
          {pending ? "Đang tạo…" : "Tạo phiếu nhập"}
        </Button>
      </div>
    </div>
  );
}
