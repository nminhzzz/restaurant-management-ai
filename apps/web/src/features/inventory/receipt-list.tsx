"use client";

import { PackagePlus, Truck } from "lucide-react";
import { useState } from "react";

import {
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  StatusBadge,
} from "@/components/page-states";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/confirm-dialog";
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

const loadReceipts = () => apiFetch<Receipt[]>("/inventory/receipts");
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
  const receipts = useResource(loadReceipts);
  const ingredients = useResource(loadIngredients);
  const suppliers = useResource(loadSuppliers);
  const [open, setOpen] = useState(false);
  const [cancelTarget, setCancelTarget] = useState<number | null>(null);
  const cancelAction = useAction();

  function openCreate() {
    setOpen(true);
  }

  const dialogOpen = open || prefillIngredientId != null;

  const items = receipts.status === "ready" ? receipts.data : [];
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

      {receipts.status === "loading" ? (
        <LoadingState />
      ) : receipts.status === "error" ? (
        <ErrorState message={receipts.message} onRetry={receipts.reload} />
      ) : items.length === 0 ? (
        <EmptyState
          icon={Truck}
          title="Chưa có phiếu nhập"
          description="Tạo phiếu nhập đầu tiên để bắt đầu theo dõi tồn kho."
          action={<Button onClick={openCreate}>Tạo phiếu nhập</Button>}
        />
      ) : (
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
          </TableBody>
        </Table>
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
