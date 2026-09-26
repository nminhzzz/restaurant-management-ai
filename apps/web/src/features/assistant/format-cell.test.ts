import { describe, expect, it } from "vitest";

import { columnsFor, formatCell, isNumericKind } from "./format-cell";
import { suggestionsFor } from "./suggestions";

describe("formatCell", () => {
  it("formats each kind", () => {
    expect(formatCell("65000.0000", "money")).toBe("65.000 ₫");
    expect(formatCell(1234.5, "number")).toBe("1.234,5");
    expect(formatCell("12.5", "percent")).toBe("12,5%");
    expect(formatCell("2026-09-26", "date")).toBe("26/09/2026");
    expect(formatCell(null, "money")).toBe("");
    expect(formatCell("Phở bò", "text")).toBe("Phở bò");
  });

  it("keeps a non-numeric value readable under a numeric kind", () => {
    expect(formatCell("n/a", "number")).toBe("n/a");
  });

  it("falls back to raw keys when the API sent no column metadata", () => {
    expect(columnsFor([{ A: 1 }])).toEqual([
      { key: "A", label: "A", kind: "text" },
    ]);
    expect(columnsFor([])).toEqual([]);
  });

  it("knows which kinds are right-aligned", () => {
    expect(isNumericKind("money")).toBe(true);
    expect(isNumericKind("date")).toBe(false);
  });
});

describe("suggestionsFor", () => {
  it("filters by role and by module", () => {
    expect(
      suggestionsFor("WAREHOUSE").every((s) => s.module === "inventory"),
    ).toBe(true);
    expect(suggestionsFor("MANAGER", "inventory").length).toBeGreaterThan(0);
    expect(
      suggestionsFor("MANAGER", "inventory").every(
        (s) => s.module === "inventory",
      ),
    ).toBe(true);
  });
});
