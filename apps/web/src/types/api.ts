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

export interface ChatResponse {
  answer: string;
  data: Record<string, unknown>[];
  chart: ChartSpec | null;
  detail: QueryDetail | null;
  session_id?: number | null;
}
