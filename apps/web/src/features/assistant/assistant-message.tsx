"use client";

import {
  ArrowRight,
  CircleAlert,
  CircleHelp,
  Copy,
  RefreshCw,
  RotateCcw,
  ShieldCheck,
  UtensilsCrossed,
} from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { ResultTabs } from "./result-tabs";
import type { Turn } from "./use-conversation";

function Elapsed() {
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => clearInterval(id);
  }, []);
  return <span className="tabular-nums">{seconds}</span>;
}

function Points({
  headline,
  highlights,
}: {
  headline: string;
  highlights: string[];
}) {
  return (
    <>
      <p className="text-base leading-[25px] font-bold text-pretty">
        {headline}
      </p>
      {highlights.length > 0 && (
        <ul className="grid gap-1.5 text-[15px] leading-[23px]">
          {highlights.map((point) => (
            <li
              key={point}
              className="grid grid-cols-[14px_minmax(0,1fr)] gap-2"
            >
              <span aria-hidden className="mt-[9px] size-1.5 bg-ink" />
              <span>{point}</span>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}

export function AssistantMessage({
  turn,
  compact = false,
  busy = false,
  onAsk,
}: {
  turn: Turn;
  compact?: boolean;
  busy?: boolean;
  onAsk: (text: string) => void;
}) {
  const result = turn.result;

  async function copy() {
    if (!result) return;
    const text = [
      result.headline,
      ...result.highlights.map((p) => `- ${p}`),
      "",
      result.scope_note ?? "",
    ]
      .join("\n")
      .trim();
    try {
      await navigator.clipboard.writeText(text);
      toast.success("Đã sao chép câu trả lời.");
    } catch {
      toast.error(
        "Trình duyệt không cho sao chép. Hãy chọn và sao chép thủ công.",
      );
    }
  }

  let body: React.ReactNode;
  if (turn.status === "pending") {
    body = (
      <p
        role="status"
        className="flex h-8 items-center gap-2.5 font-medium text-muted"
      >
        <span aria-hidden className="size-2 bg-ink motion-safe:animate-pulse" />
        Đang phân tích câu hỏi · <Elapsed /> giây
      </p>
    );
  } else if (turn.status === "failed") {
    body = (
      <div
        role="alert"
        className="flex flex-wrap items-center gap-3 rounded-container bg-danger-subtle px-3.5 py-3 text-danger-fg shadow-[inset_4px_0_0_0_var(--color-danger)]"
      >
        <CircleAlert className="size-4 shrink-0" aria-hidden />
        <p className="flex-1 font-medium">{turn.error}</p>
        <Button
          variant="secondary"
          size="sm"
          disabled={busy}
          onClick={() => onAsk(turn.question)}
        >
          Thử lại
        </Button>
      </div>
    );
  } else if (turn.restored) {
    body = (
      <>
        <Points
          headline={turn.restored.headline}
          highlights={turn.restored.highlights}
        />
        <div className="flex flex-wrap items-center gap-2 text-[13px] text-subtle">
          Bảng và biểu đồ của lượt cũ không được lưu.
          <Button
            variant="ghost"
            size="sm"
            disabled={busy}
            onClick={() => onAsk(turn.question)}
          >
            <RefreshCw />
            Chạy lại
          </Button>
        </div>
      </>
    );
  } else if (result && result.kind === "error") {
    body = (
      <div
        role="alert"
        className="flex flex-wrap items-center gap-3 rounded-container bg-danger-subtle px-3.5 py-3 text-danger-fg shadow-[inset_4px_0_0_0_var(--color-danger)]"
      >
        <CircleAlert className="size-4 shrink-0" aria-hidden />
        <p className="flex-1 font-medium">{result.headline || result.answer}</p>
        <Button
          variant="secondary"
          size="sm"
          disabled={busy}
          onClick={() => onAsk(turn.question)}
        >
          Thử lại
        </Button>
      </div>
    );
  } else if (result && result.kind !== "answer") {
    body = (
      <div className="grid gap-1.5 rounded-container border border-border bg-surface px-3.5 py-3 shadow-[inset_3px_0_0_0_var(--color-warning)]">
        <p className="flex items-center gap-2 font-bold">
          <CircleHelp className="size-4 text-warning" aria-hidden />
          {result.kind === "clarify"
            ? "Cần làm rõ câu hỏi"
            : "Không trả lời được câu này"}
        </p>
        <p className="text-[15px] leading-[23px]">
          {result.headline || result.answer}
        </p>
      </div>
    );
  } else if (result) {
    body = (
      <>
        <Points
          headline={result.headline || result.answer}
          highlights={result.highlights}
        />
        <ResultTabs result={result} />
        {result.scope_note && (
          <p className="flex items-start gap-2 text-[12.5px] leading-[18px] text-subtle">
            <ShieldCheck className="mt-px size-3.5 shrink-0" aria-hidden />
            {result.scope_note} Trợ lý chỉ đọc, không sửa dữ liệu.
          </p>
        )}
        <div className="-ml-2 flex flex-wrap gap-0.5">
          <Button variant="ghost" size="sm" onClick={copy}>
            <Copy />
            Sao chép
          </Button>
          <Button
            variant="ghost"
            size="sm"
            disabled={busy}
            onClick={() => onAsk(turn.question)}
          >
            <RotateCcw />
            Hỏi lại
          </Button>
        </div>
        {result.follow_ups.length > 0 && (
          <div className="grid gap-1.5">
            <p className="text-[11px] font-bold tracking-wider text-subtle uppercase">
              Hỏi tiếp
            </p>
            <div className="flex flex-wrap gap-1.5">
              {result.follow_ups.map((q) => (
                <button
                  key={q}
                  type="button"
                  disabled={busy}
                  onClick={() => onAsk(q)}
                  className="inline-flex items-center gap-2 rounded-control border border-border bg-surface px-2.5 py-1.5 text-left font-medium hover:border-ink disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <ArrowRight className="size-3.5 text-subtle" aria-hidden />
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}
      </>
    );
  }

  return (
    <div className="grid gap-6">
      <p
        className={cn(
          "max-w-[80%] justify-self-end rounded-container border border-border bg-surface px-3.5 py-2.5",
          !compact && "text-[15px] leading-[22px]",
        )}
      >
        {turn.question}
      </p>
      <article
        aria-label="Câu trả lời của trợ lý"
        className={cn(
          "grid gap-3.5",
          !compact && "grid-cols-[32px_minmax(0,1fr)] gap-x-3.5",
        )}
      >
        {!compact && (
          <span
            aria-hidden
            className="grid size-8 place-items-center rounded-control bg-ink text-white"
          >
            <UtensilsCrossed className="size-4" />
          </span>
        )}
        <div className="grid min-w-0 gap-3.5">{body}</div>
      </article>
    </div>
  );
}
