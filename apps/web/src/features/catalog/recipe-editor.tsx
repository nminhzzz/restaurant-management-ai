"use client";

import { Plus, Trash2 } from "lucide-react";
import { useState } from "react";

import { ConfirmDialog } from "@/components/confirm-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type {
  Ingredient,
  RecipeItem,
  RecipeVersion,
} from "@/features/catalog/types";
import { apiFetch } from "@/lib/api-client";
import { formatDate } from "@/lib/format";
import { useAction } from "@/lib/use-action";
import { cn } from "@/lib/utils";

const SELECT_CLASS =
  "flex h-9 w-56 rounded-control border border-border-strong bg-surface px-3 py-1 text-sm text-ink hover:border-ink focus-visible:border-primary focus-visible:ring-1 focus-visible:ring-primary focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50";

type Line = { id: number; MaNguyenLieu: string; SoLuong: string };

let nextLineId = 0;

function emptyLine(): Line {
  return { id: nextLineId++, MaNguyenLieu: "", SoLuong: "" };
}

function RecipeLines({ recipe }: { recipe: RecipeVersion }) {
  return (
    <p className="text-xs text-subtle">
      {recipe.items
        .map((it) => `${it.TenNguyenLieu} (${it.SoLuong} ${it.DonViTinh})`)
        .join(", ")}
    </p>
  );
}

