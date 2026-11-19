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
  quantity: string;
  unitPrice: string;
  total: string;
  /** Which of price / total the user typed last; quantity edits recompute the other. */
  anchor: "price" | "total";
};

function emptyLine(ingredientId = ""): DraftLine {
  return {
    key: Math.random().toString(36).slice(2),
    ingredientId,
    quantity: "",
    unitPrice: "",
    total: "",
    anchor: "price",
  };
}

type Decimal = { digits: bigint; scale: number };

function parseDecimal(value: string): Decimal | null {
  const match = /^(\d*)(?:\.(\d+))?$/.exec(value.trim());
  if (!match || (match[1] === "" && match[2] === undefined)) return null;
  const fraction = match[2] ?? "";
  return {
    digits: BigInt(`${match[1] || "0"}${fraction}`),
    scale: fraction.length,
  };
}

const ZERO = BigInt(0);
const TWO = BigInt(2);
const HUNDRED = BigInt(100);
const TEN = BigInt(10);

/** Exact half-up division of non-negative bigints, mirroring the API's `money()`. */
function divideHalfUp(numerator: bigint, denominator: bigint): bigint {
  return (TWO * numerator + denominator) / (TWO * denominator);
}

function centsToString(cents: bigint): string {
  const whole = cents / HUNDRED;
  const fraction = (cents % HUNDRED)
    .toString()
    .padStart(2, "0")
    .replace(/0+$/, "");
  return fraction ? `${whole}.${fraction}` : String(whole);
}

/** quantity x unit price, rounded half-up to 2 decimals; "" when not computable. */
function computeTotal(quantity: string, unitPrice: string): string {
  const q = parseDecimal(quantity);
  const p = parseDecimal(unitPrice);
  if (!q || !p) return "";
  const product = q.digits * p.digits;
  const scale = q.scale + p.scale;
  const cents =
    scale >= 2
      ? divideHalfUp(product, TEN ** BigInt(scale - 2))
      : product * TEN ** BigInt(2 - scale);
  return centsToString(cents);
}

/** line total / quantity, rounded half-up to 2 decimals; "" when quantity is not above 0. */
function computeUnitPrice(quantity: string, total: string): string {
  const q = parseDecimal(quantity);
  const t = parseDecimal(total);
  if (!q || !t || q.digits === ZERO) return "";
  const numerator = t.digits * TEN ** BigInt(q.scale + 2);
  const denominator = q.digits * TEN ** BigInt(t.scale);
  return centsToString(divideHalfUp(numerator, denominator));
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
  const [receiptDate, setReceiptDate] = useState(() =>
    new Date().toLocaleDateString("en-CA"),
  );
  const [lines, setLines] = useState<DraftLine[]>([
    emptyLine(prefillIngredientId ? String(prefillIngredientId) : ""),
  ]);
  const [error, setError] = useState<string | null>(null);

  function updateLine(key: string, patch: Partial<DraftLine>) {
    setLines((prev) =>
      prev.map((l) => (l.key === key ? { ...l, ...patch } : l)),
    );
  }

  function unitOf(line: DraftLine): string {
    return (
      ingredients.find((i) => String(i.MaNguyenLieu) === line.ingredientId)
        ?.DonViTinh ?? ""
    );
  }

  function editQuantity(line: DraftLine, quantity: string) {
    updateLine(
      line.key,
      line.anchor === "price"
        ? { quantity, total: computeTotal(quantity, line.unitPrice) }
        : { quantity, unitPrice: computeUnitPrice(quantity, line.total) },
    );
  }

  const total = lines.reduce((sum, l) => sum + (Number(l.total) || 0), 0);

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
            receipt_date: `${receiptDate}T00:00:00`,
            lines: lines.map((l) => ({
              ingredient_id: Number(l.ingredientId),
              quantity: Number(l.quantity),
              unit_price: Number(l.unitPrice),
            })),
          },
        }),
      "Đã tạo phiếu nhập.",
    );
    if (result) onCreated();
  }

  return (
    <div className="space-y-4">
      <FormField id={`${formId}-date`} label="Ngày nhập">
        <Input
          id={`${formId}-date`}
          type="date"
          value={receiptDate}
          onChange={(e) => setReceiptDate(e.target.value)}
        />
      </FormField>
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
                        {ing.TenNguyenLieu}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </FormField>
            </div>
            <FormField
              id={`${formId}-qty-${line.key}`}
              label={unitOf(line) ? `Số lượng (${unitOf(line)})` : "Số lượng"}
            >
              <Input
                id={`${formId}-qty-${line.key}`}
                type="number"
                inputMode="decimal"
                min={0}
                value={line.quantity}
                onChange={(e) => editQuantity(line, e.target.value)}
              />
            </FormField>
            <FormField
              id={`${formId}-price-${line.key}`}
              label={
                unitOf(line) ? `Đơn giá (đ/${unitOf(line)})` : "Đơn giá (đ)"
              }
            >
              <Input
                id={`${formId}-price-${line.key}`}
                type="number"
                inputMode="decimal"
                min={0}
                value={line.unitPrice}
                onChange={(e) =>
                  updateLine(line.key, {
                    unitPrice: e.target.value,
                    total: computeTotal(line.quantity, e.target.value),
                    anchor: "price",
                  })
                }
              />
            </FormField>
            <div className="col-span-2 flex items-end gap-2 sm:col-span-2">
              <FormField
                id={`${formId}-total-${line.key}`}
                label="Thành tiền (đ)"
              >
                <Input
                  id={`${formId}-total-${line.key}`}
                  type="number"
                  inputMode="decimal"
                  min={0}
                  value={line.total}
                  onChange={(e) =>
                    updateLine(line.key, {
                      total: e.target.value,
                      unitPrice: computeUnitPrice(
                        line.quantity,
                        e.target.value,
                      ),
                      anchor: "total",
                    })
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
