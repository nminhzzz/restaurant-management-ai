import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { ApiError, apiFetch } from "@/lib/api-client";
import { useConversation } from "./use-conversation";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;
const reply = {
  answer: "a",
  headline: "Có 2 đơn.",
  highlights: [],
  follow_ups: [],
  scope_note: null,
  columns: [],
  kind: "answer",
  data: [],
  chart: null,
  detail: null,
  session_id: 9,
};

describe("useConversation", () => {
  beforeEach(() => vi.resetAllMocks());

  it("sends the session id after the first turn and reports a new session once", async () => {
    fetchMock.mockResolvedValue(reply);
    const onSessionCreated = vi.fn();
    const { result } = renderHook(() => useConversation({ onSessionCreated }));

    await act(() => result.current.ask("Câu 1"));
    await act(() => result.current.ask("Câu 2"));

    expect(fetchMock.mock.calls[0][1].body).toEqual({ question: "Câu 1" });
    expect(fetchMock.mock.calls[1][1].body).toEqual({
      question: "Câu 2",
      session_id: 9,
    });
    expect(onSessionCreated).toHaveBeenCalledTimes(1);
    expect(result.current.turns.map((t) => t.status)).toEqual(["done", "done"]);
  });

  it("marks a failed turn with the API message and ignores blank questions", async () => {
    fetchMock.mockRejectedValue(new ApiError(500, "X", "Máy chủ lỗi."));
    const { result } = renderHook(() => useConversation());
    await act(() => result.current.ask("   "));
    expect(fetchMock).not.toHaveBeenCalled();
    await act(() => result.current.ask("Câu"));
    expect(result.current.turns[0]).toMatchObject({
      status: "failed",
      error: "Máy chủ lỗi.",
    });
  });

  it("ignores a second ask while a turn is still pending (review #5)", async () => {
    let resolveFirst!: (value: typeof reply) => void;
    fetchMock.mockImplementationOnce(
      () => new Promise((resolve) => (resolveFirst = resolve)),
    );
    const { result } = renderHook(() => useConversation());

    act(() => {
      void result.current.ask("Câu 1");
    });
    act(() => {
      void result.current.ask("Câu 2");
    });
    expect(fetchMock).toHaveBeenCalledTimes(1);

    await act(async () => resolveFirst(reply));
  });

  it("loads a stored session and continues it", async () => {
    fetchMock.mockResolvedValue(reply);
    const { result } = renderHook(() => useConversation());
    act(() =>
      result.current.load({
        id: 5,
        title: "Cũ",
        turns: [
          {
            id: 1,
            question: "Cũ?",
            headline: "Đáp.",
            highlights: [],
            status: "Thành công",
            occurred_at: "2026-09-25T10:00:00",
          },
        ],
      }),
    );
    expect(result.current.turns[0].restored?.headline).toBe("Đáp.");
    await act(() => result.current.ask("Tiếp?"));
    expect(fetchMock.mock.calls[0][1].body).toEqual({
      question: "Tiếp?",
      session_id: 5,
    });
  });
});
