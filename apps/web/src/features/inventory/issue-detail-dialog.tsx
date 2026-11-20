"use client";

import { useCallback } from "react";

import { ErrorState, LoadingState } from "@/components/page-states";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { apiFetch } from "@/lib/api-client";
import {
  formatDate,
  formatDateTime,
  formatNumber,
  formatVnd,
} from "@/lib/format";
import { useResource } from "@/lib/use-resource";

type IssueDetail = {
  MaPhieuXuat: number;
  LyDo: string;
  TrangThai: string;
  NgayTao: string | null;
  Nguon: string;
  MaPhieuKiemKe: number | null;
  GhiChu: string | null;
  NguoiLap: number | null;
  TenNguoiLap: string | null;
  TenNguoiDuyet: string | null;
  NgayDuyet: string | null;
  lines: {
    MaChiTietXuat: number;
    TenNguyenLieu: string;
    DonViTinh: string;
    SoLuong: number;
    GiaVonUocTinh: number | null;
    MaLoNguyenLieu: number | null;
    HanSuDung: string | null;
    MaChiTietOrder: number | null;
    SoSuat: number | null;
  }[];
};

export function IssueDetailDialog({
  issueId,
  onClose,
}: {
  issueId: number;
  onClose: () => void;
}) {
  const load = useCallback(
    () => apiFetch<IssueDetail>(`/inventory/issues/${issueId}`),
    [issueId],
  );
  const detail = useResource(load);

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="w-[min(42rem,calc(100vw-2rem))]">
        <DialogHeader>
          <DialogTitle>Phiếu xuất #{issueId}</DialogTitle>
        </DialogHeader>
        {detail.status === "loading" ? (
          <LoadingState rows={3} />
        ) : detail.status === "error" ? (
          <ErrorState message={detail.message} onRetry={detail.reload} />
        ) : (
          <div className="space-y-3">
            <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-sm">
              <dt className="text-muted">Lý do</dt>
              <dd>{detail.data.LyDo}</dd>
              <dt className="text-muted">Nguồn</dt>
              <dd>{detail.data.Nguon}</dd>
              <dt className="text-muted">Thời điểm</dt>
              <dd>{formatDateTime(detail.data.NgayTao)}</dd>
              <dt className="text-muted">Trạng thái</dt>
              <dd>{detail.data.TrangThai}</dd>
              <dt className="text-muted">Người lập</dt>
              <dd>
                {detail.data.NguoiLap === null
                  ? "Hệ thống"
                  : (detail.data.TenNguoiLap ?? `#${detail.data.NguoiLap}`)}
              </dd>
              {detail.data.TenNguoiDuyet && (
                <>
                  <dt className="text-muted">Người duyệt</dt>
                  <dd>{detail.data.TenNguoiDuyet}</dd>
                </>
              )}
              {detail.data.NgayDuyet && (
                <>
                  <dt className="text-muted">Thời điểm duyệt</dt>
                  <dd>{formatDateTime(detail.data.NgayDuyet)}</dd>
                </>
              )}
              {detail.data.MaPhieuKiemKe !== null && (
                <>
                  <dt className="text-muted">Phiếu kiểm kê</dt>
                  <dd>#{detail.data.MaPhieuKiemKe}</dd>
                </>
              )}
              {detail.data.GhiChu && (
                <>
                  <dt className="text-muted">Ghi chú</dt>
                  <dd>{detail.data.GhiChu}</dd>
                </>
              )}
            </dl>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nguyên liệu</TableHead>
                  <TableHead className="text-right">Số lượng</TableHead>
                  <TableHead className="text-right">Giá vốn</TableHead>
                  <TableHead>Lô</TableHead>
                  <TableHead>Nguồn dòng</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {detail.data.lines.map((line) => (
                  <TableRow key={line.MaChiTietXuat}>
                    <TableCell>
                      {line.TenNguyenLieu} ({line.DonViTinh})
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {formatNumber(line.SoLuong)}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {line.GiaVonUocTinh === null
                        ? "Chưa xác định"
                        : formatVnd(line.GiaVonUocTinh)}
                    </TableCell>
                    <TableCell>
                      {line.MaLoNguyenLieu === null
                        ? "—"
                        : `#${line.MaLoNguyenLieu}` +
                          (line.HanSuDung
                            ? ` · HSD ${formatDate(line.HanSuDung)}`
                            : "")}
                    </TableCell>
                    <TableCell>
                      {line.MaChiTietOrder !== null
                        ? `Dòng món #${line.MaChiTietOrder}` +
                          (line.SoSuat ? ` · ${line.SoSuat} suất` : "")
                        : "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
