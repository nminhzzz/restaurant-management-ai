"use client";

import { PackageMinus, Plus, Trash2 } from "lucide-react";
import { useCallback, useId, useState } from "react";

import { DataPagination } from "@/components/data-pagination";
import {
  DateRangeFilter,
  FilterBar,
  SelectFilter,
} from "@/components/filter-bar";
import { FormField } from "@/components/form-field";
import {
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  StatusBadge,
} from "@/components/page-states";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { apiFetch } from "@/lib/api-client";
import { formatDateTime, formatNumber } from "@/lib/format";
import { useAction } from "@/lib/use-action";
import { useResource } from "@/lib/use-resource";

import { IssueDetailDialog } from "./issue-detail-dialog";
import { ISSUE_REASONS } from "./types";
import { LotSelect } from "./lot-select";
import type { IngredientOption, StockIssue, Stocktake } from "./types";

const PAGE_SIZE = 20;

type IssueFilters = { reason: string; dateFrom: string; dateTo: string };

const INITIAL_FILTERS: IssueFilters = { reason: "", dateFrom: "", dateTo: "" };

function queryOf(filters: IssueFilters, page: number): string {
  const params = new URLSearchParams();
  if (filters.reason) params.set("reason", filters.reason);
  if (filters.dateFrom) params.set("date_from", filters.dateFrom);
  if (filters.dateTo) params.set("date_to", filters.dateTo);
  params.set("page", String(page));
  params.set("page_size", String(PAGE_SIZE));
  return `/inventory/issues?${params.toString()}`;
}

const loadIngredients = () =>
  apiFetch<{ items: IngredientOption[] }>("/catalog/ingredients?size=200").then(
    (d) => d.items || [],
  );

type DraftLine = {
  key: string;
  ingredientId: string;
  quantity: string;
  lotId: string;
  orderLineId: string;
  servings: string;
};

type PreparedPreviewLine = {
  ingredient_id: number;
  ingredient_name: string;
  unit: string;
  quantity: number;
};

type PreparedPreviewData = {
  order_line_id: number;
  servings: number;
  written_servings: number;
  eligible_servings: number;
  lines: PreparedPreviewLine[];
};

function emptyLine(): DraftLine {
  return {
    key: Math.random().toString(36).slice(2),
    ingredientId: "",
    quantity: "",
    lotId: "",
    orderLineId: "",
    servings: "",
  };
}

