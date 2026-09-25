"use client";

import {
  Eye,
  EyeOff,
  ImageOff,
  Package,
  PackageX,
  Pencil,
  Plus,
  Trash2,
  UtensilsCrossed,
} from "lucide-react";
import { useState } from "react";

import { ConfirmDialog } from "@/components/confirm-dialog";
import { DataPagination } from "@/components/data-pagination";
import { FilterBar, SearchFilter, SelectFilter } from "@/components/filter-bar";
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { DishDetail } from "@/features/catalog/dish-detail";
import type { Dish, Group } from "@/features/catalog/types";
import { useCanWrite } from "@/features/catalog/use-role";
import { apiFetch } from "@/lib/api-client";
import { formatVnd } from "@/lib/format";
import { useAction } from "@/lib/use-action";
import { useClientPagination } from "@/lib/use-client-pagination";
import { useResource } from "@/lib/use-resource";

const WRITE_ROLES = ["MANAGER"];

/** 40px thumbnail; falls back to a plain icon when there is no image or it fails to load. */
function DishThumbnail({
  src,
  alt,
  size = "size-10",
}: {
  src?: string | null;
  alt: string;
  size?: string;
}) {
  const [failed, setFailed] = useState(false);
  if (!src || failed) {
    return (
      <span
        className={`flex ${size} shrink-0 items-center justify-center rounded-control bg-surface-sunken text-subtle`}
      >
        <ImageOff className="size-4" aria-hidden />
      </span>
    );
  }
  return (
    // eslint-disable-next-line @next/next/no-img-element -- external/relative URLs, no remote host config
    <img
      src={src}
      alt={alt}
      className={`${size} shrink-0 rounded-control object-cover`}
      onError={() => setFailed(true)}
    />
  );
}

async function loadCatalog(): Promise<{ dishes: Dish[]; groups: Group[] }> {
  const [page, groups] = await Promise.all([
    apiFetch<{ items: Dish[] }>("/catalog/dishes?size=200"),
    apiFetch<Group[]>("/catalog/groups").catch(() => []),
  ]);
  return { dishes: page.items, groups: Array.isArray(groups) ? groups : [] };
}

type DishFormValues = {
  TenMon: string;
  MaNhomMon: string;
  GiaHienTai: string;
  HinhAnh: string;
};

