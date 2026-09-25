"use client";

import { ClipboardCheck, ClipboardList } from "lucide-react";
import { useState } from "react";

import {
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  StatusBadge,
} from "@/components/page-states";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { apiFetch } from "@/lib/api-client";
import { formatNumber } from "@/lib/format";
import { useAction } from "@/lib/use-action";
import { useResource } from "@/lib/use-resource";
import { cn } from "@/lib/utils";

import type { Stocktake } from "./types";

type StockRow = {
  MaNguyenLieu: number;
  TenNguyenLieu: string;
  SoLuongTon?: number;
};

// page_size is capped at 100 server-side (see inventory router); that covers the
// expected ingredient catalog size for this MVP.
const loadStock = () =>
  apiFetch<{ items: StockRow[] }>("/inventory/stock?page_size=100").then(
    (d) => d.items || [],
  );
const loadStocktakes = () => apiFetch<Stocktake[]>("/inventory/stocktakes");

function DraftStocktake({
  stocktakeId,
  ingredients,
  onDone,
}: {
  stocktakeId: number;
  ingredients: StockRow[];
  onDone: () => void;
}) {
  const [counts, setCounts] = useState<Record<number, string>>({});
  const { run, pending, error } = useAction();

  const allFilled = ingredients.every((ing) => {
    const v = counts[ing.MaNguyenLieu];
    return v !== undefined && v !== "" && Number(v) >= 0;
  });

  async function confirm() {
    const payload = ingredients.map((ing) => ({
      ingredient_id: ing.MaNguyenLieu,
      actual_qty: Number(counts[ing.MaNguyenLieu]),
    }));
    const recorded = await run(() =>
      apiFetch(`/inventory/stocktakes/${stocktakeId}/counts`, {
        method: "POST",
        body: payload,
      }),
    );
    if (recorded === undefined) return;
    const confirmed = await run(
      () =>
        apiFetch(`/inventory/stocktakes/${stocktakeId}/confirm`, {
          method: "POST",
        }),
      "Đã xác nhận kiểm kê, cập nhật tồn kho.",
    );
    if (confirmed !== undefined) onDone();
  }

  return (
    <div className="space-y-4">
      <Table>
        <caption className="sr-only">Nhập số liệu kiểm kê</caption>
        <TableHeader>
          <TableRow>
            <TableHead>Nguyên liệu</TableHead>
            <TableHead className="text-right">Tồn hệ thống</TableHead>
            <TableHead className="text-right">Tồn thực tế</TableHead>
            <TableHead className="text-right">Chênh lệch</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {ingredients.map((ing) => {
            const raw = counts[ing.MaNguyenLieu] ?? "";
            const diff =
              raw === "" ? null : Number(raw) - (ing.SoLuongTon ?? 0);
            return (
              <TableRow key={ing.MaNguyenLieu}>
                <TableCell className="font-medium">
                  {ing.TenNguyenLieu}
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatNumber(ing.SoLuongTon)}
                </TableCell>
                <TableCell className="text-right">
                  <Input
                    aria-label={`Tồn thực tế ${ing.TenNguyenLieu}`}
                    type="number"
                    inputMode="decimal"
                    min={0}
                    className="ml-auto w-28 text-right"
                    value={raw}
                    onChange={(e) =>
                      setCounts((prev) => ({
                        ...prev,
                        [ing.MaNguyenLieu]: e.target.value,
                      }))
                    }
                  />
                </TableCell>
                <TableCell
                  className={cn(
                    "text-right tabular-nums",
                    diff !== null &&
                      diff !== 0 &&
                      "font-semibold text-danger-fg",
                  )}
                >
                  {diff === null ? "—" : formatNumber(diff)}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>

      {error ? (
        <p role="alert" className="text-danger-fg">
          {error}
        </p>
      ) : null}

      <div className="flex justify-end">
        <Button onClick={confirm} disabled={!allFilled || pending}>
          {pending ? "Đang xác nhận…" : "Xác nhận kiểm kê"}
        </Button>
      </div>
    </div>
  );
}

export function StocktakePanel() {
  const stock = useResource(loadStock);
  const stocktakes = useResource(loadStocktakes);
  const createAction = useAction();
  const [draftId, setDraftId] = useState<number | null>(null);

  async function createStocktake() {
    const st = await createAction.run(() =>
      apiFetch<{ MaPhieuKiemKe: number }>("/inventory/stocktakes", {
        method: "POST",
      }),
    );
    if (st) setDraftId(st.MaPhieuKiemKe);
  }

  const pastStocktakes =
    stocktakes.status === "ready"
      ? stocktakes.data.filter((s) => s.MaPhieuKiemKe !== draftId)
      : [];

  return (
    <div className="space-y-5">
      <PageHeader
        title="Kiểm kê"
        description="Đối chiếu tồn thực tế với hệ thống theo định kỳ."
        actions={
          draftId === null ? (
            <Button onClick={createStocktake} disabled={createAction.pending}>
              <ClipboardCheck aria-hidden />
              Tạo phiếu kiểm kê
            </Button>
          ) : null
        }
      />

      {draftId !== null ? (
        stock.status === "loading" ? (
          <LoadingState rows={5} />
        ) : stock.status === "error" ? (
          <ErrorState message={stock.message} onRetry={stock.reload} />
        ) : stock.data.length === 0 ? (
          <EmptyState
            icon={ClipboardList}
            title="Chưa có nguyên liệu"
            description="Thêm nguyên liệu trong Danh mục trước khi kiểm kê."
          />
        ) : (
          <DraftStocktake
            stocktakeId={draftId}
            ingredients={stock.data}
            onDone={() => {
              setDraftId(null);
              stock.reload();
              stocktakes.reload();
            }}
          />
        )
      ) : null}

      <div className="space-y-3">
        <h2 className="font-medium">Lịch sử kiểm kê</h2>
        {stocktakes.status === "loading" ? (
          <LoadingState rows={3} />
        ) : stocktakes.status === "error" ? (
          <ErrorState
            message={stocktakes.message}
            onRetry={stocktakes.reload}
          />
        ) : pastStocktakes.length === 0 ? (
          <EmptyState
            icon={ClipboardList}
            title="Chưa có phiếu kiểm kê"
            description="Phiếu kiểm kê đã xác nhận sẽ hiện tại đây."
          />
        ) : (
          <Table>
            <caption className="sr-only">Lịch sử kiểm kê</caption>
            <TableHeader>
              <TableRow>
                <TableHead>Mã phiếu</TableHead>
                <TableHead>Trạng thái</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {pastStocktakes.map((s) => (
                <TableRow key={s.MaPhieuKiemKe}>
                  <TableCell className="font-medium tabular-nums">
                    #{s.MaPhieuKiemKe}
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={s.TrangThai} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  );
}
