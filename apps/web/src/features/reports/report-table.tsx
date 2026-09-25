"use client";

import { useMemo, useState } from "react";

import { DataPagination } from "@/components/data-pagination";
import { SearchFilter } from "@/components/filter-bar";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useClientPagination } from "@/lib/use-client-pagination";

export function ReportTable({
  headers,
  rows,
  pageSize,
  searchLabel,
  searchColumn = 0,
}: {
  headers: string[];
  rows: (string | number)[][];
  /** Enables client-side paging when set (report tables page at 10/page). */
  pageSize?: number;
  /** Enables a search box filtering on `searchColumn` when set. */
  searchLabel?: string;
  searchColumn?: number;
}) {
  const [search, setSearch] = useState("");
  const filtered = useMemo(() => {
    if (!searchLabel || !search.trim()) return rows;
    const needle = search.trim().toLowerCase();
    return rows.filter((row) =>
      String(row[searchColumn] ?? "")
        .toLowerCase()
        .includes(needle),
    );
  }, [rows, search, searchLabel, searchColumn]);

  const paging = useClientPagination(
    filtered,
    search,
    pageSize ?? Number.MAX_SAFE_INTEGER,
  );
  const pageItems = pageSize ? paging.pageItems : filtered;

  return (
    <div className="space-y-3">
      {searchLabel ? (
        <SearchFilter label={searchLabel} value={search} onChange={setSearch} />
      ) : null}
      <Table className="min-w-96">
        <TableHeader>
          <TableRow>
            {headers.map((header, index) => (
              <TableHead
                key={header}
                className={index > 0 ? "text-right" : undefined}
              >
                {header}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {pageItems.map((row, rowIndex) => (
            <TableRow key={rowIndex}>
              {row.map((cell, cellIndex) => (
                <TableCell
                  key={cellIndex}
                  className={
                    cellIndex > 0 ? "text-right tabular-nums" : undefined
                  }
                >
                  {cell}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {pageSize && filtered.length > 0 ? (
        <DataPagination
          page={paging.page}
          pageSize={paging.pageSize}
          total={paging.total}
          onPageChange={paging.setPage}
        />
      ) : null}
    </div>
  );
}
