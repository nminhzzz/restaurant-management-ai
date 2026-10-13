"use client";

import { DoorOpen, LayoutGrid, Pencil, Plus, Trash2 } from "lucide-react";
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
const RELEASE_ROLES = ["MANAGER", "CASHIER"];
const OCCUPIED = "Đang phục vụ";

const loadTables = () =>
  apiFetch<DiningTable[]>("/catalog/tables").then((t) =>
    Array.isArray(t) ? t : [],
  );

export function TableList() {
  const res = useResource(loadTables);
  const canWrite = useCanWrite(WRITE_ROLES);
  const canRelease = useCanWrite(RELEASE_ROLES);
  const [createOpen, setCreateOpen] = useState(false);
  const [editTable, setEditTable] = useState<DiningTable | null>(null);
  const [name, setName] = useState("");
  const [seats, setSeats] = useState("");
  const [deleteTable, setDeleteTable] = useState<DiningTable | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const create = useAction();
  const del = useAction();
  const edit = useAction();
  const release = useAction();

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
          ...(seats.trim() ? { SoChoNgoi: Number(seats) } : {}),
        },
      });
      setCreateOpen(false);
      setName("");
      setSeats("");
      res.reload();
    }, "Đã thêm bàn.");
  }

  function handleEdit() {
    if (!editTable) return;
    void edit.run(async () => {
      await apiFetch(`/catalog/tables/${editTable.MaBan}`, {
        method: "PATCH",
        body: {
          TenBan: name.trim(),
          ...(seats.trim() ? { SoChoNgoi: Number(seats) } : {}),
        },
      });
      setEditTable(null);
      res.reload();
    }, "Đã cập nhật bàn.");
  }

  function handleRelease(table: DiningTable) {
    void release.run(async () => {
      await apiFetch(`/catalog/tables/${table.MaBan}/release`, {
        method: "POST",
        body:
          table.MaOrderDangPhucVu != null
            ? { MaOrder: table.MaOrderDangPhucVu }
            : {},
      });
      res.reload();
    }, `Đã trả ${table.TenBan}.`);
  }

  const seatsInvalid =
    seats.trim() !== "" &&
    !(
      Number.isInteger(Number(seats)) &&
      Number(seats) >= 1 &&
      Number(seats) <= 1000
    );

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
        setSeats("");
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
                {t.SoChoNgoi != null && (
                  <span className="text-xs text-muted">
                    {t.SoChoNgoi} chỗ ngồi
                  </span>
                )}
                {t.TrangThai ? <StatusBadge status={t.TrangThai} /> : null}
                {canRelease && t.TrangThai === OCCUPIED && (
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={release.pending}
                    aria-label={`Trả bàn ${t.TenBan}`}
                    onClick={() => handleRelease(t)}
                  >
                    <DoorOpen />
                    Trả bàn
                  </Button>
                )}
                {canWrite && (
                  <div className="flex justify-end gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      aria-label={`Sửa bàn ${t.TenBan}`}
                      onClick={() => {
                        setName(t.TenBan);
                        setSeats(
                          t.SoChoNgoi != null ? String(t.SoChoNgoi) : "",
                        );
                        setEditTable(t);
                      }}
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

      <Dialog
        open={createOpen || editTable !== null}
        onOpenChange={(open) => {
          if (!open) {
            setCreateOpen(false);
            setEditTable(null);
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editTable ? "Sửa bàn" : "Thêm bàn"}</DialogTitle>
          </DialogHeader>
          <FormField id="table-name" label="Tên bàn">
            <Input
              id="table-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </FormField>
          <FormField
            id="table-seats"
            label="Số chỗ ngồi"
            help="Không bắt buộc."
            error={seatsInvalid ? "Nhập số nguyên từ 1 đến 1000." : null}
          >
            <Input
              id="table-seats"
              inputMode="numeric"
              value={seats}
              onChange={(e) => setSeats(e.target.value)}
            />
          </FormField>
          <DialogFooter>
            <Button
              variant="secondary"
              onClick={() => {
                setCreateOpen(false);
                setEditTable(null);
              }}
            >
              Quay lại
            </Button>
            <Button
              disabled={
                create.pending ||
                edit.pending ||
                name.trim() === "" ||
                seatsInvalid
              }
              onClick={editTable ? handleEdit : handleCreate}
            >
              Lưu
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
