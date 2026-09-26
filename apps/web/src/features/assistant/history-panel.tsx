"use client";

import { Plus } from "lucide-react";
import { useCallback } from "react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api-client";
import { useResource } from "@/lib/use-resource";
import { cn } from "@/lib/utils";
import type { SessionSummary } from "@/types/api";

const GROUPS = ["Hôm nay", "Hôm qua", "7 ngày trước", "Cũ hơn"] as const;

function startOfDay(d: Date): number {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
}

export function groupLabel(iso: string, now: Date): (typeof GROUPS)[number] {
  const days = Math.round((startOfDay(now) - startOfDay(new Date(iso))) / 86_400_000);
  if (days <= 0) return "Hôm nay";
  if (days === 1) return "Hôm qua";
  if (days <= 7) return "7 ngày trước";
  return "Cũ hơn";
}

function timeOf(iso: string, group: string): string {
  const d = new Date(iso);
  return group === "Hôm nay" || group === "Hôm qua"
    ? d.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" })
    : d.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit" });
}

export function HistoryPanel({ activeId, refreshKey, onSelect, onNew }: {
  activeId: number | null;
  refreshKey: number;
  onSelect: (id: number) => void;
  onNew: () => void;
}) {
  const fetcher = useCallback(
    () => apiFetch<{ items: SessionSummary[] }>(`/assistant/sessions?size=50&v=${refreshKey}`),
    [refreshKey],
  );
  const history = useResource(fetcher);
  const now = new Date();

  return (
    <div className="flex h-full min-h-0 flex-col bg-surface">
      <div className="grid gap-2.5 border-b border-border p-3.5">
        <h2 className="text-[15px] font-bold">Trợ lý AI</h2>
        <Button onClick={onNew}><Plus />Cuộc trò chuyện mới</Button>
      </div>
      <nav aria-label="Lịch sử trò chuyện" className="min-h-0 flex-1 overflow-y-auto p-2">
        {history.status === "loading" && (
          <div className="grid gap-2 p-2"><Skeleton className="h-9" /><Skeleton className="h-9" /></div>
        )}
        {history.status === "error" && <p className="p-2 text-danger-fg">{history.message}</p>}
        {history.status === "ready" && history.data.items.length === 0 && (
          <p className="p-2 text-muted">Chưa có cuộc trò chuyện nào.</p>
        )}
        {history.status === "ready" &&
          GROUPS.map((group) => {
            const items = history.data.items.filter((s) => groupLabel(s.last_at, now) === group);
            if (items.length === 0) return null;
            return (
              <div key={group}>
                <p className="px-2 pt-3 pb-1 text-[11px] font-bold tracking-wider text-subtle uppercase">{group}</p>
                {items.map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    aria-current={s.id === activeId ? "true" : undefined}
                    onClick={() => onSelect(s.id)}
                    className={cn(
                      "grid w-full gap-0.5 rounded-control px-2.5 py-2 text-left hover:bg-surface-sunken",
                      s.id === activeId && "bg-primary-subtle hover:bg-primary-subtle",
                    )}
                  >
                    <span className="truncate font-semibold">{s.title}</span>
                    <span className="text-xs text-subtle">{s.turn_count} câu hỏi · {timeOf(s.last_at, group)}</span>
                  </button>
                ))}
              </div>
            );
          })}
      </nav>
    </div>
  );
}
