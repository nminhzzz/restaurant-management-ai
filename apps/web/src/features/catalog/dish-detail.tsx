"use client";

import { useCallback, useState } from "react";

import { ConfirmDialog } from "@/components/confirm-dialog";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ErrorState, LoadingState } from "@/components/page-states";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PriceScheduler } from "@/features/catalog/price-scheduler";
import { RecipeEditor } from "@/features/catalog/recipe-editor";
import type {
  Dish,
  Ingredient,
  PriceVersion,
  RecipeVersion,
} from "@/features/catalog/types";
import { useCanWrite } from "@/features/catalog/use-role";
import { apiFetch } from "@/lib/api-client";
import { formatDate, formatVnd } from "@/lib/format";
import { useAction } from "@/lib/use-action";
import { useResource } from "@/lib/use-resource";

const WRITE_ROLES = ["MANAGER"];
const HISTORY_LIMIT = 3;

type DishVersions = { prices: PriceVersion[]; recipes: RecipeVersion[] };

const loadIngredients = () =>
  apiFetch<{ items: Ingredient[] } | Ingredient[]>(
    "/catalog/ingredients?size=200",
  ).then((r) => (Array.isArray(r) ? r : r.items));

function ApplyNowRow({
  onApply,
  pending,
}: {
  onApply: (gia: number) => void;
  pending: boolean;
}) {
  const [value, setValue] = useState("");
  return (
    <div className="flex flex-wrap items-end gap-2">
      <div className="space-y-1.5">
        <Label htmlFor="apply-now-price">Áp dụng giá ngay</Label>
        <Input
          id="apply-now-price"
          type="number"
          min={0}
          className="w-32"
          value={value}
          onChange={(e) => setValue(e.target.value)}
        />
      </div>
      <Button
        variant="secondary"
        disabled={pending || value.trim() === "" || Number(value) <= 0}
        onClick={() => onApply(Number(value))}
      >
        Áp dụng ngay
      </Button>
    </div>
  );
}

