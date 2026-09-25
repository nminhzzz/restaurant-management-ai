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
import { useAction } from "@/lib/use-action";
import { useResource } from "@/lib/use-resource";

import { ISSUE_REASONS } from "./types";
import type { IngredientOption, StockIssue } from "./types";

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

type DraftLine = { key: string; ingredientId: string; quantity: string };

function emptyLine(): DraftLine {
  return {
    key: Math.random().toString(36).slice(2),
    ingredientId: "",
    quantity: "",
  };
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
  const [lines, setLines] = useState<DraftLine[]>([emptyLine()]);
  const [error, setError] = useState<string | null>(null);

  function updateLine(key: string, patch: Partial<DraftLine>) {
    setLines((prev) =>
      prev.map((l) => (l.key === key ? { ...l, ...patch } : l)),
    );
  }

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
    const result = await run(
      () =>
        apiFetch("/inventory/issues", {
          method: "POST",
          body: {
            reason,
            lines: lines.map((l) => ({
              ingredient_id: Number(l.ingredientId),
              quantity: Number(l.quantity),
            })),
          },
        }),
      "Đã ghi nhận xuất kho.",
    );
    if (result !== undefined) onCreated();
  }

  return (
    <div className="space-y-4">
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

      <div className="space-y-3">
        {lines.map((line, index) => (
          <div
            key={line.key}
            className="grid grid-cols-2 gap-2 rounded-container border border-border p-3 sm:grid-cols-5"
          >
            <div className="col-span-2 sm:col-span-3">
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
            <div className="flex items-end">
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
                <TableHead>Lý do</TableHead>
                <TableHead>Trạng thái</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((it) => (
                <TableRow key={it.MaPhieuXuat}>
                  <TableCell className="font-medium tabular-nums">
                    #{it.MaPhieuXuat}
                  </TableCell>
                  <TableCell>{it.LyDo}</TableCell>
                  <TableCell>
                    <StatusBadge status={it.TrangThai} />
                  </TableCell>
                </TableRow>
              ))}
              {items.length === 0 && (
                <TableRow>
                  <TableCell
                    colSpan={3}
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
