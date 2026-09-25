"use client";

import {
  ArrowDown,
  ArrowUp,
  FolderPlus,
  Pencil,
  Plus,
  Trash2,
} from "lucide-react";
import { useState } from "react";

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
import type { Group } from "@/features/catalog/types";
import { useCanWrite } from "@/features/catalog/use-role";
import { apiFetch } from "@/lib/api-client";
import { useAction } from "@/lib/use-action";
import { useClientPagination } from "@/lib/use-client-pagination";
import { useResource } from "@/lib/use-resource";

const WRITE_ROLES = ["MANAGER"];

const loadGroups = () =>
  apiFetch<Group[]>("/catalog/groups").then((g) => (Array.isArray(g) ? g : []));

export function GroupList() {
  const groupsRes = useResource(loadGroups);
  const canWrite = useCanWrite(WRITE_ROLES);
  const [createOpen, setCreateOpen] = useState(false);
  const [editGroup, setEditGroup] = useState<Group | null>(null);
  const [deleteGroup, setDeleteGroup] = useState<Group | null>(null);
  const [name, setName] = useState("");
  const [query, setQuery] = useState("");
  const create = useAction();
  const edit = useAction();
  const del = useAction();
  const reorder = useAction();

  const groups = groupsRes.status === "ready" ? groupsRes.data : [];
  const trimmedQuery = query.trim().toLowerCase();
  const visible = groups.filter((g) =>
    g.TenNhom.toLowerCase().includes(trimmedQuery),
  );
  const pagination = useClientPagination(visible, trimmedQuery, 20);

  function handleCreate() {
    void create.run(async () => {
      await apiFetch("/catalog/groups", {
        method: "POST",
        body: { TenNhom: name.trim() },
      });
      setCreateOpen(false);
      setName("");
      groupsRes.reload();
    }, "Đã thêm nhóm món.");
  }

  function handleRename() {
    if (!editGroup) return;
    void edit.run(async () => {
      await apiFetch(`/catalog/groups/${editGroup.MaNhomMon}`, {
        method: "PATCH",
        body: { TenNhom: name.trim() },
      });
      setEditGroup(null);
      setName("");
      groupsRes.reload();
    }, "Đã cập nhật nhóm món.");
  }

  function handleDelete() {
    if (!deleteGroup) return;
    void del.run(async () => {
      await apiFetch(`/catalog/groups/${deleteGroup.MaNhomMon}`, {
        method: "DELETE",
      });
      setDeleteGroup(null);
      groupsRes.reload();
    }, "Đã xóa nhóm món.");
  }

  function move(groupId: number, direction: -1 | 1) {
    const index = groups.findIndex((g) => g.MaNhomMon === groupId);
    const target = index + direction;
    if (index < 0 || target < 0 || target >= groups.length) return;
    const order = groups.map((g) => g.MaNhomMon);
    [order[index], order[target]] = [order[target], order[index]];
    void reorder.run(async () => {
      await apiFetch("/catalog/groups/order", { method: "PUT", body: order });
      groupsRes.reload();
    });
  }

  const addButton = canWrite ? (
    <Button
      onClick={() => {
        setName("");
        setCreateOpen(true);
      }}
    >
      <Plus />
      Thêm nhóm
    </Button>
  ) : undefined;

  return (
    <div className="space-y-4">
      {groupsRes.status === "loading" ? (
        <LoadingState />
      ) : groupsRes.status === "error" ? (
        <ErrorState message={groupsRes.message} onRetry={groupsRes.reload} />
      ) : groups.length === 0 ? (
        <EmptyState
          icon={FolderPlus}
          title="Chưa có nhóm món"
          description="Tạo nhóm để sắp xếp món ăn theo loại."
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
                label="Tìm nhóm"
                value={query}
                onChange={setQuery}
              />
            </FilterBar>
            {addButton}
          </div>
          <ul className="divide-y divide-border rounded-container border border-border bg-surface">
            {pagination.pageItems.map((g) => {
              const fullIndex = groups.findIndex(
                (x) => x.MaNhomMon === g.MaNhomMon,
              );
              return (
                <li
                  key={g.MaNhomMon}
                  className="flex items-center justify-between gap-3 px-4 py-3"
                >
                  <span className="font-medium">{g.TenNhom}</span>
                  {canWrite && (
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label="Di chuyển lên"
                        disabled={fullIndex === 0}
                        onClick={() => move(g.MaNhomMon, -1)}
                      >
                        <ArrowUp />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label="Di chuyển xuống"
                        disabled={fullIndex === groups.length - 1}
                        onClick={() => move(g.MaNhomMon, 1)}
                      >
                        <ArrowDown />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label="Sửa nhóm"
                        onClick={() => {
                          setEditGroup(g);
                          setName(g.TenNhom);
                        }}
                      >
                        <Pencil />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label="Xóa nhóm"
                        onClick={() => {
                          del.clearError();
                          setDeleteGroup(g);
                        }}
                      >
                        <Trash2 />
                      </Button>
                    </div>
                  )}
                </li>
              );
            })}
            {visible.length === 0 && (
              <li className="py-8 text-center text-muted">
                Không có nhóm nào khớp bộ lọc.
              </li>
            )}
          </ul>
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

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Thêm nhóm món</DialogTitle>
          </DialogHeader>
          <FormField id="group-name" label="Tên nhóm">
            <Input
              id="group-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
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
        open={!!editGroup}
        onOpenChange={(open) => !open && setEditGroup(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Sửa nhóm món</DialogTitle>
          </DialogHeader>
          <FormField id="group-edit-name" label="Tên nhóm">
            <Input
              id="group-edit-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </FormField>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setEditGroup(null)}>
              Quay lại
            </Button>
            <Button
              disabled={edit.pending || name.trim() === ""}
              onClick={handleRename}
            >
              Lưu
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={!!deleteGroup}
        onOpenChange={(open) => {
          if (!open) {
            setDeleteGroup(null);
            del.clearError();
          }
        }}
        title={`Xóa nhóm "${deleteGroup?.TenNhom ?? ""}"?`}
        description={del.error ?? "Xóa nhóm không xóa các món đã thuộc nhóm."}
        confirmLabel="Xóa"
        danger
        pending={del.pending}
        onConfirm={handleDelete}
      />
    </div>
  );
}
