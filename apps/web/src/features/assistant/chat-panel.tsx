"use client";

import {
  CircleAlert,
  CodeXml,
  MessageCirclePlus,
  SendHorizontal,
  ShieldCheck,
} from "lucide-react";
import { useMemo, useRef, useState, useSyncExternalStore } from "react";

import { DataPagination } from "@/components/data-pagination";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ChartView } from "@/features/assistant/chart-view";
import { ApiError, apiFetch } from "@/lib/api-client";
import { roleLabel } from "@/lib/roles";
import {
  parseSession,
  serverSessionSnapshot,
  sessionSnapshot,
  subscribeSession,
} from "@/lib/session";
import { useClientPagination } from "@/lib/use-client-pagination";
import type { ChatResponse, QueryDetail } from "@/types/api";

type Turn = {
  id: number;
  question: string;
  result: ChatResponse | null;
  error: string | null;
};

const SUGGESTIONS: Record<string, string[]> = {
  MANAGER: [
    "Món nào bán chạy nhất tuần này?",
    "Doanh thu 7 ngày gần nhất theo từng ngày?",
    "So sánh doanh thu tiền mặt và QR tháng này",
    "Nguyên liệu nào đang dưới mức tối thiểu?",
  ],
  CASHIER: [
    "Hôm nay đã có bao nhiêu hóa đơn?",
    "Doanh thu ca hôm nay là bao nhiêu?",
    "Có order nào đang chờ đối soát không?",
  ],
  WAREHOUSE: [
    "Nguyên liệu nào đang dưới mức tối thiểu?",
    "Tồn kho thịt bò hiện còn bao nhiêu?",
    "Những lô nào sắp hết hạn trong tuần này?",
  ],
};

