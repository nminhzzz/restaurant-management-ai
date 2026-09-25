"use client";

import { useState } from "react";

import { ChartView } from "@/features/assistant/chart-view";
import { ApiError, apiFetch } from "@/lib/api-client";
import type { ChatResponse, QueryDetail } from "@/types/api";

function ResultTable({ rows }: { rows: Record<string, unknown>[] }) {
  if (rows.length === 0) {
    return null;
  }
  const columns = Object.keys(rows[0]);
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
      <table className="w-full text-left text-sm">
        <thead className="bg-slate-50 text-slate-600">
          <tr>
            {columns.map((column) => (
              <th key={column} className="px-3 py-2 font-medium">
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index} className="border-t border-slate-100">
              {columns.map((column) => (
                <td key={column} className="px-3 py-2">
                  {String(row[column] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SqlDetail({ detail }: { detail: QueryDetail }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
      <p>
        View <code>{detail.view}</code> · {detail.row_count} dòng ·{" "}
        {Math.round(detail.elapsed_ms)} ms
      </p>
      <details className="mt-2">
        <summary className="cursor-pointer">Câu SQL đã chạy</summary>
        <pre className="mt-2 overflow-x-auto whitespace-pre-wrap">
          {detail.sql}
        </pre>
      </details>
    </div>
  );
}

export function ChatPanel() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<ChatResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setResult(null);
    setError(null);
    try {
      const response = await apiFetch<ChatResponse>("/assistant/chat", {
        method: "POST",
        body: { question },
      });
      setResult(response);
    } catch (cause) {
      setError(
        cause instanceof ApiError
          ? cause.message
          : "Không kết nối được máy chủ API.",
      );
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="space-y-3" onSubmit={handleSubmit}>
      <label
        className="block text-sm font-medium text-slate-700"
        htmlFor="question"
      >
        Câu hỏi bằng tiếng Việt
      </label>
      <textarea
        id="question"
        className="h-24 w-full rounded-lg border border-slate-300 p-3 text-sm"
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
        placeholder="Ví dụ: Doanh thu tháng 8 theo từng ngày?"
        required
      />
      <button
        type="submit"
        disabled={pending}
        className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {pending ? "Đang xử lý…" : "Gửi câu hỏi"}
      </button>
      {error === null ? null : <p className="text-sm text-red-600">{error}</p>}
      {result === null ? null : (
        <div className="space-y-3">
          <p className="rounded-lg border border-slate-200 bg-white p-3 text-sm">
            {result.answer}
          </p>
          <ResultTable rows={result.data} />
          <ChartView spec={result.chart} rows={result.data} />
          {result.detail === null ? null : <SqlDetail detail={result.detail} />}
        </div>
      )}
    </form>
  );
}
