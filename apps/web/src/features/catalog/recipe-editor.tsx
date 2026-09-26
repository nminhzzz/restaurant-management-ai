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
  const [lines, setLines] = useState<Line[]>([emptyLine()]);
  const [date, setDate] = useState("");
  const [cancelOpen, setCancelOpen] = useState(false);
  const assignAction = useAction();
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

  function items(): RecipeItem[] {
    return lines
      .filter((l) => l.MaNguyenLieu && l.SoLuong.trim() !== "")
      .map((l) => ({
        MaNguyenLieu: Number(l.MaNguyenLieu),
        SoLuong: Number(l.SoLuong),
      }));
  }

  const busy =
    assignAction.pending || scheduleAction.pending || applyNowAction.pending;
  const canSubmit = items().length > 0 && !busy;

  function handleAssign() {
    const payload = items();
    void assignAction.run(async () => {
      await apiFetch(`/catalog/dishes/${dishId}/recipes/assign`, {
        method: "POST",
        body: { items: payload },
      });
      setLines([emptyLine()]);
      onChanged();
    }, "Đã gán công thức.");
  }

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
      setLines([emptyLine()]);
      setDate("");
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
      setLines([emptyLine()]);
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

      {canWrite && (
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
          </div>

          <div className="flex flex-wrap items-end gap-3">
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
            <Button
              variant="secondary"
              disabled={!canSubmit}
              onClick={handleAssign}
            >
              Gán công thức lần đầu
            </Button>
            <Button
              variant="secondary"
              disabled={!canSubmit}
              onClick={handleSchedule}
            >
              Lên lịch thay đổi
            </Button>
            <Button disabled={!canSubmit} onClick={handleApplyNow}>
              Áp dụng ngay
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
