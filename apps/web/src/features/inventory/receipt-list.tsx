"use client";

import { PackagePlus, Truck } from "lucide-react";
import { useCallback, useState } from "react";

import { ConfirmDialog } from "@/components/confirm-dialog";
import { DataPagination } from "@/components/data-pagination";
import {
  DateRangeFilter,
  FilterBar,
  SelectFilter,
} from "@/components/filter-bar";
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { apiFetch } from "@/lib/api-client";
import { formatDateTime } from "@/lib/format";
import { useAction } from "@/lib/use-action";
import { useResource } from "@/lib/use-resource";

import { ReceiptForm } from "./receipt-form";
import type { IngredientOption, Receipt, SupplierOption } from "./types";

const PAGE_SIZE = 20;

const RECEIPT_STATUSES = [
  { value: "Nháp", label: "Nháp" },
  { value: "Đã hủy", label: "Đã hủy" },
];

type ReceiptFilters = {
  supplierId: string;
  status: string;
  dateFrom: string;
  dateTo: string;
};

const INITIAL_FILTERS: ReceiptFilters = {
  supplierId: "",
  status: "",
  dateFrom: "",
  dateTo: "",
};

function queryOf(filters: ReceiptFilters, page: number): string {
  const params = new URLSearchParams();
  if (filters.supplierId) params.set("supplier_id", filters.supplierId);
  if (filters.status) params.set("status", filters.status);
  if (filters.dateFrom) params.set("date_from", filters.dateFrom);
  if (filters.dateTo) params.set("date_to", filters.dateTo);
  params.set("page", String(page));
  params.set("page_size", String(PAGE_SIZE));
  return `/inventory/receipts?${params.toString()}`;
}

const loadIngredients = () =>
  apiFetch<{ items: IngredientOption[] }>("/catalog/ingredients?size=200").then(
    (d) => d.items || [],
  );
const loadSuppliers = () => apiFetch<SupplierOption[]>("/catalog/suppliers");

