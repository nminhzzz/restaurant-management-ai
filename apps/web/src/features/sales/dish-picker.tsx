"use client";

import { Search, UtensilsCrossed } from "lucide-react";
import { useState } from "react";

import { EmptyState } from "@/components/page-states";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { formatVnd } from "@/lib/format";
import { cn } from "@/lib/utils";

export type PickableDish = {
  MaMon: number;
  TenMon: string;
  TrangThai?: string;
  GiaHienTai?: number | null;
};

const UNSELLABLE = new Set(["Hết nguyên liệu", "Ẩn", "Nháp"]);

/**
 * Reusable dish grid — shared by OrderScreen (new order) and OrderDetail (FR-SALE-06/09,
 * adding dishes to an already-open order). Dialog variant picks one dish and closes.
 */
export function DishPicker({
  dishes,
  onPick,
}: {
  dishes: PickableDish[];
  onPick: (dish: PickableDish) => void;
}) {
  const [query, setQuery] = useState("");
  const sellable = dishes.filter((d) => !UNSELLABLE.has(d.TrangThai ?? ""));
  const needle = query.trim().toLowerCase();
  const visible = sellable.filter(
    (d) => !needle || d.TenMon.toLowerCase().includes(needle),
  );

  return (
    <div className="space-y-3">
      <div className="relative">
        <Search
          className="absolute top-3.5 left-2.5 size-4 text-subtle"
          aria-hidden
        />
        <Input
          type="search"
          aria-label="Tìm món"
          placeholder="Tìm món"
          className="h-11 pl-8"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>
      {visible.length === 0 ? (
        <EmptyState
          icon={UtensilsCrossed}
          title="Không có món nào bán được"
          description="Các món đều đang hết nguyên liệu, bị ẩn hoặc chưa khớp tìm kiếm."
        />
      ) : (
        <div className="grid max-h-96 grid-cols-2 gap-2.5 overflow-y-auto sm:grid-cols-3">
          {visible.map((d) => (
            <button
              key={d.MaMon}
              type="button"
              onClick={() => onPick(d)}
              className={cn(
                "flex min-h-24 flex-col justify-between gap-2 rounded-container border border-border bg-surface p-3 text-left transition-[border-color,box-shadow,transform] hover:border-ink hover:shadow-lift active:translate-y-px",
              )}
            >
              <span className="line-clamp-2 text-[15px] leading-5 font-medium">
                {d.TenMon}
              </span>
              {typeof d.GiaHienTai === "number" && (
                <span className="text-muted tabular-nums">
                  {formatVnd(d.GiaHienTai)}
                </span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export function DishPickerDialog({
  open,
  onOpenChange,
  dishes,
  onPick,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  dishes: PickableDish[];
  onPick: (dish: PickableDish) => void;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-[min(36rem,calc(100vw-2rem))]">
        <DialogHeader>
          <DialogTitle>Thêm món vào order</DialogTitle>
        </DialogHeader>
        <DishPicker
          dishes={dishes}
          onPick={(dish) => {
            onPick(dish);
            onOpenChange(false);
          }}
        />
      </DialogContent>
    </Dialog>
  );
}
