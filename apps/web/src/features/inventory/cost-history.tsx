"use client";

import { useCallback, useState } from "react";

import { DataPagination } from "@/components/data-pagination";
import { ErrorState, LoadingState } from "@/components/page-states";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { apiFetch } from "@/lib/api-client";
import { formatDateTime, formatNumber, formatVnd } from "@/lib/format";
import { useResource } from "@/lib/use-resource";

type CostRow = {
  ThoiDiemHieuLuc: string;
  DonGiaBinhQuan: number;
  SoLuongTon: number;
  MaGiaoDichKho: number | null;
  ChungTu: string;
};

const PAGE_SIZE = 20;

/** FR-INV-12: how the average unit cost of one ingredient moved, newest first. */
export function CostHistory({
  ingredientId,
  unit,
}: {
  ingredientId: number;
  unit?: string;
}) {
  const [page, setPage] = useState(1);
  const load = useCallback(
    () =>
      apiFetch<{ items: CostRow[]; total: number }>(
        `/inventory/stock/${ingredientId}/cost-history?page=${page}&page_size=${PAGE_SIZE}`,
      ),
    [ingredientId, page],
  );
  const history = useResource(load);

  return (
    <section className="space-y-2">
      <h3 className="font-medium">Lịch sử đơn giá bình quân</h3>
      {history.status === "loading" ? (
        <LoadingState rows={2} />
      ) : history.status === "error" ? (
        <ErrorState message={history.message} onRetry={history.reload} />
      ) : history.data.items.length === 0 ? (
        <p className="text-sm text-muted">
          Chưa xác định — nguyên liệu chưa có phiếu nhập hợp lệ nào.
        </p>
      ) : (
        <>
          <Table>
            <caption className="sr-only">Lịch sử đơn giá bình quân</caption>
            <TableHeader>
              <TableRow>
                <TableHead>Thời điểm</TableHead>
                <TableHead>Chứng từ phát sinh</TableHead>
                <TableHead className="text-right">Đơn giá bình quân</TableHead>
                <TableHead className="text-right">Tồn sau giao dịch</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {history.data.items.map((row) => (
                <TableRow key={row.ThoiDiemHieuLuc}>
                  <TableCell className="tabular-nums">
                    {formatDateTime(row.ThoiDiemHieuLuc)}
                  </TableCell>
                  <TableCell>{row.ChungTu}</TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatVnd(row.DonGiaBinhQuan)}
                    {unit ? `/${unit}` : ""}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatNumber(row.SoLuongTon)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <DataPagination
            page={page}
            pageSize={PAGE_SIZE}
            total={history.data.total}
            onPageChange={setPage}
          />
        </>
      )}
    </section>
  );
}