function PreparedPreview({
  orderLineId,
  servings,
}: {
  orderLineId: string;
  servings: string;
}) {
  const ready = Boolean(orderLineId) && Number(servings) > 0;
  const load = useCallback(() => {
    if (!ready) return Promise.resolve(null);
    return apiFetch<PreparedPreviewData>(
      `/inventory/issues/prepared-preview?order_line_id=${orderLineId}&servings=${servings}`,
    );
  }, [ready, orderLineId, servings]);
  const preview = useResource(load);

  if (!ready) return null;
  if (preview.status === "loading") {
    return <p className="text-xs text-muted">Đang tính nguyên liệu…</p>;
  }
  if (preview.status === "error") {
    return <p className="text-xs text-danger-fg">{preview.message}</p>;
  }
  if (!preview.data) return null;
  return (
    <div className="space-y-1 rounded-control bg-surface-sunken p-2.5">
      <p className="text-xs font-semibold text-muted">
        Nguyên liệu ghi nhận theo tiêu hao gốc · đã hủy{" "}
        {preview.data.written_servings}/{preview.data.eligible_servings} suất
      </p>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Nguyên liệu</TableHead>
            <TableHead className="text-right">Số lượng</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {preview.data.lines.map((line) => (
            <TableRow key={line.ingredient_id}>
              <TableCell>
                {line.ingredient_name} ({line.unit})
              </TableCell>
              <TableCell className="text-right tabular-nums">
                {formatNumber(line.quantity)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

function IssueForm({
  ingredients,
  onCreated,
}: {
  ingredients: IngredientOption[];
  onCreated: () => void;
}) {
  const formId = useId();
  const { run, pending, error: actionError } = useAction();
  const [reason, setReason] = useState<string>(ISSUE_REASONS[0]);
  const [source, setSource] = useState<string>("Nguyên liệu");
  const [stocktakeId, setStocktakeId] = useState("");
  const [orderCode, setOrderCode] = useState("");
  const [orderLines, setOrderLines] = useState<
    {
      MaChiTietOrder: number;
      TenMon?: string;
      SoLuong: number;
      TrangThai?: string;
    }[]
  >([]);
  const [orderLookupError, setOrderLookupError] = useState<string | null>(null);
  const [lines, setLines] = useState<DraftLine[]>([emptyLine()]);
  const loadStocktakes = useCallback(
    () =>
      apiFetch<{ items: Stocktake[] }>(
        "/inventory/stocktakes?status=%C4%90%C3%A3%20ch%E1%BB%91t&page_size=50",
      ),
    [],
  );
  const stocktakes = useResource(loadStocktakes);
  const [error, setError] = useState<string | null>(null);

  function updateLine(key: string, patch: Partial<DraftLine>) {
    setLines((prev) =>
      prev.map((l) => (l.key === key ? { ...l, ...patch } : l)),
    );
  }

  async function findOrderLines() {
    setOrderLookupError(null);
    setOrderLines([]);
    if (!orderCode.trim()) return;
    try {
      const found = await apiFetch<{
        items: { MaOrder: number }[];
      }>(`/sales/orders?code=${encodeURIComponent(orderCode.trim())}&size=1`);
      const order = found.items[0];
      if (!order) {
        setOrderLookupError("Không tìm thấy order.");
        return;
      }
      const detail = await apiFetch<{
        lines?: {
          MaChiTietOrder: number;
          TenMon?: string;
          SoLuong: number;
          TrangThai?: string;
        }[];
      }>(`/sales/orders/${order.MaOrder}`);
      setOrderLines(
        (detail.lines ?? []).filter((line) => line.TrangThai !== "Đã hủy"),
      );
    } catch {
      setOrderLookupError("Không tra cứu được order.");
    }
  }

  async function submit() {
    setError(null);
    if (source === "Món đã chế biến") {
      if (lines.some((l) => !l.orderLineId || !(Number(l.servings) > 0))) {
        setError("Chọn dòng món và nhập số suất hủy.");
        return;
      }
    } else {
      if (lines.some((l) => !l.ingredientId)) {
        setError("Chọn nguyên liệu cho từng dòng.");
        return;
      }
      if (lines.some((l) => !(Number(l.quantity) > 0))) {
        setError("Số lượng phải lớn hơn 0.");
        return;
      }
    }
    if (source === "Kiểm kê" && !stocktakeId) {
      setError("Chọn phiếu kiểm kê đã chốt.");
      return;
    }
    const result = await run(
      () =>
        apiFetch("/inventory/issues", {
          method: "POST",
          body: {
            reason,
            source,
            stocktake_id: stocktakeId ? Number(stocktakeId) : null,
            lines:
              source === "Món đã chế biến"
                ? lines.map((l) => ({
                    order_line_id: Number(l.orderLineId),
                    servings: Number(l.servings),
                  }))
                : lines.map((l) => ({
                    ingredient_id: Number(l.ingredientId),
                    quantity: Number(l.quantity),
                    lot_id: l.lotId ? Number(l.lotId) : null,
                  })),
          },
        }),
      "Đã ghi nhận xuất kho. Nếu lô đang được giữ, hệ thống đã giải phóng lượt giữ — kiểm tra lại dòng món liên quan.",
    );
    if (result !== undefined) onCreated();
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2">
        <FormField id={`${formId}-reason`} label="Lý do">
          <Select value={reason} onValueChange={setReason}>
            <SelectTrigger id={`${formId}-reason`}>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {ISSUE_REASONS.map((r) => (
                <SelectItem key={r} value={r}>
                  {r}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </FormField>
        <FormField id={`${formId}-source`} label="Nguồn">
          <Select value={source} onValueChange={setSource}>
            <SelectTrigger id={`${formId}-source`}>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Nguyên liệu">Nguyên liệu</SelectItem>
              <SelectItem value="Món đã chế biến">Món đã chế biến</SelectItem>
              <SelectItem value="Kiểm kê">Kiểm kê</SelectItem>
            </SelectContent>
          </Select>
        </FormField>
      </div>
      {source === "Kiểm kê" ? (
        <FormField id={`${formId}-stocktake`} label="Phiếu kiểm kê đã chốt">
          <Select value={stocktakeId} onValueChange={setStocktakeId}>
            <SelectTrigger id={`${formId}-stocktake`}>
              <SelectValue placeholder="Chọn phiếu kiểm kê" />
            </SelectTrigger>
            <SelectContent>
              {stocktakes.status === "ready"
                ? stocktakes.data.items.map((item) => (
                    <SelectItem
                      key={item.MaPhieuKiemKe}
                      value={String(item.MaPhieuKiemKe)}
                    >
                      #{item.MaPhieuKiemKe}
                    </SelectItem>
                  ))
                : null}
            </SelectContent>
          </Select>
        </FormField>
      ) : null}

      <div className="space-y-3">
        {lines.map((line, index) => (
          <div
            key={line.key}
            className="grid grid-cols-2 gap-2 rounded-container border border-border p-3 sm:grid-cols-6"
          >
            {source === "Món đã chế biến" ? (
              <>
                <div className="col-span-2">
                  <FormField
                    id={`${formId}-order-${line.key}`}
                    label="Mã order"
                  >
                    <div className="flex gap-2">
                      <Input
                        id={`${formId}-order-${line.key}`}
                        value={orderCode}
                        onChange={(e) => setOrderCode(e.target.value)}
                        placeholder="ORD-..."
                      />
                      <Button
                        type="button"
                        size="sm"
                        variant="secondary"
                        onClick={findOrderLines}
                      >
                        Tìm
                      </Button>
                    </div>
                    {orderLookupError && (
                      <p className="text-xs text-danger-fg">
                        {orderLookupError}
                      </p>
                    )}
                  </FormField>
                </div>
                <div className="col-span-2">
                  <FormField id={`${formId}-line-${line.key}`} label="Dòng món">
                    <Select
                      value={line.orderLineId}
                      onValueChange={(value) =>
                        updateLine(line.key, { orderLineId: value })
                      }
                    >
                      <SelectTrigger id={`${formId}-line-${line.key}`}>
                        <SelectValue placeholder="Chọn dòng món" />
                      </SelectTrigger>
                      <SelectContent>
                        {orderLines.map((orderLine) => (
                          <SelectItem
                            key={orderLine.MaChiTietOrder}
                            value={String(orderLine.MaChiTietOrder)}
                          >
                            #{orderLine.MaChiTietOrder} ·{" "}
                            {orderLine.TenMon ?? "Món"} × {orderLine.SoLuong}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </FormField>
                </div>
                <FormField id={`${formId}-sv-${line.key}`} label="Số suất">
                  <Input
                    id={`${formId}-sv-${line.key}`}
                    type="number"
                    min={1}
                    value={line.servings}
                    onChange={(e) =>
                      updateLine(line.key, { servings: e.target.value })
                    }
                  />
                </FormField>
                <div className="flex items-end justify-end">
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
                <div className="col-span-full">
                  <PreparedPreview
                    orderLineId={line.orderLineId}
                    servings={line.servings}
                  />
                </div>
              </>
            ) : (
              <>
                <div className="col-span-2 sm:col-span-3">
                  <FormField
                    id={`${formId}-ing-${line.key}`}
                    label="Nguyên liệu"
                  >
                    <Select
                      value={line.ingredientId}
                      onValueChange={(v) =>
                        updateLine(line.key, { ingredientId: v, lotId: "" })
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
                {source === "Nguyên liệu" ? (
                  <FormField
                    id={`${formId}-lot-${line.key}`}
                    label="Lô nguyên liệu"
                  >
                    <LotSelect
                      key={line.ingredientId}
                      id={`${formId}-lot-${line.key}`}
                      ingredientId={line.ingredientId}
                      value={line.lotId}
                      onChange={(value) =>
                        updateLine(line.key, { lotId: value })
                      }
                    />
                  </FormField>
                ) : null}
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
                <div className="flex items-end justify-end">
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
              </>
            )}
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

      {(error ?? actionError) ? (
        <p role="alert" className="text-danger-fg">
          {error ?? actionError}
        </p>
      ) : null}

      <div className="flex justify-end border-t border-border pt-4">
        <Button onClick={submit} disabled={pending}>
          {pending ? "Đang ghi nhận…" : "Ghi nhận xuất kho"}
        </Button>
      </div>
    </div>
  );
}

export function IssueList() {
  const [filters, setFilters] = useState<IssueFilters>(INITIAL_FILTERS);
  const [page, setPage] = useState(1);

  const fetchIssues = useCallback(
    () =>
      apiFetch<{ items: StockIssue[]; total: number }>(queryOf(filters, page)),
    [filters, page],
  );
  const issues = useResource(fetchIssues);
  const ingredients = useResource(loadIngredients);
  const [open, setOpen] = useState(false);

  function updateFilters(patch: Partial<IssueFilters>) {
    setFilters((previous) => ({ ...previous, ...patch }));
    setPage(1);
  }

  const filtersActive =
    filters.reason !== "" || filters.dateFrom !== "" || filters.dateTo !== "";
  const items = issues.status === "ready" ? issues.data.items : [];
  const [detailId, setDetailId] = useState<number | null>(null);
  const total = issues.status === "ready" ? issues.data.total : 0;

  return (
    <div className="space-y-5">
      <PageHeader
        title="Phiếu xuất"
        description="Xuất kho thủ công cho hao hụt, hết hạn hoặc hàng hỏng."
        actions={
          <Button onClick={() => setOpen(true)}>
            <PackageMinus aria-hidden />
            Tạo phiếu xuất
          </Button>
        }
      />

      <FilterBar
        active={filtersActive}
        onReset={() => updateFilters(INITIAL_FILTERS)}
      >
        <SelectFilter
          label="Lý do"
          value={filters.reason}
          onChange={(v) => updateFilters({ reason: v })}
          allLabel="Mọi lý do"
          options={ISSUE_REASONS.map((r) => ({ value: r, label: r }))}
        />
        <DateRangeFilter
          from={filters.dateFrom}
          to={filters.dateTo}
          onChange={({ from, to }) =>
            updateFilters({ dateFrom: from, dateTo: to })
          }
        />
      </FilterBar>

      {issues.status === "loading" ? (
        <LoadingState />
      ) : issues.status === "error" ? (
        <ErrorState message={issues.message} onRetry={issues.reload} />
      ) : items.length === 0 && !filtersActive ? (
        <EmptyState
          icon={PackageMinus}
          title="Chưa có phiếu xuất"
          description="Ghi nhận hao hụt, hàng hỏng hoặc hết hạn tại đây."
          action={<Button onClick={() => setOpen(true)}>Tạo phiếu xuất</Button>}
        />
      ) : (
        <>
          <Table>
            <caption className="sr-only">Danh sách phiếu xuất</caption>
            <TableHeader>
              <TableRow>
                <TableHead>Mã phiếu</TableHead>
                <TableHead>Thời điểm</TableHead>
                <TableHead>Lý do</TableHead>
                <TableHead className="text-right">Tổng SL</TableHead>
                <TableHead className="text-right">Số dòng</TableHead>
                <TableHead>Trạng thái</TableHead>
                <TableHead className="text-right">Thao tác</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((it) => (
                <TableRow key={it.MaPhieuXuat}>
                  <TableCell className="font-medium tabular-nums">
                    #{it.MaPhieuXuat}
                  </TableCell>
                  <TableCell>{formatDateTime(it.NgayTao)}</TableCell>
                  <TableCell>{it.LyDo}</TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatNumber(it.TongSoLuong)}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {it.SoDong ?? 0}
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={it.TrangThai} />
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setDetailId(it.MaPhieuXuat)}
                    >
                      Xem
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {items.length === 0 && (
                <TableRow>
                  <TableCell
                    colSpan={7}
                    className="py-8 text-center text-muted"
                  >
                    Không có phiếu xuất nào khớp bộ lọc.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>

          <DataPagination
            page={page}
            pageSize={PAGE_SIZE}
            total={total}
            onPageChange={setPage}
          />
        </>
      )}

      {detailId !== null && (
        <IssueDetailDialog
          issueId={detailId}
          onClose={() => setDetailId(null)}
        />
      )}

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Tạo phiếu xuất</DialogTitle>
          </DialogHeader>
          {ingredients.status === "loading" ? (
            <LoadingState rows={2} />
          ) : ingredients.status === "error" ? (
            <ErrorState
              message={ingredients.message}
              onRetry={ingredients.reload}
            />
          ) : (
            <IssueForm
              ingredients={ingredients.data}
              onCreated={() => {
                setOpen(false);
                issues.reload();
              }}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
