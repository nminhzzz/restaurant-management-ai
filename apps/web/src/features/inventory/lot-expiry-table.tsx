"use client";

import { Boxes } from "lucide-react";
import { useCallback, useState } from "react";

import { DataPagination } from "@/components/data-pagination";
import {
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
} from "@/components/page-states";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { apiFetch } from "@/lib/api-client";
import { formatDate, formatNumber } from "@/lib/format";
import { useResource } from "@/lib/use-resource";

type LotRow = {
  MaLoNguyenLieu: number;
  MaNguyenLieu: number;
  TenNguyenLieu: string;
  SoLuongConLai: number;
  HanSuDung: string | null;
  SoNgayConLai?: number | null;
  TrangThaiHanSuDung: "Còn hạn" | "Sắp hết hạn" | "Hết hạn" | "Đã dùng hết";
};

type LotPage = {
  items: LotRow[];
  total: number;
  page: number;
  page_size: number;
};
const PAGE_SIZE = 20;

export function LotExpiryTable() {
  const [page, setPage] = useState(1);
  const fetchLots = useCallback(
    () =>
      apiFetch<LotPage>(`/inventory/lots?page=${page}&page_size=${PAGE_SIZE}`),
    [page],
  );
  const lots = useResource(fetchLots);

  return (
    <div className="space-y-5">
      <PageHeader
        title="Hạn sử dụng theo lô"
        description="Ngày hết hạn của từng lô nguyên liệu theo ngày hiện tại."
      />
      {lots.status === "loading" ||
      (lots.status === "ready" && lots.data.page !== page) ? (
        <LoadingState />
      ) : lots.status === "error" ? (
        <ErrorState message={lots.message} onRetry={lots.reload} />
      ) : lots.data.items.length === 0 && lots.data.total === 0 ? (
        <EmptyState
          icon={Boxes}
          title="Chưa có lô nguyên liệu"
          description="Lô nguyên liệu xuất hiện sau phiếu nhập đầu tiên."
        />
      ) : (
        <>
          <Table>
            <caption className="sr-only">Hạn sử dụng theo lô</caption>
            <TableHeader>
              <TableRow>
                <TableHead>Mã lô</TableHead>
                <TableHead>Nguyên liệu</TableHead>
                <TableHead className="text-right">Số lượng còn lại</TableHead>
                <TableHead>Hạn sử dụng</TableHead>
                <TableHead>Trạng thái hạn dùng</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {lots.data.items.map((lot) => (
                <TableRow key={lot.MaLoNguyenLieu}>
                  <TableCell>{lot.MaLoNguyenLieu}</TableCell>
                  <TableCell className="font-medium">
                    {lot.TenNguyenLieu}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatNumber(lot.SoLuongConLai)}
                  </TableCell>
                  <TableCell>
                    {formatDate(lot.HanSuDung)}
                    {lot.SoNgayConLai != null &&
                      lot.TrangThaiHanSuDung !== "Đã dùng hết" && (
                        <span className="block text-xs text-muted">
                          {lot.SoNgayConLai >= 0
                            ? `Còn ${lot.SoNgayConLai} ngày`
                            : `Quá hạn ${-lot.SoNgayConLai} ngày`}
                        </span>
                      )}
                  </TableCell>
                  <TableCell>
                    <Badge
                      tone={
                        lot.TrangThaiHanSuDung === "Hết hạn"
                          ? "danger"
                          : lot.TrangThaiHanSuDung === "Sắp hết hạn"
                            ? "warning"
                            : lot.TrangThaiHanSuDung === "Đã dùng hết"
                              ? "neutral"
                              : "success"
                      }
                    >
                      {lot.TrangThaiHanSuDung}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <DataPagination
            page={page}
            pageSize={PAGE_SIZE}
            total={lots.data.total}
            onPageChange={setPage}
          />
        </>
      )}
    </div>
  );
}
