import { formatDate, formatDateTime, formatNumber, formatVnd } from "@/lib/format";
import type { ColumnKind, ColumnMeta } from "@/types/api";

export function isNumericKind(kind: ColumnKind): boolean {
  return kind === "money" || kind === "number" || kind === "percent";
}

export function formatCell(value: unknown, kind: ColumnKind): string {
  if (value === null || value === undefined || value === "") return "";
  const raw = String(value);
  switch (kind) {
    case "money":
      return formatVnd(raw) || raw;
    case "number":
      return formatNumber(raw) || raw;
    case "percent": {
      const text = formatNumber(raw);
      return text ? `${text}%` : raw;
    }
    case "date":
      return formatDate(raw);
    case "datetime":
      return formatDateTime(raw);
    default:
      return raw;
  }
}

export function columnsFor(rows: Record<string, unknown>[], columns?: ColumnMeta[]): ColumnMeta[] {
  if (columns && columns.length > 0) return columns;
  return rows.length > 0 ? Object.keys(rows[0]).map((key) => ({ key, label: key, kind: "text" })) : [];
}
