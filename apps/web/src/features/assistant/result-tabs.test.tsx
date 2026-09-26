import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ResultTabs } from "./result-tabs";
import type { ChatResponse } from "@/types/api";

const base: ChatResponse = {
  answer: "x",
  headline: "x",
  highlights: [],
  follow_ups: [],
  scope_note: null,
  columns: [],
  kind: "answer",
  data: [],
  chart: null,
  detail: null,
};

describe("ResultTabs", () => {
  it("keeps a valid tab selected after the result changes shape", () => {
    const withSql: ChatResponse = {
      ...base,
      detail: {
        sql: "SELECT 1",
        row_count: 1,
        view: "vw_ai_quanly",
        elapsed_ms: 10,
      },
    };
    const { rerender } = render(<ResultTabs result={withSql} />);
    expect(screen.getByRole("tab", { name: /SQL/ })).toHaveAttribute(
      "aria-selected",
      "true",
    );

    const withTableOnly: ChatResponse = {
      ...base,
      data: [{ a: 1 }],
      detail: null,
    };
    rerender(<ResultTabs result={withTableOnly} />);

    expect(screen.getByRole("tab", { name: /Bảng/ })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByRole("table")).toBeInTheDocument();
  });
});