export function RecipeEditor({
  dishId,
  ingredients,
  canWrite,
  currentRecipe,
  pendingRecipe,
  history,
  onChanged,
}: {
  dishId: number;
  ingredients: Ingredient[];
  canWrite: boolean;
  currentRecipe: RecipeVersion | null;
  pendingRecipe: RecipeVersion | null;
  history: RecipeVersion[];
  onChanged: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [lines, setLines] = useState<Line[]>([emptyLine()]);
  const [date, setDate] = useState("");
  const [cancelOpen, setCancelOpen] = useState(false);
  const scheduleAction = useAction();
  const applyNowAction = useAction();
  const cancelAction = useAction();

  function updateLine(id: number, patch: Partial<Line>) {
    setLines((prev) => prev.map((l) => (l.id === id ? { ...l, ...patch } : l)));
  }
  function addLine() {
    setLines((prev) => [...prev, emptyLine()]);
  }
  function removeLine(id: number) {
    setLines((prev) =>
      prev.length > 1 ? prev.filter((l) => l.id !== id) : prev,
    );
  }

  function startEditing() {
    const base = pendingRecipe ?? currentRecipe;
    setLines(
      base && base.items.length > 0
        ? base.items.map((it) => ({
            id: nextLineId++,
            MaNguyenLieu: String(it.MaNguyenLieu),
            SoLuong: String(it.SoLuong),
          }))
        : [emptyLine()],
    );
    setDate("");
    setEditing(true);
  }

  function stopEditing() {
    setLines([emptyLine()]);
    setDate("");
    setEditing(false);
  }

  function unitOf(ingredientId: string): string {
    return (
      ingredients.find((i) => String(i.MaNguyenLieu) === ingredientId)
        ?.DonViTinh ?? ""
    );
  }

  function items(): RecipeItem[] {
    return lines
      .filter((l) => l.MaNguyenLieu && l.SoLuong.trim() !== "")
      .map((l) => ({
        MaNguyenLieu: Number(l.MaNguyenLieu),
        SoLuong: Number(l.SoLuong),
      }));
  }

  const busy = scheduleAction.pending || applyNowAction.pending;
  const chosen = lines.map((l) => l.MaNguyenLieu).filter((v) => v !== "");
  const hasDuplicate = new Set(chosen).size !== chosen.length;
  const hasBadQuantity = lines.some((l) => {
    if (l.MaNguyenLieu === "") return false;
    const qty = Number(l.SoLuong);
    return l.SoLuong.trim() === "" || !Number.isFinite(qty) || qty <= 0;
  });
  const canSubmit =
    items().length > 0 && !busy && !hasDuplicate && !hasBadQuantity;

  function handleSchedule() {
    const payload = items();
    void scheduleAction.run(async () => {
      await apiFetch(`/catalog/dishes/${dishId}/recipes/schedule`, {
        method: "POST",
        body: {
          items: payload,
          ...(date ? { BusinessDateApDung: date } : {}),
        },
      });
      stopEditing();
      onChanged();
    }, "Đã lên lịch thay đổi công thức.");
  }

  function handleApplyNow() {
    const payload = items();
    void applyNowAction.run(async () => {
      await apiFetch(`/catalog/dishes/${dishId}/recipes/apply-now`, {
        method: "POST",
        body: { items: payload },
      });
      stopEditing();
      onChanged();
    }, "Đã áp dụng công thức ngay.");
  }

  function handleCancelPending() {
    if (!pendingRecipe) {
      setCancelOpen(false);
      return;
    }
    void cancelAction.run(async () => {
      await apiFetch(`/catalog/recipes/${pendingRecipe.MaCongThuc}`, {
        method: "DELETE",
      });
      setCancelOpen(false);
      onChanged();
    }, "Đã hủy công thức đang chờ áp dụng.");
  }

  return (
    <div className="space-y-4">
      {currentRecipe && (
        <div className="rounded-control border border-border bg-surface-sunken px-3 py-2">
          <p className="font-medium">Công thức hiện tại</p>
          <RecipeLines recipe={currentRecipe} />
        </div>
      )}

      {pendingRecipe && (
        <div className="flex flex-wrap items-center justify-between gap-2 rounded-control border border-dashed border-border-strong bg-surface-sunken px-3 py-2">
          <div>
            <p className="font-medium">Công thức đang chờ áp dụng</p>
            <p className="text-xs text-subtle">
              {`Áp dụng từ ${formatDate(pendingRecipe.BusinessDateApDung)}`}
              {" · "}
              {pendingRecipe.items
                .map((it) => `${it.TenNguyenLieu} (${it.SoLuong})`)
                .join(", ")}
            </p>
          </div>
          {canWrite && (
            <Button
              variant="outlineDanger"
              size="sm"
              onClick={() => setCancelOpen(true)}
            >
              Hủy lịch
            </Button>
          )}
        </div>
      )}

      {history.length > 0 && (
        <ul className="space-y-1 text-xs text-subtle">
          {history.map((r) => (
            <li key={r.MaCongThuc}>
              {formatDate(r.BusinessDateApDung)} · {r.TrangThai}
            </li>
          ))}
        </ul>
      )}

      {canWrite && !editing && (
        <Button variant="secondary" size="sm" onClick={startEditing}>
          {currentRecipe || pendingRecipe ? "Sửa công thức" : "Thêm công thức"}
        </Button>
      )}

      {canWrite && editing && (
        <div className="space-y-3">
          <div className="space-y-2">
            {lines.map((line) => (
              <div key={line.id} className="flex flex-wrap items-center gap-2">
                <select
                  aria-label="Nguyên liệu"
                  className={cn(SELECT_CLASS)}
                  value={line.MaNguyenLieu}
                  onChange={(e) =>
                    updateLine(line.id, { MaNguyenLieu: e.target.value })
                  }
                >
                  <option value="">Chọn nguyên liệu</option>
                  {ingredients.map((i) => (
                    <option key={i.MaNguyenLieu} value={i.MaNguyenLieu}>
                      {i.TenNguyenLieu} ({i.DonViTinh})
                    </option>
                  ))}
                </select>
                <Input
                  type="number"
                  min={0}
                  step="any"
                  aria-label="Số lượng"
                  className="w-28"
                  value={line.SoLuong}
                  onChange={(e) =>
                    updateLine(line.id, { SoLuong: e.target.value })
                  }
                />
                <span className="min-w-8 text-sm text-subtle">
                  {unitOf(line.MaNguyenLieu)}
                </span>
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label="Xóa dòng nguyên liệu"
                  onClick={() => removeLine(line.id)}
                >
                  <Trash2 />
                </Button>
              </div>
            ))}
            <Button variant="secondary" size="sm" onClick={addLine}>
              <Plus />
              Thêm nguyên liệu
            </Button>
            {hasBadQuantity && (
              <p role="alert" className="text-sm text-danger">
                Mỗi nguyên liệu cần số lượng lớn hơn 0; số thập phân dùng dấu
                chấm, ví dụ 0.15.
              </p>
            )}
            {hasDuplicate && (
              <p role="alert" className="text-sm text-danger">
                Có nguyên liệu bị chọn hai lần. Hãy gộp số lượng vào một dòng.
              </p>
            )}
          </div>

          <div className="flex flex-wrap items-end gap-3">
            {currentRecipe && (
              <div className="space-y-1.5">
                <Label htmlFor="recipe-date">
                  Business Date áp dụng (lên lịch)
                </Label>
                <Input
                  id="recipe-date"
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                />
              </div>
            )}
            {currentRecipe && (
              <Button
                variant="secondary"
                disabled={!canSubmit}
                onClick={handleSchedule}
              >
                Lên lịch thay đổi
              </Button>
            )}
            <Button disabled={!canSubmit} onClick={handleApplyNow}>
              Áp dụng ngay
            </Button>
            <Button variant="ghost" disabled={busy} onClick={stopEditing}>
              Hủy
            </Button>
          </div>
        </div>
      )}

      <ConfirmDialog
        open={cancelOpen}
        onOpenChange={setCancelOpen}
        title="Hủy công thức đang chờ áp dụng?"
        confirmLabel="Hủy lịch"
        danger
        pending={cancelAction.pending}
        onConfirm={handleCancelPending}
      />
    </div>
  );
}
