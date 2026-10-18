"use client";

import { LayoutGrid, Pencil, Plus, Trash2 } from "lucide-react";
import { useState } from "react";

import { ConfirmDialog } from "@/components/confirm-dialog";
import { FilterBar, SelectFilter } from "@/components/filter-bar";
import { FormField } from "@/components/form-field";
import {
  EmptyState,
  ErrorState,
  LoadingState,
  StatusBadge,
} from "@/components/page-states";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import type { DiningTable } from "@/features/catalog/types";
import { useCanWrite } from "@/features/catalog/use-role";
import { apiFetch } from "@/lib/api-client";
import { useAction } from "@/lib/use-action";
import { useResource } from "@/lib/use-resource";

const WRITE_ROLES = ["MANAGER"];

const loadTables = () =>
  apiFetch<DiningTable[]>("/catalog/tables").then((t) =>
    Array.isArray(t) ? t : [],
  );

export function TableList() {
  const res = useResource(loadTables);
  const canWrite = useCanWrite(WRITE_ROLES);
  const [createOpen, setCreateOpen] = useState(false);
  const [name, setName] = useState("");
  const [area, setArea] = useState("");
  const [capacity, setCapacity] = useState("");
  const [editTable, setEditTable] = useState<DiningTable | null>(null);
  const [editName, setEditName] = useState("");
  const [editArea, setEditArea] = useState("");
  const [editCapacity, setEditCapacity] = useState("");
  const [deleteTable, setDeleteTable] = useState<DiningTable | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const create = useAction();
  const edit = useAction();
  const del = useAction();

  const tables = res.status === "ready" ? res.data : [];
  const statusOptions = [
    ...new Set(tables.map((t) => t.TrangThai).filter((s): s is string => !!s)),
  ].map((status) => ({ value: status, label: status }));
  const visible = tables.filter(
    (t) => statusFilter === "" || t.TrangThai === statusFilter,
  );

  function handleCreate() {
    void create.run(async () => {
      await apiFetch("/catalog/tables", {
        method: "POST",
        body: {
          TenBan: name.trim(),
          ...(area.trim() ? { KhuVuc: area.trim() } : {}),
          ...(capacity.trim() ? { SoChoNgoi: Number(capacity) } : {}),
        },
      });
      setCreateOpen(false);
      setName("");
      setArea("");
      setCapacity("");
      res.reload();
    }, "Đã thêm bàn.");
  }

  function openEdit(table: DiningTable) {
    setEditTable(table);
    setEditName(table.TenBan);
    setEditArea(table.KhuVuc ?? "");
    setEditCapacity(table.SoChoNgoi != null ? String(table.SoChoNgoi) : "");
  }

  function handleEdit() {
    if (!editTable) return;
    void edit.run(async () => {
      await apiFetch(`/catalog/tables/${editTable.MaBan}`, {
        method: "PATCH",
        body: {
          TenBan: editName.trim(),
          KhuVuc: editArea.trim() || null,
          SoChoNgoi: editCapacity.trim() ? Number(editCapacity) : null,
        },
      });
      setEditTable(null);
      res.reload();
    }, "Đã cập nhật bàn.");
  }

  function handleDelete() {
    if (!deleteTable) return;
    void del.run(async () => {
      await apiFetch(`/catalog/tables/${deleteTable.MaBan}`, {
        method: "DELETE",
      });
      setDeleteTable(null);
      res.reload();
    }, "Đã xóa bàn.");
  }

  const addButton = canWrite ? (
    <Button
      onClick={() => {
        setName("");
        setCreateOpen(true);
      }}
    >
      <Plus />
      Thêm bàn
    </Button>
  ) : undefined;

  return (
    <div className="space-y-4">
      {res.status === "loading" ? (
        <LoadingState />
      ) : res.status === "error" ? (
        <ErrorState message={res.message} onRetry={res.reload} />
      ) : tables.length === 0 ? (
        <EmptyState
          icon={LayoutGrid}
          title="Chưa có bàn nào"
          description="Thêm bàn để mở order tại chỗ."
          action={addButton}
        />
      ) : (
        <>
          <div className="flex flex-wrap items-end justify-between gap-3">
            <FilterBar
              active={statusFilter !== ""}
              onReset={() => setStatusFilter("")}
            >
              <SelectFilter
                label="Trạng thái"
                value={statusFilter}
                onChange={setStatusFilter}
                options={statusOptions}
                allLabel="Tất cả trạng thái"
              />
            </FilterBar>
            {addButton}
          </div>
          <div className="flex flex-wrap gap-3">
            {visible.length === 0 && (
              <p className="py-8 text-center text-muted">
                Không có bàn nào khớp bộ lọc.
              </p>
            )}
            {visible.map((t) => (
              <div
                key={t.MaBan}
                className="flex min-w-32 flex-col gap-2 rounded-container border border-border bg-surface px-4 py-3"
              >
                <span className="font-medium">{t.TenBan}</span>
                {t.TrangThai ? <StatusBadge status={t.TrangThai} /> : null}
                {(t.KhuVuc || t.SoChoNgoi) && (
                  <span className="text-xs text-muted">
                    {[t.KhuVuc, t.SoChoNgoi ? `${t.SoChoNgoi} chỗ` : null]
                      .filter(Boolean)
                      .join(" · ")}
                  </span>
                )}
                {canWrite && (
                  <div className="flex justify-end gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      aria-label={`Sửa bàn ${t.TenBan}`}
                      onClick={() => openEdit(t)}
                    >
                      <Pencil />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-danger-fg"
                      aria-label={`Xóa bàn ${t.TenBan}`}
                      onClick={() => setDeleteTable(t)}
                    >
                      <Trash2 />
                    </Button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Thêm bàn</DialogTitle>
          </DialogHeader>
          <FormField id="table-name" label="Tên bàn">
            <Input
              id="table-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </FormField>
          <FormField id="table-area" label="Khu vực">
            <Input
              id="table-area"
              value={area}
              onChange={(e) => setArea(e.target.value)}
            />
          </FormField>
          <FormField id="table-capacity" label="Số chỗ ngồi">
            <Input
              id="table-capacity"
              type="number"
              min={0}
              value={capacity}
              onChange={(e) => setCapacity(e.target.value)}
            />
          </FormField>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setCreateOpen(false)}>
              Quay lại
            </Button>
            <Button
              disabled={create.pending || name.trim() === ""}
              onClick={handleCreate}
            >
              Lưu
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={!!editTable}
        onOpenChange={(open) => !open && setEditTable(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Sửa bàn {editTable?.TenBan}</DialogTitle>
          </DialogHeader>
          <FormField id="table-edit-name" label="Tên bàn">
            <Input
              id="table-edit-name"
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
            />
          </FormField>
          <FormField id="table-edit-area" label="Khu vực">
            <Input
              id="table-edit-area"
              value={editArea}
              onChange={(e) => setEditArea(e.target.value)}
            />
          </FormField>
          <FormField id="table-edit-capacity" label="Số chỗ ngồi">
            <Input
              id="table-edit-capacity"
              type="number"
              min={0}
              value={editCapacity}
              onChange={(e) => setEditCapacity(e.target.value)}
            />
          </FormField>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setEditTable(null)}>
              Quay lại
            </Button>
            <Button
              disabled={edit.pending || editName.trim() === ""}
              onClick={handleEdit}
            >
              Lưu thay đổi
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={!!deleteTable}
        onOpenChange={(open) => {
          if (!open) {
            setDeleteTable(null);
            del.clearError();
          }
        }}
        title={`Xóa "${deleteTable?.TenBan ?? ""}"?`}
        description={del.error ?? "Không thể xóa bàn đang được sử dụng."}
        confirmLabel="Xóa"
        danger
        pending={del.pending}
        onConfirm={handleDelete}
      />
    </div>
  );
}
