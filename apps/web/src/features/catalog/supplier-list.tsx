"use client";

import { Building2, Eye, Pencil, Plus, Trash2 } from "lucide-react";
import { useCallback, useState } from "react";

import { ConfirmDialog } from "@/components/confirm-dialog";
import { DataPagination } from "@/components/data-pagination";
import { FilterBar, SearchFilter } from "@/components/filter-bar";
import { FormField } from "@/components/form-field";
import { EmptyState, ErrorState, LoadingState } from "@/components/page-states";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { Supplier } from "@/features/catalog/types";
import { useCanWrite } from "@/features/catalog/use-role";
import { apiFetch } from "@/lib/api-client";
import { useAction } from "@/lib/use-action";
import { useClientPagination } from "@/lib/use-client-pagination";
import { useResource } from "@/lib/use-resource";

const WRITE_ROLES = ["MANAGER", "WAREHOUSE"];

const loadSuppliers = () =>
  apiFetch<{ items: Supplier[] } | Supplier[]>("/catalog/suppliers").then(
    (r) => (Array.isArray(r) ? r : r.items),
  );

type FormValues = { TenNhaCungCap: string; SoDienThoai: string };

function SupplierFormDialog({
  open,
  onOpenChange,
  title,
  initial,
  pending,
  onSubmit,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  initial: FormValues;
  pending: boolean;
  onSubmit: (values: FormValues) => void;
}) {
  const [values, setValues] = useState(initial);

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (next) setValues(initial);
        onOpenChange(next);
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <FormField id="supplier-name" label="Tên nhà cung cấp">
            <Input
              id="supplier-name"
              value={values.TenNhaCungCap}
              onChange={(e) =>
                setValues((v) => ({ ...v, TenNhaCungCap: e.target.value }))
              }
            />
          </FormField>
          <FormField id="supplier-phone" label="Số điện thoại">
            <Input
              id="supplier-phone"
              value={values.SoDienThoai}
              onChange={(e) =>
                setValues((v) => ({ ...v, SoDienThoai: e.target.value }))
              }
            />
          </FormField>
        </div>
        <DialogFooter>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>
            Quay lại
          </Button>
          <Button
            disabled={pending || values.TenNhaCungCap.trim() === ""}
            onClick={() => onSubmit(values)}
          >
            Lưu
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function SupplierDetailDialog({
  supplierId,
  onOpenChange,
}: {
  supplierId: number;
  onOpenChange: (open: boolean) => void;
}) {
  const fetchDetail = useCallback(
    () => apiFetch<Supplier>(`/catalog/suppliers/${supplierId}`),
    [supplierId],
  );
  const detail = useResource(fetchDetail);

  return (
    <Dialog open onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Lịch sử nhập hàng</DialogTitle>
        </DialogHeader>
        {detail.status === "loading" ? (
          <LoadingState rows={3} />
        ) : detail.status === "error" ? (
          <ErrorState message={detail.message} onRetry={detail.reload} />
        ) : (detail.data.PhieuNhap ?? []).length === 0 ? (
          <p className="text-muted">
            Chưa có phiếu nhập nào từ nhà cung cấp này.
          </p>
        ) : (
          <ul className="space-y-1.5">
            {(detail.data.PhieuNhap ?? []).map((r) => (
              <li
                key={r.MaPhieuNhap}
                className="rounded-control border border-border px-3 py-2"
              >
                Phiếu nhập #{r.MaPhieuNhap}
              </li>
            ))}
          </ul>
        )}
      </DialogContent>
    </Dialog>
  );
}

const EMPTY_FORM: FormValues = { TenNhaCungCap: "", SoDienThoai: "" };

export function SupplierList() {
  const res = useResource(loadSuppliers);
  const canWrite = useCanWrite(WRITE_ROLES);
  const [query, setQuery] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [editSupplier, setEditSupplier] = useState<Supplier | null>(null);
  const [deleteSupplier, setDeleteSupplier] = useState<Supplier | null>(null);
  const [detailId, setDetailId] = useState<number | null>(null);
  const create = useAction();
  const edit = useAction();
  const del = useAction();

  const items = res.status === "ready" ? res.data : [];
  const trimmedQuery = query.trim().toLowerCase();
  const visible = items.filter(
    (s) =>
      s.TenNhaCungCap.toLowerCase().includes(trimmedQuery) ||
      (s.SoDienThoai ?? "").toLowerCase().includes(trimmedQuery),
  );
  const pagination = useClientPagination(visible, trimmedQuery, 20);

  function handleCreate(values: FormValues) {
    void create.run(async () => {
      await apiFetch("/catalog/suppliers", {
        method: "POST",
        body: {
          TenNhaCungCap: values.TenNhaCungCap.trim(),
          SoDienThoai: values.SoDienThoai.trim() || undefined,
        },
      });
      setCreateOpen(false);
      res.reload();
    }, "Đã thêm nhà cung cấp.");
  }

  function handleEdit(values: FormValues) {
    if (!editSupplier) return;
    void edit.run(async () => {
      await apiFetch(`/catalog/suppliers/${editSupplier.MaNhaCungCap}`, {
        method: "PATCH",
        body: {
          TenNhaCungCap: values.TenNhaCungCap.trim(),
          SoDienThoai: values.SoDienThoai.trim() || undefined,
        },
      });
      setEditSupplier(null);
      res.reload();
    }, "Đã cập nhật nhà cung cấp.");
  }

  function handleDelete() {
    if (!deleteSupplier) return;
    void del.run(async () => {
      await apiFetch(`/catalog/suppliers/${deleteSupplier.MaNhaCungCap}`, {
        method: "DELETE",
      });
      setDeleteSupplier(null);
      res.reload();
    }, "Đã xóa nhà cung cấp.");
  }

  const addButton = canWrite ? (
    <Button onClick={() => setCreateOpen(true)}>
      <Plus />
      Thêm nhà cung cấp
    </Button>
  ) : undefined;

  return (
    <div className="space-y-4">
      {res.status === "loading" ? (
        <LoadingState />
      ) : res.status === "error" ? (
        <ErrorState message={res.message} onRetry={res.reload} />
      ) : items.length === 0 ? (
        <EmptyState
          icon={Building2}
          title="Chưa có nhà cung cấp nào"
          description="Thêm nhà cung cấp để ghi nhận phiếu nhập nguyên liệu."
          action={addButton}
        />
      ) : (
        <>
          <div className="flex flex-wrap items-end justify-between gap-3">
            <FilterBar
              active={query.trim() !== ""}
              onReset={() => setQuery("")}
            >
              <SearchFilter
                label="Tìm nhà cung cấp"
                value={query}
                onChange={setQuery}
              />
            </FilterBar>
            {addButton}
          </div>
          <Table>
            <caption className="sr-only">Danh sách nhà cung cấp</caption>
            <TableHeader>
              <TableRow>
                <TableHead>Tên nhà cung cấp</TableHead>
                <TableHead>Số điện thoại</TableHead>
                <TableHead className="sr-only">Thao tác</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {pagination.pageItems.map((s) => (
                <TableRow key={s.MaNhaCungCap}>
                  <TableCell className="font-medium">
                    {s.TenNhaCungCap}
                  </TableCell>
                  <TableCell className="text-muted">
                    {s.SoDienThoai || ""}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label="Xem lịch sử nhập hàng"
                        onClick={() => setDetailId(s.MaNhaCungCap)}
                      >
                        <Eye />
                      </Button>
                      {canWrite && (
                        <>
                          <Button
                            variant="ghost"
                            size="icon"
                            aria-label="Sửa nhà cung cấp"
                            onClick={() => setEditSupplier(s)}
                          >
                            <Pencil />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            aria-label="Xóa nhà cung cấp"
                            onClick={() => setDeleteSupplier(s)}
                          >
                            <Trash2 />
                          </Button>
                        </>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              {visible.length === 0 && (
                <TableRow>
                  <TableCell
                    colSpan={3}
                    className="py-8 text-center text-muted"
                  >
                    Không có nhà cung cấp nào khớp bộ lọc.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
          {visible.length > 0 && (
            <DataPagination
              page={pagination.page}
              pageSize={pagination.pageSize}
              total={pagination.total}
              onPageChange={pagination.setPage}
              onPageSizeChange={pagination.setPageSize}
            />
          )}
        </>
      )}

      <SupplierFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        title="Thêm nhà cung cấp"
        initial={EMPTY_FORM}
        pending={create.pending}
        onSubmit={handleCreate}
      />

      {editSupplier && (
        <SupplierFormDialog
          open
          onOpenChange={(open) => !open && setEditSupplier(null)}
          title="Sửa nhà cung cấp"
          initial={{
            TenNhaCungCap: editSupplier.TenNhaCungCap,
            SoDienThoai: editSupplier.SoDienThoai ?? "",
          }}
          pending={edit.pending}
          onSubmit={handleEdit}
        />
      )}

      <ConfirmDialog
        open={!!deleteSupplier}
        onOpenChange={(open) => !open && setDeleteSupplier(null)}
        title={`Xóa "${deleteSupplier?.TenNhaCungCap ?? ""}"?`}
        confirmLabel="Xóa"
        danger
        pending={del.pending}
        onConfirm={handleDelete}
      />

      {detailId !== null && (
        <SupplierDetailDialog
          supplierId={detailId}
          onOpenChange={(open) => !open && setDetailId(null)}
        />
      )}
    </div>
  );
}
