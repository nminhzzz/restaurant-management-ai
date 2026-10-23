"use client";

import { ShieldCheck } from "lucide-react";

import { DataPagination } from "@/components/data-pagination";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useClientPagination } from "@/lib/use-client-pagination";
import { cn } from "@/lib/utils";
import type { ChatResponse } from "@/types/api";

import { ChartView } from "./chart-view";
import { columnsFor, formatCell, isNumericKind } from "./format-cell";

function ResultTable({ result }: { result: ChatResponse }) {
  const paging = useClientPagination(result.data, "", 10);
  const columns = columnsFor(result.data, result.columns);
  return (
    <div className="space-y-3">
      <Table>
        <TableHeader>
          <TableRow>
            {columns.map((c) => (
              <TableHead
                key={c.key}
                className={cn(isNumericKind(c.kind) && "text-right")}
              >
                {c.label}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {result.data.length === 0 && (
            <TableRow>
              <TableCell colSpan={Math.max(1, columns.length)}>
                Không có dữ liệu phù hợp.
              </TableCell>
            </TableRow>
          )}
          {paging.pageItems.map((row, index) => (
            <TableRow key={index}>
              {columns.map((c) => (
                <TableCell
                  key={c.key}
                  className={cn(
                    isNumericKind(c.kind) && "text-right tabular-nums",
                  )}
                >
                  {formatCell(row[c.key], c.kind)}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {result.data.length > paging.pageSize && (
        <DataPagination
          page={paging.page}
          pageSize={paging.pageSize}
          total={paging.total}
          onPageChange={paging.setPage}
        />
      )}
    </div>
  );
}

export function ResultTabs({ result }: { result: ChatResponse }) {
  return (
    <div className="overflow-hidden rounded-container border border-border bg-surface">
      {result.chart && result.data.length > 0 && (
        <div className="border-b border-border p-3.5">
          <ChartView
            spec={result.chart}
            rows={result.data}
            columns={result.columns}
          />
        </div>
      )}
      <ResultTable result={result} />
      {result.detail && (
        <details className="border-t border-border p-3.5">
          <summary className="cursor-pointer font-semibold text-muted">
            Chi tiết kỹ thuật
          </summary>
          <div className="mt-3 space-y-3">
            <p className="text-xs text-subtle">
              {result.detail.row_count} dòng ·{" "}
              {(result.detail.elapsed_ms / 1000).toLocaleString("vi-VN", {
                maximumFractionDigits: 2,
              })}{" "}
              giây
            </p>
            <pre className="overflow-x-auto font-mono text-xs leading-5 whitespace-pre-wrap">
              {result.detail.sql}
            </pre>
            <p className="flex items-center gap-2 rounded-control bg-success-subtle px-2.5 py-2 text-[13px] font-semibold text-success-fg">
              <ShieldCheck className="size-4 shrink-0" aria-hidden />
              Đã qua kiểm duyệt: chỉ đọc, đúng tập view {result.detail.view} của
              vai trò, có giới hạn số dòng.
            </p>
          </div>
        </details>
      )}
    </div>
  );
}
