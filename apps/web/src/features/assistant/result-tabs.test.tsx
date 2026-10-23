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
  it("always displays a result table alongside the chart", () => {
    render(
      <ResultTabs
        result={{
          ...base,
          data: [{ SoDon: 3 }],
          chart: { type: "bar", x: "SoDon", y: ["SoDon"] },
        }}
      />,
    );
    expect(screen.getByRole("table")).toBeVisible();
    expect(screen.getByRole("columnheader", { name: "SoDon" })).toBeVisible();
  });

  it("keeps technical SQL details collapsed by default", () => {
    render(
      <ResultTabs
        result={{
          ...base,
          detail: {
            sql: "SELECT 1",
            view: "vw_ai_quanly_order",
            elapsed_ms: 10,
            row_count: 0,
          },
        }}
      />,
    );
    expect(screen.getByText("SELECT 1")).not.toBeVisible();
    expect(screen.getByText("Chi tiết kỹ thuật")).toBeVisible();
    expect(screen.getByRole("table")).toBeVisible();
    expect(screen.getByText("Không có dữ liệu phù hợp.")).toBeVisible();
  });
});