export function DishDetail({
  dish,
  onOpenChange,
  onChanged,
}: {
  dish: Dish;
  onOpenChange: (open: boolean) => void;
  onChanged: () => void;
}) {
  const canWrite = useCanWrite(WRITE_ROLES);

  const loadVersions = useCallback(
    (): Promise<DishVersions> =>
      Promise.all([
        apiFetch<PriceVersion[]>(`/catalog/dishes/${dish.MaMon}/prices`),
        apiFetch<RecipeVersion[]>(`/catalog/dishes/${dish.MaMon}/recipes`),
      ]).then(([prices, recipes]) => ({ prices, recipes })),
    [dish.MaMon],
  );
  const versionsRes = useResource(loadVersions);

  const ingredientsRes = useResource(loadIngredients);
  const ingredients =
    ingredientsRes.status === "ready" ? ingredientsRes.data : [];

  const [cancelPriceOpen, setCancelPriceOpen] = useState(false);
  const applyNowAction = useAction();
  const cancelPriceAction = useAction();

  function reloadAll() {
    versionsRes.reload();
    onChanged();
  }

  function handleApplyNow(gia: number) {
    void applyNowAction.run(async () => {
      await apiFetch(`/catalog/dishes/${dish.MaMon}/prices/apply-now`, {
        method: "POST",
        body: { Gia: gia },
      });
      reloadAll();
    }, "Đã áp dụng giá mới ngay lập tức.");
  }

  function handleCancelPrice(pendingPrice: PriceVersion) {
    void cancelPriceAction.run(async () => {
      await apiFetch(`/catalog/prices/${pendingPrice.MaLichSuGia}`, {
        method: "DELETE",
      });
      setCancelPriceOpen(false);
      reloadAll();
    }, "Đã hủy giá đang chờ áp dụng.");
  }

  const prices = versionsRes.status === "ready" ? versionsRes.data.prices : [];
  const recipes =
    versionsRes.status === "ready" ? versionsRes.data.recipes : [];
  const pendingPrice = prices.find((p) => p.TrangThai === "Nháp") ?? null;
  const currentPrice = prices.find((p) => p.TrangThai === "Hiệu lực") ?? null;
  const priceHistory = prices
    .filter((p) => p !== pendingPrice && p !== currentPrice)
    .slice(0, HISTORY_LIMIT);

  const pendingRecipe = recipes.find((r) => r.TrangThai === "Nháp") ?? null;
  const currentRecipe = recipes.find((r) => r.TrangThai === "Hiệu lực") ?? null;
  const recipeHistory = recipes
    .filter((r) => r !== pendingRecipe && r !== currentRecipe)
    .slice(0, HISTORY_LIMIT);

  return (
    <Dialog open onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{dish.TenMon}</DialogTitle>
        </DialogHeader>

        {versionsRes.status === "loading" ? (
          <LoadingState rows={3} />
        ) : versionsRes.status === "error" ? (
          <ErrorState
            message={versionsRes.message}
            onRetry={versionsRes.reload}
          />
        ) : (
          <>
            <section className="space-y-3 border-b border-border pb-5">
              <h3 className="font-semibold">Giá bán</h3>
              <p className="text-muted">
                Giá hiện tại:{" "}
                <span className="font-medium text-ink">
                  {formatVnd(currentPrice?.Gia ?? dish.GiaHienTai)}
                </span>
              </p>
              {pendingPrice && (
                <div className="flex flex-wrap items-center justify-between gap-2 rounded-control border border-dashed border-border-strong bg-surface-sunken px-3 py-2">
                  <p>
                    Đang chờ áp dụng:{" "}
                    <span className="font-medium">
                      {formatVnd(pendingPrice.Gia)}
                    </span>
                    {" từ "}
                    {formatDate(pendingPrice.BusinessDateApDung)}
                  </p>
                  {canWrite && (
                    <Button
                      variant="outlineDanger"
                      size="sm"
                      onClick={() => setCancelPriceOpen(true)}
                    >
                      Hủy lịch
                    </Button>
                  )}
                </div>
              )}
              {priceHistory.length > 0 && (
                <ul className="space-y-1 text-xs text-subtle">
                  {priceHistory.map((p) => (
                    <li key={p.MaLichSuGia}>
                      {formatDate(p.BusinessDateApDung)} · {formatVnd(p.Gia)} ·{" "}
                      {p.TrangThai}
                    </li>
                  ))}
                </ul>
              )}
              {canWrite && (
                <div className="space-y-2">
                  <PriceScheduler dishId={dish.MaMon} onScheduled={reloadAll} />
                  <ApplyNowRow
                    onApply={handleApplyNow}
                    pending={applyNowAction.pending}
                  />
                </div>
              )}
            </section>

            <section className="space-y-3 pt-5">
              <h3 className="font-semibold">Công thức</h3>
              {ingredientsRes.status === "loading" ? (
                <LoadingState rows={2} />
              ) : ingredientsRes.status === "error" ? (
                <p className="text-danger-fg">{ingredientsRes.message}</p>
              ) : (
                <RecipeEditor
                  dishId={dish.MaMon}
                  ingredients={ingredients}
                  canWrite={canWrite}
                  currentRecipe={currentRecipe}
                  pendingRecipe={pendingRecipe}
                  history={recipeHistory}
                  onChanged={reloadAll}
                />
              )}
            </section>
          </>
        )}

        <ConfirmDialog
          open={cancelPriceOpen}
          onOpenChange={setCancelPriceOpen}
          title="Hủy giá đang chờ áp dụng?"
          confirmLabel="Hủy lịch"
          danger
          pending={cancelPriceAction.pending}
          onConfirm={() => pendingPrice && handleCancelPrice(pendingPrice)}
        />
      </DialogContent>
    </Dialog>
  );
}
