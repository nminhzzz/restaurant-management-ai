export interface ApiErrorBody {
  error: { code: string; message: string };
}

export interface QueryDetail {
  sql: string;
  row_count: number;
  view: string;
  elapsed_ms: number;
}

export interface ChartSpec {
  type: "line" | "bar" | "doughnut";
  x: string;
  y: string[];
}

export type ColumnKind = "text" | "money" | "number" | "date" | "datetime" | "percent";

export interface ColumnMeta {
  key: string;
  label: string;
  kind: ColumnKind;
}

export type AnswerKind = "answer" | "clarify" | "refused" | "error";

export interface ChatResponse {
  answer: string;
  headline: string;
  highlights: string[];
  follow_ups: string[];
  scope_note: string | null;
  columns: ColumnMeta[];
  kind: AnswerKind;
  data: Record<string, unknown>[];
  chart: ChartSpec | null;
  detail: QueryDetail | null;
  session_id?: number | null;
}

export interface SessionSummary {
  id: number;
  title: string;
  turn_count: number;
  created_at: string;
  last_at: string;
}

export interface TurnOut {
  id: number;
  question: string;
  headline: string;
  highlights: string[];
  status: string;
  occurred_at: string;
}

export interface SessionDetail {
  id: number;
  title: string;
  turns: TurnOut[];
}
