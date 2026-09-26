import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AssistantMessage } from "./assistant-message";
import type { Turn } from "./use-conversation";

const base = {
  answer: "x",
  headline: "Doanh thu 7 ngày đạt 128.450.000 ₫.",
  highlights: ["Chủ nhật cao nhất."],
  follow_ups: ["So với tuần trước?"],
  scope_note: "Phạm vi dữ liệu: vw_ai_quanly — toàn bộ.",
  kind: "answer" as const,
  columns: [
    { key: "BusinessDate", label: "Ngày kinh doanh", kind: "date" as const },
    { key: "DoanhThu", label: "Doanh thu", kind: "money" as const },
  ],
  data: [{ BusinessDate: "2026-09-20", DoanhThu: "22100000" }],
  chart: null,
  detail: {
    sql: "SELECT 1",
    row_count: 1,
    view: "vw_ai_quanly",
    elapsed_ms: 840,
  },
};

function turn(overrides: Partial<Turn> = {}): Turn {
  return {
    id: "1",
    question: "Doanh thu?",
    status: "done",
    result: base,
    error: null,
    restored: null,
    ...overrides,
  };
}

describe("AssistantMessage", () => {
  it("renders the headline, highlights, labelled table and scope note", () => {
    render(<AssistantMessage turn={turn()} onAsk={vi.fn()} />);
    expect(screen.getByText(base.headline)).toBeInTheDocument();
    expect(screen.getByText("Chủ nhật cao nhất.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: /Bảng/ }));
    expect(
      screen.getByRole("columnheader", { name: "Doanh thu" }),
    ).toBeInTheDocument();
    expect(screen.getByText("22.100.000 ₫")).toBeInTheDocument();
    expect(screen.getByText("20/09/2026")).toBeInTheDocument();
    expect(screen.getByText(/vw_ai_quanly/)).toBeInTheDocument();
  });

  it("only shows tabs that have content", () => {
    render(<AssistantMessage turn={turn()} onAsk={vi.fn()} />);
    expect(
      screen.queryByRole("tab", { name: /Biểu đồ/ }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /SQL/ })).toBeInTheDocument();
  });

  it("asks a follow-up immediately", () => {
    const onAsk = vi.fn();
    render(<AssistantMessage turn={turn()} onAsk={onAsk} />);
    fireEvent.click(screen.getByRole("button", { name: "So với tuần trước?" }));
    expect(onAsk).toHaveBeenCalledWith("So với tuần trước?");
  });

  it("disables the follow-up chips and re-ask actions while busy (review #5)", () => {
    render(<AssistantMessage turn={turn()} onAsk={vi.fn()} busy />);
    expect(
      screen.getByRole("button", { name: "So với tuần trước?" }),
    ).toBeDisabled();
    expect(screen.getByRole("button", { name: /Hỏi lại/ })).toBeDisabled();
  });

  it("shows a clarification without a result block", () => {
    render(
      <AssistantMessage
        turn={turn({
          result: {
            ...base,
            kind: "clarify",
            headline: "Bạn muốn xem ngày nào?",
            data: [],
            detail: null,
          },
        })}
        onAsk={vi.fn()}
      />,
    );
    expect(screen.getByText("Bạn muốn xem ngày nào?")).toBeInTheDocument();
    expect(screen.queryByRole("tablist")).not.toBeInTheDocument();
  });

  it("shows a backend error as an alert with a retry", () => {
    const onAsk = vi.fn();
    render(
      <AssistantMessage
        turn={turn({
          result: {
            ...base,
            kind: "error",
            headline: "Trợ lý phản hồi quá lâu.",
            data: [],
            detail: null,
          },
        })}
        onAsk={onAsk}
      />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Trợ lý phản hồi quá lâu.",
    );
    fireEvent.click(screen.getByRole("button", { name: "Thử lại" }));
    expect(onAsk).toHaveBeenCalledWith("Doanh thu?");
  });

  it("offers a retry on failure and a re-run for a restored turn", () => {
    const onAsk = vi.fn();
    const { rerender } = render(
      <AssistantMessage
        turn={turn({ status: "failed", result: null, error: "Mất kết nối." })}
        onAsk={onAsk}
      />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent("Mất kết nối.");
    fireEvent.click(screen.getByRole("button", { name: "Thử lại" }));
    rerender(
      <AssistantMessage
        turn={turn({
          result: null,
          restored: {
            id: 1,
            question: "Doanh thu?",
            headline: "Cũ.",
            highlights: [],
            status: "Thành công",
            occurred_at: "",
          },
        })}
        onAsk={onAsk}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Chạy lại" }));
    expect(onAsk).toHaveBeenCalledTimes(2);
    expect(onAsk).toHaveBeenLastCalledWith("Doanh thu?");
  });
});
