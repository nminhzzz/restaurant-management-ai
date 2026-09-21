"use client";

import { useState } from "react";

import { ApiError, apiFetch } from "@/lib/api-client";
import type { ChatResponse } from "@/types/api";

export function ChatPanel() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setAnswer(null);
    setError(null);
    try {
      const response = await apiFetch<ChatResponse>("/assistant/chat", {
        method: "POST",
        body: { question },
      });
      setAnswer(response.answer);
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
      {answer === null ? null : (
        <p className="rounded-lg border border-slate-200 bg-white p-3 text-sm">
          {answer}
        </p>
      )}
    </form>
  );
}
