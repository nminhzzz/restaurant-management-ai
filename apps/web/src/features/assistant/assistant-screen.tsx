"use client";

import { PanelLeft, ShieldCheck, X } from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";

import { Button } from "@/components/ui/button";
import { ApiError, apiFetch } from "@/lib/api-client";
import { roleLabel } from "@/lib/roles";
import { parseSession, serverSessionSnapshot, sessionSnapshot, subscribeSession } from "@/lib/session";
import type { SessionDetail } from "@/types/api";

import { AssistantMessage } from "./assistant-message";
import { Composer } from "./composer";
import { HistoryPanel } from "./history-panel";
import { useConversation } from "./use-conversation";
import { Welcome } from "./welcome";

export function AssistantScreen() {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const stored = useSyncExternalStore(subscribeSession, sessionSnapshot, serverSessionSnapshot);
  const user = useMemo(() => parseSession(stored), [stored]);
  const [refreshKey, setRefreshKey] = useState(0);
  const [drawer, setDrawer] = useState(false);
  const [openError, setOpenError] = useState<string | null>(null);
  const conversation = useConversation({ onSessionCreated: () => setRefreshKey((k) => k + 1) });
  const bottom = useRef<HTMLDivElement>(null);
  const { turns, pending, ask, reset, load, sessionId } = conversation;

  // Plain function + `.then()`, not `async`/`await`: an effect below calls this
  // directly, and react-hooks/set-state-in-effect flags an async function there.
  function open(id: number) {
    apiFetch<SessionDetail>(`/assistant/sessions/${id}`).then(
      (detail) => {
        setOpenError(null);
        load(detail);
      },
      (error: unknown) => {
        reset();
        setOpenError(error instanceof ApiError ? error.message : "Không mở được cuộc trò chuyện.");
        router.replace(pathname);
      },
    );
  }

  const requested = Number(params.get("session"));
  useEffect(() => {
    if (Number.isInteger(requested) && requested > 0) open(requested);
    // Only the URL value matters; `open` is recreated every render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [requested]);

  useEffect(() => {
    bottom.current?.scrollIntoView?.({ block: "end" });
  }, [turns]);

  function startNew() {
    reset();
    setOpenError(null);
    setDrawer(false);
    router.replace(pathname);
  }

  const title = turns[0]?.question ?? "Cuộc trò chuyện mới";
  const scope = user ? `${roleLabel(user.role)} · chỉ đọc` : "Chỉ đọc";
  const history = (
    <HistoryPanel
      activeId={sessionId}
      refreshKey={refreshKey}
      onSelect={(id) => {
        setDrawer(false);
        open(id);
      }}
      onNew={startNew}
    />
  );

  return (
    <div className="flex h-[calc(100dvh-5.5rem)] overflow-hidden rounded-container border border-border bg-canvas lg:h-[calc(100dvh-3rem)]">
      <aside className="hidden w-72 shrink-0 border-r border-border xl:block">{history}</aside>
      {drawer && (
        <div className="fixed inset-0 z-40 xl:hidden">
          <button aria-label="Đóng lịch sử" className="absolute inset-0 bg-ink/40" onClick={() => setDrawer(false)} />
          <aside className="relative h-full w-72 border-r border-border">
            <button aria-label="Đóng lịch sử" onClick={() => setDrawer(false)}
              className="absolute top-2 right-2 z-10 grid size-11 place-items-center rounded-control text-subtle hover:bg-surface-sunken">
              <X className="size-4" />
            </button>
            {history}
          </aside>
        </div>
      )}

      <section className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-3 border-b border-border bg-surface px-4 py-2.5">
          <Button variant="ghost" size="icon" className="size-11 xl:hidden" aria-label="Mở lịch sử" onClick={() => setDrawer(true)}>
            <PanelLeft />
          </Button>
          <h1 className="min-w-0 flex-1 truncate text-base font-bold">{title}</h1>
          <span className="inline-flex h-[26px] items-center gap-1.5 rounded-badge bg-surface-sunken px-2 text-xs font-semibold whitespace-nowrap text-muted ring-1 ring-border ring-inset">
            <ShieldCheck className="size-3.5" aria-hidden />
            {scope}
          </span>
        </header>

        {openError && (
          <p role="alert" className="mx-4 mt-3 rounded-container bg-danger-subtle px-3.5 py-2.5 text-danger-fg shadow-[inset_4px_0_0_0_var(--color-danger)]">
            {openError}
          </p>
        )}

        <div className="min-h-0 flex-1 overflow-y-auto">
          {turns.length === 0 ? (
            <Welcome username={user?.username} role={user?.role} onAsk={(q) => void ask(q)}
              composer={<Composer size="lg" autoFocus disabled={pending} placeholder="Ví dụ: Doanh thu tháng 8 theo từng ngày?" onSubmit={(q) => void ask(q)} />} />
          ) : (
            <div className="mx-auto grid max-w-3xl gap-7 px-5 pt-6 pb-3">
              {turns.map((turn) => (
                <AssistantMessage key={turn.id} turn={turn} onAsk={(q) => void ask(q)} />
              ))}
              <div ref={bottom} />
            </div>
          )}
        </div>

        {turns.length > 0 && (
          <div className="px-5 pt-2 pb-3.5">
            <div className="mx-auto max-w-3xl">
              <Composer size="lg" disabled={pending} placeholder="Hỏi tiếp về số liệu…" onSubmit={(q) => void ask(q)} />
              <p className="mt-2 text-center text-xs text-subtle">
                Trợ lý có thể hiểu sai câu hỏi. Kiểm tra lại số liệu quan trọng ở mục Báo cáo.
              </p>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
