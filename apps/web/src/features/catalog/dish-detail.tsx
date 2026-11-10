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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  CostRatioHint,
  PriceScheduler,
  type CostBasis,
} from "@/features/catalog/price-scheduler";
import { RecipeEditor } from "@/features/catalog/recipe-editor";
import type {
  Dish,
  DishCost,
  Ingredient,
  PriceVersion,
  RecipeVersion,
} from "@/features/catalog/types";
import { useCanWrite } from "@/features/catalog/use-role";
import { apiFetch } from "@/lib/api-client";
import {
  formatDate,
  formatNumber,
  formatPercent,
  formatVnd,
} from "@/lib/format";
import { useAction } from "@/lib/use-action";
import { useResource } from "@/lib/use-resource";

const WRITE_ROLES = ["MANAGER"];
const HISTORY_LIMIT = 3;

type DishVersions = { prices: PriceVersion[]; recipes: RecipeVersion[] };

const loadIngredients = () =>
  apiFetch<{ items: Ingredient[] } | Ingredient[]>(
    "/catalog/ingredients?size=200",
  ).then((r) => (Array.isArray(r) ? r : r.items));

function unknown(value: number | null, format: (value: number) => string) {
  return value === null ? "Chưa xác định" : format(value);
}

/** FR-CAT-29: each ingredient of the recipe in force with its unit cost and amount. */
function CostBreakdown({ cost }: { cost: DishCost }) {
  if (cost.TinhTrang === "Chưa có công thức") {
    return <p className="text-muted">Chưa có công thức.</p>;
  }
  return (
    <div className="space-y-2">
      <Table>
        <caption className="sr-only">Giá vốn theo nguyên liệu</caption>
        <TableHeader>
          <TableRow>
            <TableHead>Nguyên liệu</TableHead>
            <TableHead className="text-right">Định lượng</TableHead>
            <TableHead className="text-right">Đơn giá bình quân</TableHead>
            <TableHead className="text-right">Thành tiền</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {(cost.ChiTiet ?? []).map((line) => (
            <TableRow key={line.MaNguyenLieu}>
              <TableCell className="font-medium">
                {line.TenNguyenLieu}
              </TableCell>
              <TableCell className="text-right tabular-nums">
                {formatNumber(line.DinhLuong)} {line.DonViTinh}
              </TableCell>
              <TableCell className="text-right tabular-nums">
                {unknown(line.DonGiaBinhQuan, formatVnd)}
              </TableCell>
              <TableCell className="text-right tabular-nums">
                {unknown(line.ThanhTien, formatVnd)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {cost.TinhTrang === "Chưa đủ dữ liệu" ? (
        <p role="status" className="text-warning-fg">
          Chưa đủ dữ liệu: {cost.NguyenLieuThieuGia.join(", ")} chưa có đơn giá
          bình quân nên chưa tính được giá vốn.
        </p>
      ) : (
        <p role="status" className={cost.CanhBao ? "text-warning-fg" : ""}>
          Giá vốn ước tính{" "}
          <strong>{unknown(cost.GiaVonUocTinh, formatVnd)}</strong> · tỷ lệ giá
          vốn <strong>{unknown(cost.TyLeGiaVon, formatPercent)}</strong> · lãi
          gộp mỗi suất <strong>{unknown(cost.LaiGop, formatVnd)}</strong>
          {cost.CanhBao
            ? ` · vượt ngưỡng ${formatPercent(cost.NguongCanhBao)}`
            : ""}
        </p>
      )}
    </div>
  );
}

function ApplyNowRow({
  onApply,
  pending,
  costBasis,
}: {
  onApply: (gia: number) => void;
  pending: boolean;
  costBasis?: CostBasis | null;
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
        <CostRatioHint price={value} basis={costBasis} />
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

  // FR-CAT-29: the estimate is the manager's; other roles never request it.
  const loadCost = useCallback(
    () =>
      canWrite
        ? apiFetch<DishCost>(`/catalog/dishes/${dish.MaMon}/cost`)
        : Promise.resolve(null),
    [canWrite, dish.MaMon],
  );
  const costRes = useResource(loadCost);
  const cost = costRes.status === "ready" ? costRes.data : null;
  const costBasis: CostBasis | null =
    cost && cost.GiaVonUocTinh !== null
      ? { cost: cost.GiaVonUocTinh, threshold: cost.NguongCanhBao }
      : null;

  const ingredientsRes = useResource(loadIngredients);
  const ingredients =
    ingredientsRes.status === "ready" ? ingredientsRes.data : [];

  const [cancelPriceOpen, setCancelPriceOpen] = useState(false);
  const applyNowAction = useAction();
  const cancelPriceAction = useAction();

  function reloadAll() {
    versionsRes.reload();
    costRes.reload();
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
  const pendingPrice =
    prices.find((p) => p.TrangThai === "Chờ áp dụng") ?? null;
  const currentPrice =
    prices.find((p) => p.TrangThai === "Đang áp dụng") ?? null;
  const priceHistory = prices
    .filter((p) => p !== pendingPrice && p !== currentPrice)
    .slice(0, HISTORY_LIMIT);

  const pendingRecipe =
    recipes.find((r) => r.TrangThai === "Chờ áp dụng") ?? null;
  const currentRecipe =
    recipes.find((r) => r.TrangThai === "Đang áp dụng") ?? null;
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
              <h3 className="font-bold">Giá bán</h3>
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
                  <PriceScheduler
                    dishId={dish.MaMon}
                    onScheduled={reloadAll}
                    costBasis={costBasis}
                  />
                  <ApplyNowRow
                    onApply={handleApplyNow}
                    pending={applyNowAction.pending}
                    costBasis={costBasis}
                  />
                </div>
              )}
            </section>

            {cost ? (
              <section className="space-y-3 border-b border-border py-5">
                <h3 className="font-bold">Giá vốn ước tính</h3>
                <CostBreakdown cost={cost} />
              </section>
            ) : null}

            <section className="space-y-3 pt-5">
              <h3 className="font-bold">Công thức</h3>
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