function DishFormDialog({
  open,
  onOpenChange,
  groups,
  initial,
  title,
  showPrice,
  pending,
  onSubmit,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  groups: Group[];
  initial: DishFormValues;
  title: string;
  showPrice: boolean;
  pending: boolean;
  onSubmit: (values: DishFormValues) => void;
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
          <FormField id="dish-name" label="Tên món">
            <Input
              id="dish-name"
              value={values.TenMon}
              onChange={(e) =>
                setValues((v) => ({ ...v, TenMon: e.target.value }))
              }
            />
          </FormField>
          <FormField id="dish-group" label="Nhóm món">
            <select
              id="dish-group"
              className="flex h-9 w-full rounded-control border border-border bg-surface px-3 py-1 text-sm text-ink focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
              value={values.MaNhomMon}
              onChange={(e) =>
                setValues((v) => ({ ...v, MaNhomMon: e.target.value }))
              }
            >
              <option value="">Chọn nhóm món</option>
              {groups.map((g) => (
                <option key={g.MaNhomMon} value={g.MaNhomMon}>
                  {g.TenNhom}
                </option>
              ))}
            </select>
          </FormField>
          {showPrice && (
            <FormField id="dish-price" label="Giá bán">
              <Input
                id="dish-price"
                type="number"
                min={0}
                value={values.GiaHienTai}
                onChange={(e) =>
                  setValues((v) => ({ ...v, GiaHienTai: e.target.value }))
                }
              />
            </FormField>
          )}
          <FormField
            id="dish-image"
            label="Ảnh món (URL)"
            help="Không bắt buộc."
          >
            <Input
              id="dish-image"
              value={values.HinhAnh}
              onChange={(e) =>
                setValues((v) => ({ ...v, HinhAnh: e.target.value }))
              }
            />
          </FormField>
          {values.HinhAnh.trim() !== "" && (
            <DishThumbnail
              src={values.HinhAnh.trim()}
              alt="Xem trước ảnh món"
              size="size-16"
            />
          )}
        </div>
        <DialogFooter>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>
            Quay lại
          </Button>
          <Button
            disabled={
              pending ||
              values.TenMon.trim() === "" ||
              values.MaNhomMon === "" ||
              (showPrice && values.GiaHienTai.trim() === "")
            }
            onClick={() => onSubmit(values)}
          >
            Lưu
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

const EMPTY_FORM: DishFormValues = {
  TenMon: "",
  MaNhomMon: "",
  GiaHienTai: "",
  HinhAnh: "",
};

export function DishList() {
  const catalog = useResource(loadCatalog);
  const canWrite = useCanWrite(WRITE_ROLES);
  const [query, setQuery] = useState("");
  const [groupFilter, setGroupFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [editDish, setEditDish] = useState<Dish | null>(null);
  const [deleteDish, setDeleteDish] = useState<Dish | null>(null);
  const [detailDish, setDetailDish] = useState<Dish | null>(null);
  const create = useAction();
  const edit = useAction();
  const del = useAction();
  const toggle = useAction();

  const dishes = catalog.status === "ready" ? catalog.data.dishes : null;
  const groups = catalog.status === "ready" ? catalog.data.groups : [];
  const groupName = new Map(groups.map((g) => [g.MaNhomMon, g.TenNhom]));
  const statusOptions = [
    ...new Set((dishes ?? []).map((d) => d.TrangThai)),
  ].map((status) => ({ value: status, label: status }));
  const groupOptions = groups.map((g) => ({
    value: String(g.MaNhomMon),
    label: g.TenNhom,
  }));
  const trimmedQuery = query.trim().toLowerCase();
  const visible = (dishes ?? []).filter(
    (d) =>
      d.TenMon.toLowerCase().includes(trimmedQuery) &&
      (groupFilter === "" || String(d.MaNhomMon ?? "") === groupFilter) &&
      (statusFilter === "" || d.TrangThai === statusFilter),
  );
  const filtersActive =
    query.trim() !== "" || groupFilter !== "" || statusFilter !== "";
  function resetFilters() {
    setQuery("");
    setGroupFilter("");
    setStatusFilter("");
  }
  const pagination = useClientPagination(
    visible,
    JSON.stringify({ trimmedQuery, groupFilter, statusFilter }),
    20,
  );

  function handleCreate(values: DishFormValues) {
    void create.run(async () => {
      await apiFetch("/catalog/dishes", {
        method: "POST",
        body: {
          TenMon: values.TenMon.trim(),
          MaNhomMon: Number(values.MaNhomMon),
          GiaHienTai: Number(values.GiaHienTai),
          ...(values.HinhAnh.trim() ? { HinhAnh: values.HinhAnh.trim() } : {}),
        },
      });
      setCreateOpen(false);
      catalog.reload();
    }, "Đã thêm món.");
  }

  function handleEdit(dish: Dish, values: DishFormValues) {
    void edit.run(async () => {
      await apiFetch(`/catalog/dishes/${dish.MaMon}`, {
        method: "PATCH",
        body: {
          TenMon: values.TenMon.trim(),
          MaNhomMon: Number(values.MaNhomMon),
          HinhAnh: values.HinhAnh.trim() || null,
        },
      });
      setEditDish(null);
      catalog.reload();
    }, "Đã cập nhật món.");
  }

  function handleDelete(dish: Dish) {
    void del.run(async () => {
      await apiFetch(`/catalog/dishes/${dish.MaMon}`, { method: "DELETE" });
      setDeleteDish(null);
      catalog.reload();
    }, "Đã xóa món.");
  }

  function toggleVisibility(dish: Dish, field: "AnThuCong" | "HetNLThuCong") {
    void toggle.run(async () => {
      await apiFetch(`/catalog/dishes/${dish.MaMon}/visibility`, {
        method: "PATCH",
        body: { [field]: !dish[field] },
      });
      catalog.reload();
    });
  }

  const addButton = canWrite ? (
    <Button onClick={() => setCreateOpen(true)}>
      <Plus />
      Thêm món
    </Button>
  ) : undefined;

  return (
    <div className="space-y-5">
      {catalog.status === "loading" ? (
        <LoadingState />
      ) : catalog.status === "error" ? (
        <ErrorState message={catalog.message} onRetry={catalog.reload} />
      ) : !dishes || dishes.length === 0 ? (
        <EmptyState
          icon={UtensilsCrossed}
          title="Chưa có món nào"
          description="Thêm món đầu tiên để thu ngân có thể gọi món trên màn hình bán hàng."
          action={addButton}
        />
      ) : (
        <>
          <div className="flex flex-wrap items-end justify-between gap-3">
            <FilterBar active={filtersActive} onReset={resetFilters}>
              <SearchFilter label="Tìm món" value={query} onChange={setQuery} />
              <SelectFilter
                label="Lọc theo nhóm"
                value={groupFilter}
                onChange={setGroupFilter}
                options={groupOptions}
                allLabel="Tất cả nhóm"
              />
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
          <Table>
            <caption className="sr-only">Danh sách món</caption>
            <TableHeader>
              <TableRow>
                <TableHead>Tên món</TableHead>
                <TableHead>Nhóm</TableHead>
                <TableHead className="text-right">Giá hiện tại</TableHead>
                <TableHead>Trạng thái</TableHead>
                <TableHead className="sr-only">Thao tác</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {pagination.pageItems.map((d) => (
                <TableRow
                  key={d.MaMon}
                  className="cursor-pointer"
                  onClick={() => setDetailDish(d)}
                >
                  <TableCell className="font-medium">
                    <div className="flex items-center gap-2">
                      <DishThumbnail src={d.HinhAnh} alt={d.TenMon} />
                      <span>{d.TenMon}</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-muted">
                    {(d.MaNhomMon != null && groupName.get(d.MaNhomMon)) || ""}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatVnd(d.GiaHienTai)}
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={d.TrangThai} />
                  </TableCell>
                  <TableCell onClick={(e) => e.stopPropagation()}>
                    {canWrite && (
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label="Sửa món"
                          onClick={() => setEditDish(d)}
                        >
                          <Pencil />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label={d.AnThuCong ? "Bỏ ẩn món" : "Ẩn món"}
                          onClick={() => toggleVisibility(d, "AnThuCong")}
                        >
                          {d.AnThuCong ? <EyeOff /> : <Eye />}
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label={
                            d.HetNLThuCong
                              ? "Bỏ đánh dấu hết nguyên liệu"
                              : "Đánh dấu hết nguyên liệu"
                          }
                          onClick={() => toggleVisibility(d, "HetNLThuCong")}
                        >
                          {d.HetNLThuCong ? <Package /> : <PackageX />}
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label="Xóa món"
                          onClick={() => setDeleteDish(d)}
                        >
                          <Trash2 />
                        </Button>
                      </div>
                    )}
                  </TableCell>
                </TableRow>
              ))}
              {visible.length === 0 && (
                <TableRow>
                  <TableCell
                    colSpan={5}
                    className="py-8 text-center text-muted"
                  >
                    Không có món nào khớp bộ lọc.
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

      <DishFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        groups={groups}
        initial={EMPTY_FORM}
        title="Thêm món"
        showPrice
        pending={create.pending}
        onSubmit={handleCreate}
      />

      {editDish && (
        <DishFormDialog
          open
          onOpenChange={(open) => !open && setEditDish(null)}
          groups={groups}
          initial={{
            TenMon: editDish.TenMon,
            MaNhomMon:
              editDish.MaNhomMon != null ? String(editDish.MaNhomMon) : "",
            GiaHienTai: "",
            HinhAnh: editDish.HinhAnh ?? "",
          }}
          title="Sửa món"
          showPrice={false}
          pending={edit.pending}
          onSubmit={(values) => handleEdit(editDish, values)}
        />
      )}

      <ConfirmDialog
        open={!!deleteDish}
        onOpenChange={(open) => !open && setDeleteDish(null)}
        title={`Xóa "${deleteDish?.TenMon ?? ""}"?`}
        description="Món sẽ được ẩn khỏi thực đơn, dữ liệu lịch sử vẫn được giữ lại."
        confirmLabel="Xóa"
        danger
        pending={del.pending}
        onConfirm={() => deleteDish && handleDelete(deleteDish)}
      />

      {detailDish && (
        <DishDetail
          dish={detailDish}
          onOpenChange={(open) => !open && setDetailDish(null)}
          onChanged={catalog.reload}
        />
      )}
    </div>
  );
}
