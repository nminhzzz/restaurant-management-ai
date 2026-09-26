"use client";

import { ChartColumn, CodeXml, ShieldCheck, Table2 } from "lucide-react";
import { useState } from "react";

import { DataPagination } from "@/components/data-pagination";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useClientPagination } from "@/lib/use-client-pagination";
import { cn } from "@/lib/utils";
import type { ChatResponse } from "@/types/api";

import { ChartView } from "./chart-view";
import { columnsFor, formatCell, isNumericKind } from "./format-cell";

type Tab = "chart" | "table" | "sql";

function ResultTable({ result }: { result: ChatResponse }) {
  const paging = useClientPagination(result.data, "", 10);
  const columns = columnsFor(result.data, result.columns);
  return (
    <div className="space-y-3">
      <Table>
        <TableHeader>
          <TableRow>
            {columns.map((c) => (
              <TableHead key={c.key} className={cn(isNumericKind(c.kind) && "text-right")}>
                {c.label}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {paging.pageItems.map((row, index) => (
            <TableRow key={index}>
              {columns.map((c) => (
                <TableCell key={c.key} className={cn(isNumericKind(c.kind) && "text-right tabular-nums")}>
                  {formatCell(row[c.key], c.kind)}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {result.data.length > paging.pageSize && (
        <DataPagination page={paging.page} pageSize={paging.pageSize} total={paging.total} onPageChange={paging.setPage} />
      )}
    </div>
  );
}

export function ResultTabs({ result }: { result: ChatResponse }) {
  const tabs: { key: Tab; label: string; Icon: typeof ChartColumn }[] = [];
  if (result.chart && result.data.length > 0) tabs.push({ key: "chart", label: "Biểu đồ", Icon: ChartColumn });
  if (result.data.length > 0) tabs.push({ key: "table", label: "Bảng", Icon: Table2 });
  if (result.detail) tabs.push({ key: "sql", label: "SQL", Icon: CodeXml });
  const [active, setActive] = useState<Tab | null>(tabs[0]?.key ?? null);
  if (tabs.length === 0 || active === null) return null;

  return (
    <div className="overflow-hidden rounded-container border border-border bg-surface">
      <div role="tablist" aria-label="Kết quả" className="flex items-center gap-0.5 border-b border-border pr-3 pl-1">
        {tabs.map(({ key, label, Icon }) => (
          <button
            key={key}
            type="button"
            role="tab"
            aria-selected={active === key}
            onClick={() => setActive(key)}
            className={cn(
              "inline-flex items-center gap-1.5 px-2.5 py-2.5 font-semibold text-muted shadow-[inset_0_-2px_0_0_transparent]",
              active === key && "text-ink shadow-[inset_0_-2px_0_0_var(--color-ink)]",
            )}
          >
            <Icon className="size-4" aria-hidden />
            {label}
          </button>
        ))}
        {result.detail && (
          <span className="ml-auto text-xs whitespace-nowrap text-subtle tabular-nums">
            {result.detail.row_count} dòng · {(result.detail.elapsed_ms / 1000).toLocaleString("vi-VN", { maximumFractionDigits: 2 })} giây
          </span>
        )}
      </div>
      <div role="tabpanel" className={cn(active !== "table" && "p-3.5")}>
        {active === "chart" && <ChartView spec={result.chart} rows={result.data} columns={result.columns} />}
        {active === "table" && <ResultTable result={result} />}
        {active === "sql" && result.detail && (
          <div className="space-y-3">
            <pre className="overflow-x-auto font-mono text-xs leading-5 whitespace-pre-wrap">{result.detail.sql}</pre>
            <p className="flex items-center gap-2 rounded-control bg-success-subtle px-2.5 py-2 text-[13px] font-semibold text-success-fg">
              <ShieldCheck className="size-4 shrink-0" aria-hidden />
              Đã qua kiểm duyệt: chỉ đọc, đúng view {result.detail.view} của vai trò, có giới hạn số dòng.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
