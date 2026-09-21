export interface ApiErrorBody {
  error: { code: string; message: string };
}

export interface QueryDetail {
  sql: string;
  row_count: number;
  view: string;
  elapsed_ms: number;
}

export interface ChatResponse {
  answer: string;
  data: Record<string, unknown>[];
  chart: Record<string, unknown> | null;
  detail: QueryDetail | null;
}
