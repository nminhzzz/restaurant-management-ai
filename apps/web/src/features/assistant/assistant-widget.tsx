"use client";

import { Maximize2, MessageSquareText, Minus, Plus } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import {
  useEffect,
  useMemo,
  useRef,
  useState,
  useSyncExternalStore,
} from "react";

import { Button } from "@/components/ui/button";
import { MODULE_LIST } from "@/lib/modules";
import { roleLabel } from "@/lib/roles";
import {
  parseSession,
  serverSessionSnapshot,
  sessionSnapshot,
  subscribeSession,
} from "@/lib/session";

import { AssistantMessage } from "./assistant-message";
import { Composer } from "./composer";
import { suggestionsFor } from "./suggestions";
import { useConversation } from "./use-conversation";

// The POS keeps its pay and send buttons in the bottom-right corner; the full assistant
// page already is the assistant.
const HIDDEN_ON = ["/assistant", "/sales"];

export function AssistantWidget() {
  const pathname = usePathname();
  const router = useRouter();
  const stored = useSyncExternalStore(
    subscribeSession,
    sessionSnapshot,
    serverSessionSnapshot,
  );
  const user = useMemo(() => parseSession(stored), [stored]);
  const [open, setOpen] = useState(false);
  const { turns, pending, ask, reset, sessionId } = useConversation();
  const bottom = useRef<HTMLDivElement>(null);

  const hidden = HIDDEN_ON.some((p) => pathname.startsWith(p));
  const assistantModule = MODULE_LIST.find((m) => m.key === "assistant");
  const allowed =
    user !== null &&
    (assistantModule?.allowedRoles.includes(user.role) ?? false);
  const current = MODULE_LIST.find((m) => pathname.startsWith(m.path));
  const role = user?.role ?? "";

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen((value) => !value);
      } else if (event.key === "Escape" && open && !event.defaultPrevented) {
        // A Radix dialog on top of the widget (change password, catalog/inventory/settings
        // dialogs) calls preventDefault on the Escape it handles first — don't also close us.
        setOpen(false);
      }
    }
    if (hidden || !allowed) return;
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [hidden, allowed, open]);

  useEffect(() => {
    bottom.current?.scrollIntoView?.({ block: "end" });
  }, [turns]);

  if (hidden || !allowed) return null;

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed right-5 bottom-5 z-40 inline-flex h-12 items-center gap-2.5 rounded-overlay bg-ink pr-4.5 pl-3.5 font-bold text-white shadow-float hover:bg-primary-hover"
      >
        <MessageSquareText className="size-4" aria-hidden />
        Hỏi trợ lý
        <kbd className="rounded-badge bg-white/15 px-1.5 font-mono text-[11px] font-medium text-white/80">
          Ctrl K
        </kbd>
      </button>
    );
  }

  return (
    <section
      role="dialog"
      aria-label="Trợ lý AI"
      className="fixed right-5 bottom-5 z-40 flex h-[min(600px,calc(100dvh-2.5rem))] w-[min(420px,calc(100vw-2.5rem))] flex-col overflow-hidden rounded-overlay border border-border-strong bg-surface shadow-float max-sm:inset-0 max-sm:h-auto max-sm:w-auto max-sm:rounded-none"
    >
      <header className="flex items-center gap-1.5 border-b border-border py-2 pr-2 pl-3.5">
        <h2 className="flex-1 text-[15px] font-bold">Trợ lý AI</h2>
        <span className="rounded-badge bg-surface-sunken px-2 py-0.5 text-xs font-semibold text-muted ring-1 ring-border ring-inset">
          {roleLabel(role)}
        </span>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Cuộc trò chuyện mới"
          onClick={reset}
        >
          <Plus />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Mở toàn màn hình"
          onClick={() => {
            setOpen(false);
            router.push(
              sessionId ? `/assistant?session=${sessionId}` : "/assistant",
            );
          }}
        >
          <Maximize2 />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Thu nhỏ"
          onClick={() => setOpen(false)}
        >
          <Minus />
        </Button>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto bg-canvas p-3.5">
        {turns.length === 0 ? (
          <div className="grid gap-2.5">
            {current && (
              <p className="text-xs text-subtle">
                Đang ở màn {current.title} · câu hỏi gợi ý theo màn này
              </p>
            )}
            {suggestionsFor(role, current?.key)
              .slice(0, 3)
              .map((s) => (
                <button
                  key={s.text}
                  type="button"
                  onClick={() => void ask(s.text)}
                  className="rounded-control border border-border bg-surface px-3 py-2.5 text-left font-medium hover:border-ink"
                >
                  {s.text}
                </button>
              ))}
          </div>
        ) : (
          <div className="grid gap-5">
            {turns.map((turn) => (
              <AssistantMessage
                key={turn.id}
                turn={turn}
                compact
                busy={pending}
                onAsk={(q) => void ask(q)}
              />
            ))}
            <div ref={bottom} />
          </div>
        )}
      </div>

      <div className="border-t border-border p-2.5">
        <Composer
          size="sm"
          autoFocus
          disabled={pending}
          placeholder="Hỏi nhanh về số liệu…"
          onSubmit={(q) => void ask(q)}
        />
      </div>
    </section>
  );
}