function ResultTable({ rows }: { rows: Record<string, unknown>[] }) {
  const paging = useClientPagination(rows, "", 10);
  if (rows.length === 0) {
    return null;
  }
  const columns = Object.keys(rows[0]);
  return (
    <div className="space-y-3">
      <Table>
        <TableHeader>
          <TableRow>
            {columns.map((column) => (
              <TableHead key={column}>{column}</TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {paging.pageItems.map((row, index) => (
            <TableRow key={index}>
              {columns.map((column) => (
                <TableCell key={column} className="tabular-nums">
                  {String(row[column] ?? "")}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {rows.length > paging.pageSize ? (
        <DataPagination
          page={paging.page}
          pageSize={paging.pageSize}
          total={paging.total}
          onPageChange={paging.setPage}
        />
      ) : null}
    </div>
  );
}

function SqlDetail({ detail }: { detail: QueryDetail }) {
  return (
    <details className="rounded-control border border-border bg-canvas">
      <summary className="flex cursor-pointer flex-wrap items-center gap-x-2 gap-y-1 px-3 py-2 text-muted marker:content-none">
        <CodeXml className="size-4" aria-hidden />
        <span>Câu SQL đã chạy</span>
        <code className="font-mono text-xs">{detail.view}</code>
        <span className="text-xs tabular-nums">
          {detail.row_count} dòng, {Math.round(detail.elapsed_ms)} ms
        </span>
      </summary>
      <pre className="overflow-x-auto border-t border-border p-3 font-mono text-xs leading-5 whitespace-pre-wrap">
        {detail.sql}
      </pre>
    </details>
  );
}

export function ChatPanel() {
  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [pending, setPending] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const nextId = useRef(0);
  const input = useRef<HTMLTextAreaElement>(null);

  const stored = useSyncExternalStore(
    subscribeSession,
    sessionSnapshot,
    serverSessionSnapshot,
  );
  const session = useMemo(() => parseSession(stored), [stored]);
  const suggestions = SUGGESTIONS[session?.role ?? ""] ?? SUGGESTIONS.MANAGER;

  async function ask(text: string) {
    const asked = text.trim();
    if (!asked || pending !== null) return;
    setPending(asked);
    setQuestion("");
    let turn: Turn;
    try {
      const response = await apiFetch<ChatResponse>("/assistant/chat", {
        method: "POST",
        body: {
          question: asked,
          ...(sessionId !== null ? { session_id: sessionId } : {}),
        },
      });
      turn = {
        id: nextId.current++,
        question: asked,
        result: response,
        error: null,
      };
      if (response.session_id != null) {
        setSessionId(response.session_id);
      }
    } catch (cause) {
      turn = {
        id: nextId.current++,
        question: asked,
        result: null,
        error:
          cause instanceof ApiError
            ? cause.message
            : "Không kết nối được máy chủ API.",
      };
    }
    setTurns((previous) => [...previous, turn]);
    setPending(null);
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void ask(question);
  }

  function startNewConversation() {
    setTurns([]);
    setSessionId(null);
    setQuestion("");
  }

  return (
    <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,1fr)_260px]">
      <div className="min-w-0 space-y-4">
        <div className="flex items-start gap-2.5">
          <p className="flex flex-1 items-start gap-2.5 rounded-control bg-primary-subtle px-3.5 py-2.5 text-primary-subtle-fg">
            <ShieldCheck className="mt-0.5 size-4 shrink-0" aria-hidden />
            <span>
              {session
                ? `Bạn đang hỏi trong phạm vi dữ liệu của vai trò ${roleLabel(session.role)}.`
                : "Trợ lý chỉ trả lời trong phạm vi dữ liệu của vai trò đang đăng nhập."}{" "}
              Trợ lý chỉ đọc, không sửa được dữ liệu.
            </span>
          </p>
          <Button
            type="button"
            variant="secondary"
            onClick={startNewConversation}
            disabled={turns.length === 0 && sessionId === null}
          >
            <MessageCirclePlus />
            Cuộc trò chuyện mới
          </Button>
        </div>

        {turns.map((turn) => (
          <div key={turn.id} className="space-y-3">
            <p className="ml-auto w-fit max-w-[80%] rounded-container bg-ink px-3.5 py-2.5 text-white">
              {turn.question}
            </p>
            {turn.error !== null ? (
              <p
                role="alert"
                className="flex items-start gap-2 rounded-container border border-danger/30 bg-danger-subtle p-4 text-danger-fg"
              >
                <CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
                {turn.error}
              </p>
            ) : turn.result !== null ? (
              <div className="space-y-4 rounded-container border border-border bg-surface p-4">
                <p className="text-[15px] leading-6 whitespace-pre-line">
                  {turn.result.answer}
                </p>
                <ChartView spec={turn.result.chart} rows={turn.result.data} />
                <ResultTable rows={turn.result.data} />
                {turn.result.detail === null ? null : (
                  <SqlDetail detail={turn.result.detail} />
                )}
              </div>
            ) : null}
          </div>
        ))}

        {pending !== null && (
          <div className="space-y-3">
            <p className="ml-auto w-fit max-w-[80%] rounded-container bg-ink px-3.5 py-2.5 text-white">
              {pending}
            </p>
            <div
              role="status"
              className="space-y-2.5 rounded-container border border-border bg-surface p-4"
            >
              <span className="sr-only">Đang xử lý câu hỏi…</span>
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
              <Skeleton className="h-24 w-full" />
            </div>
          </div>
        )}

        <form
          onSubmit={handleSubmit}
          className="space-y-2 rounded-container border border-border bg-surface p-3 focus-within:border-primary focus-within:ring-1 focus-within:ring-primary"
        >
          <label htmlFor="question" className="sr-only">
            Câu hỏi bằng tiếng Việt
          </label>
          <textarea
            id="question"
            ref={input}
            rows={2}
            className="w-full resize-none bg-transparent px-1 outline-none placeholder:text-subtle"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={(event) => {
              if (
                event.key === "Enter" &&
                !event.shiftKey &&
                !event.nativeEvent.isComposing
              ) {
                event.preventDefault();
                void ask(question);
              }
            }}
            placeholder="Ví dụ: Doanh thu tháng 8 theo từng ngày?"
            required
          />
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs text-subtle">
              Enter để gửi, Shift + Enter để xuống dòng
            </span>
            <Button type="submit" disabled={pending !== null}>
              <SendHorizontal />
              Gửi câu hỏi
            </Button>
          </div>
        </form>
      </div>

      <aside className="space-y-2">
        <h2 className="font-semibold text-muted">Câu hỏi gợi ý</h2>
        {suggestions.map((text) => (
          <button
            key={text}
            type="button"
            onClick={() => {
              setQuestion(text);
              input.current?.focus();
            }}
            className="w-full rounded-control border border-border bg-surface px-3 py-2.5 text-left transition-colors hover:border-border-strong"
          >
            {text}
          </button>
        ))}
      </aside>
    </div>
  );
}
