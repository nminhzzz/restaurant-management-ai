"use client";

import { Pencil, Plus, Search, Trash2, Wheat } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { ConfirmDialog } from "@/components/confirm-dialog";
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
import type { Ingredient } from "@/features/catalog/types";
import { useCanWrite } from "@/features/catalog/use-role";
import { ApiError, apiFetch } from "@/lib/api-client";
import { formatNumber } from "@/lib/format";
import { useAction } from "@/lib/use-action";
import { useResource } from "@/lib/use-resource";

const WRITE_ROLES = ["MANAGER", "WAREHOUSE"];

const loadIngredients = () =>
  apiFetch<{ items: Ingredient[] } | Ingredient[]>(
    "/catalog/ingredients?size=200",
  ).then((r) => (Array.isArray(r) ? r : r.items));

function messageOf(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback;
}

type FormValues = {
  TenNguyenLieu: string;
  DonViTinh: string;
  MucTonToiThieu: string;
};

function IngredientFormDialog({
  open,
  onOpenChange,
  title,
  initial,
  unitLocked,
  unitError,
  pending,
  onSubmit,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  initial: FormValues;
  unitLocked: boolean;
  unitError: string | null;
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
          <FormField id="ing-name" label="Tên nguyên liệu">
            <Input
              id="ing-name"
              value={values.TenNguyenLieu}
              onChange={(e) =>
                setValues((v) => ({ ...v, TenNguyenLieu: e.target.value }))
              }
            />
          </FormField>
          <FormField id="ing-unit" label="Đơn vị tính" error={unitError}>
            <Input
              id="ing-unit"
              disabled={unitLocked}
              value={values.DonViTinh}
              onChange={(e) =>
                setValues((v) => ({ ...v, DonViTinh: e.target.value }))
              }
            />
          </FormField>
          <FormField
            id="ing-min"
            label="Mức tồn tối thiểu"
            help="Để trống để dùng mức mặc định của hệ thống."
          >
            <Input
              id="ing-min"
              type="number"
              min={0}
              value={values.MucTonToiThieu}
              onChange={(e) =>
                setValues((v) => ({ ...v, MucTonToiThieu: e.target.value }))
              }
            />
          </FormField>
        </div>
        <DialogFooter>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>
            Quay lại
          </Button>
          <Button
            disabled={
              pending ||
              values.TenNguyenLieu.trim() === "" ||
              values.DonViTinh.trim() === ""
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

const EMPTY_FORM: FormValues = {
  TenNguyenLieu: "",
  DonViTinh: "",
  MucTonToiThieu: "",
};

export function IngredientList() {
  const res = useResource(loadIngredients);
  const canWrite = useCanWrite(WRITE_ROLES);
  const [query, setQuery] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [editIngredient, setEditIngredient] = useState<Ingredient | null>(null);
  const [deleteIngredient, setDeleteIngredient] = useState<Ingredient | null>(
    null,
  );
  const [unitLocked, setUnitLocked] = useState<Record<number, boolean>>({});
  const [unitError, setUnitError] = useState<string | null>(null);
  const [editPending, setEditPending] = useState(false);
  const create = useAction();
  const del = useAction();

  const items = res.status === "ready" ? res.data : [];
  const visible = items.filter((i) =>
    i.TenNguyenLieu.toLowerCase().includes(query.trim().toLowerCase()),
  );

  function handleCreate(values: FormValues) {
    void create.run(async () => {
      await apiFetch("/catalog/ingredients", {
        method: "POST",
        body: {
          TenNguyenLieu: values.TenNguyenLieu.trim(),
          DonViTinh: values.DonViTinh.trim(),
          ...(values.MucTonToiThieu.trim()
            ? { MucTonToiThieu: Number(values.MucTonToiThieu) }
            : {}),
        },
      });
      setCreateOpen(false);
      res.reload();
    }, "Đã thêm nguyên liệu.");
  }

  async function handleEdit(values: FormValues) {
    if (!editIngredient) return;
    const unitChanged = values.DonViTinh.trim() !== editIngredient.DonViTinh;
    setUnitError(null);
    setEditPending(true);
    const body: Record<string, unknown> = {
      TenNguyenLieu: values.TenNguyenLieu.trim(),
      MucTonToiThieu: values.MucTonToiThieu.trim()
        ? Number(values.MucTonToiThieu)
        : null,
    };
    if (unitChanged) body.DonViTinh = values.DonViTinh.trim();

    try {
      await apiFetch(`/catalog/ingredients/${editIngredient.MaNguyenLieu}`, {
        method: "PATCH",
        body,
      });
      toast.success("Đã cập nhật nguyên liệu.");
      setEditIngredient(null);
      res.reload();
    } catch (cause) {
      const message = messageOf(cause, "Không cập nhật được nguyên liệu.");
      if (unitChanged) {
        // The API rejected changing a unit that is already referenced elsewhere;
        // surface it near the field and lock it instead of a generic toast.
        setUnitError(message);
        setUnitLocked((prev) => ({
          ...prev,
          [editIngredient.MaNguyenLieu]: true,
        }));
      } else {
        toast.error(message);
      }
    } finally {
      setEditPending(false);
    }
  }

  function handleDelete() {
    if (!deleteIngredient) return;
    void del.run(async () => {
      await apiFetch(`/catalog/ingredients/${deleteIngredient.MaNguyenLieu}`, {
        method: "DELETE",
      });
      setDeleteIngredient(null);
      res.reload();
    }, "Đã xóa nguyên liệu.");
  }

  const addButton = canWrite ? (
    <Button onClick={() => setCreateOpen(true)}>
      <Plus />
      Thêm nguyên liệu
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
          icon={Wheat}
          title="Chưa có nguyên liệu nào"
          description="Thêm nguyên liệu để dùng cho công thức món và theo dõi tồn kho."
          action={addButton}
        />
      ) : (
        <>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="relative w-full max-w-xs">
              <Search
                className="absolute top-2.5 left-2.5 size-4 text-subtle"
                aria-hidden
              />
              <Input
                type="search"
                aria-label="Tìm nguyên liệu"
                placeholder="Tìm nguyên liệu"
                className="pl-8"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>
            {addButton}
          </div>
          <Table>
            <caption className="sr-only">Danh sách nguyên liệu</caption>
            <TableHeader>
              <TableRow>
                <TableHead>Nguyên liệu</TableHead>
                <TableHead>Đơn vị tính</TableHead>
                <TableHead className="text-right">Mức tồn tối thiểu</TableHead>
                <TableHead className="sr-only">Thao tác</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {visible.map((i) => (
                <TableRow key={i.MaNguyenLieu}>
                  <TableCell className="font-medium">
                    {i.TenNguyenLieu}
                  </TableCell>
                  <TableCell className="text-muted">{i.DonViTinh}</TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatNumber(i.MucTonToiThieu)}
                  </TableCell>
                  <TableCell>
                    {canWrite && (
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label="Sửa nguyên liệu"
                          onClick={() => {
                            setUnitError(null);
                            setEditIngredient(i);
                          }}
                        >
                          <Pencil />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label="Xóa nguyên liệu"
                          onClick={() => setDeleteIngredient(i)}
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
                    colSpan={4}
                    className="py-8 text-center text-muted"
                  >
                    Không có nguyên liệu nào khớp “{query}”.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </>
      )}

      <IngredientFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        title="Thêm nguyên liệu"
        initial={EMPTY_FORM}
        unitLocked={false}
        unitError={null}
        pending={create.pending}
        onSubmit={handleCreate}
      />

      {editIngredient && (
        <IngredientFormDialog
          open
          onOpenChange={(open) => !open && setEditIngredient(null)}
          title="Sửa nguyên liệu"
          initial={{
            TenNguyenLieu: editIngredient.TenNguyenLieu,
            DonViTinh: editIngredient.DonViTinh,
            MucTonToiThieu:
              editIngredient.MucTonToiThieu != null
                ? String(editIngredient.MucTonToiThieu)
                : "",
          }}
          unitLocked={unitLocked[editIngredient.MaNguyenLieu] ?? false}
          unitError={unitError}
          pending={editPending}
          onSubmit={handleEdit}
        />
      )}

      <ConfirmDialog
        open={!!deleteIngredient}
        onOpenChange={(open) => !open && setDeleteIngredient(null)}
        title={`Xóa "${deleteIngredient?.TenNguyenLieu ?? ""}"?`}
        confirmLabel="Xóa"
        danger
        pending={del.pending}
        onConfirm={handleDelete}
      />
    </div>
  );
}