export function ReceiptList({
  prefillIngredientId,
  onPrefillHandled,
}: {
  prefillIngredientId?: number | null;
  onPrefillHandled?: () => void;
} = {}) {
  const [filters, setFilters] = useState<ReceiptFilters>(INITIAL_FILTERS);
  const [page, setPage] = useState(1);

  const fetchReceipts = useCallback(
    () => apiFetch<{ items: Receipt[]; total: number }>(queryOf(filters, page)),
    [filters, page],
  );
  const receipts = useResource(fetchReceipts);
  const ingredients = useResource(loadIngredients);
  const suppliers = useResource(loadSuppliers);
  const [open, setOpen] = useState(false);
  const [cancelTarget, setCancelTarget] = useState<number | null>(null);
  const cancelAction = useAction();

  function openCreate() {
    setOpen(true);
  }

  function updateFilters(patch: Partial<ReceiptFilters>) {
    setFilters((previous) => ({ ...previous, ...patch }));
    setPage(1);
  }

  const dialogOpen = open || prefillIngredientId != null;
  const filtersActive =
    filters.supplierId !== "" ||
    filters.status !== "" ||
    filters.dateFrom !== "" ||
    filters.dateTo !== "";

  const items = receipts.status === "ready" ? receipts.data.items : [];
  const total = receipts.status === "ready" ? receipts.data.total : 0;
  const supplierName = (id: number | null) =>
    id === null
      ? "—"
      : suppliers.status === "ready"
        ? (suppliers.data.find((s) => s.MaNhaCungCap === id)?.TenNhaCungCap ??
          `#${id}`)
        : `#${id}`;

  async function confirmCancel() {
    if (cancelTarget === null) return;
    const result = await cancelAction.run(
      () =>
        apiFetch(`/inventory/receipts/${cancelTarget}`, { method: "DELETE" }),
      "Đã hủy phiếu nhập.",
    );
    if (result !== undefined) {
      setCancelTarget(null);
      receipts.reload();
    }
  }

  return (
    <div className="space-y-5">
      <PageHeader
        title="Phiếu nhập"
        description="Ghi nhận nhập kho theo nhà cung cấp, quy đổi về đơn vị chuẩn."
        actions={
          <Button onClick={openCreate}>
            <PackagePlus aria-hidden />
            Tạo phiếu nhập
          </Button>
        }
      />

      <FilterBar
        active={filtersActive}
        onReset={() => updateFilters(INITIAL_FILTERS)}
      >
        <SelectFilter
          label="Nhà cung cấp"
          value={filters.supplierId}
          onChange={(v) => updateFilters({ supplierId: v })}
          allLabel="Mọi nhà cung cấp"
          options={
            suppliers.status === "ready"
              ? suppliers.data.map((s) => ({
                  value: String(s.MaNhaCungCap),
                  label: s.TenNhaCungCap,
                }))
              : []
          }
        />
        <SelectFilter
          label="Trạng thái"
          value={filters.status}
          onChange={(v) => updateFilters({ status: v })}
          allLabel="Mọi trạng thái"
          options={RECEIPT_STATUSES}
        />
        <DateRangeFilter
          from={filters.dateFrom}
          to={filters.dateTo}
          onChange={({ from, to }) =>
            updateFilters({ dateFrom: from, dateTo: to })
          }
        />
      </FilterBar>

      {receipts.status === "loading" ? (
        <LoadingState />
      ) : receipts.status === "error" ? (
        <ErrorState message={receipts.message} onRetry={receipts.reload} />
      ) : items.length === 0 && !filtersActive ? (
        <EmptyState
          icon={Truck}
          title="Chưa có phiếu nhập"
          description="Tạo phiếu nhập đầu tiên để bắt đầu theo dõi tồn kho."
          action={<Button onClick={openCreate}>Tạo phiếu nhập</Button>}
        />
      ) : (
        <>
          <Table>
            <caption className="sr-only">Danh sách phiếu nhập</caption>
            <TableHeader>
              <TableRow>
                <TableHead>Mã phiếu</TableHead>
                <TableHead>Nhà cung cấp</TableHead>
                <TableHead>Ngày nhập</TableHead>
                <TableHead>Trạng thái</TableHead>
                <TableHead className="text-right">Thao tác</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((r) => (
                <TableRow key={r.MaPhieuNhap}>
                  <TableCell className="font-medium tabular-nums">
                    #{r.MaPhieuNhap}
                  </TableCell>
                  <TableCell>{supplierName(r.MaNhaCungCap)}</TableCell>
                  <TableCell>{formatDateTime(r.NgayNhap)}</TableCell>
                  <TableCell>
                    <StatusBadge status={r.TrangThai} />
                  </TableCell>
                  <TableCell className="text-right">
                    {r.TrangThai === "Nháp" ? (
                      <Button
                        variant="outlineDanger"
                        size="sm"
                        onClick={() => setCancelTarget(r.MaPhieuNhap)}
                      >
                        Hủy phiếu
                      </Button>
                    ) : null}
                  </TableCell>
                </TableRow>
              ))}
              {items.length === 0 && (
                <TableRow>
                  <TableCell
                    colSpan={5}
                    className="py-8 text-center text-muted"
                  >
                    Không có phiếu nhập nào khớp bộ lọc.
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

      <Dialog
        open={dialogOpen}
        onOpenChange={(next) => {
          setOpen(next);
          if (!next) onPrefillHandled?.();
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Tạo phiếu nhập</DialogTitle>
          </DialogHeader>
          {ingredients.status === "loading" ||
          suppliers.status === "loading" ? (
            <LoadingState rows={2} />
          ) : ingredients.status === "error" ? (
            <ErrorState
              message={ingredients.message}
              onRetry={ingredients.reload}
            />
          ) : suppliers.status === "error" ? (
            <ErrorState
              message={suppliers.message}
              onRetry={suppliers.reload}
            />
          ) : (
            <ReceiptForm
              ingredients={ingredients.data}
              suppliers={suppliers.data}
              prefillIngredientId={prefillIngredientId}
              onCreated={() => {
                setOpen(false);
                onPrefillHandled?.();
                receipts.reload();
              }}
            />
          )}
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={cancelTarget !== null}
        onOpenChange={(next) => {
          if (!next) setCancelTarget(null);
        }}
        title="Hủy phiếu nhập?"
        description="Chỉ hủy được khi lô hàng của phiếu chưa bị xuất dùng."
        confirmLabel="Hủy phiếu"
        danger
        pending={cancelAction.pending}
        onConfirm={confirmCancel}
      />
    </div>
  );
}
