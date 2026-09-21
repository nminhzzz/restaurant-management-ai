import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ChatPanel } from "@/features/assistant/chat-panel";

const response = {
  answer: "Doanh thu hôm qua là 1.000.000 đồng.",
  data: [{ DoanhThu: "1000000" }],
  chart: null,
  detail: {
    sql: "SELECT SUM(ThanhTien) AS DoanhThu FROM vw_ai_thungan",
    row_count: 1,
    view: "vw_ai_thungan",
    elapsed_ms: 12.4,
  },
};

describe("ChatPanel", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders the answer, the result rows and the query detail", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => response }),
    );

    render(<ChatPanel />);
    fireEvent.change(screen.getByLabelText("Câu hỏi bằng tiếng Việt"), {
      target: { value: "Doanh thu hôm qua?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Gửi câu hỏi" }));

    expect(await screen.findByText(response.answer)).toBeInTheDocument();
    expect(screen.getByRole("cell", { name: "1000000" })).toBeInTheDocument();
    expect(screen.getByText("vw_ai_thungan")).toBeInTheDocument();
  });
});
