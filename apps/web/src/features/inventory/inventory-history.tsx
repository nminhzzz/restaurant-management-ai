"use client";

import { useCallback, useState } from "react";

import { DataPagination } from "@/components/data-pagination";
import { DateRangeFilter, SelectFilter } from "@/components/filter-bar";
import { ErrorState, LoadingState } from "@/components/page-states";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { apiFetch } from "@/lib/api-client";
import { formatNumber } from "@/lib/format";
import { useResource } from "@/lib/use-resource";

export type LotRow = {
  MaLoNguyenLieu: number;
  MaNguyenLieu: number;
  TenNguyenLieu: string;
  DonViTinh: string;
  NgayNhap: string;
  HanSuDung: string | null;
  SoLuongConLai: number;
  SoLuongGiu: number;
  SoLuongKhaDung: number;
  TrangThai: string;
};

type MovementRow = {
  MaGiaoDichKho: number;
  TenNguyenLieu: string;
  DonViTinh: string;
  MaLoNguyenLieu: number | null;
  LoaiGiaoDich: string;
  SoLuongThayDoi: number;
  ThoiDiem: string;
  BusinessDate: string;
  MaChiTietNhap: number | null;
  MaChiTietOrder: number | null;
  MaChiTietXuat: number | null;
  MaChiTietKiemKe: number | null;
};

type Page<T> = { items: T[]; total: number };
const PAGE_SIZE = 20;
const KINDS = [
  "Nhập",
  "Trừ tự động",
  "Hoàn kho",
  "Xuất thủ công",
  "Điều chỉnh kiểm kê",
];

export function InventoryHistory({ ingredientId }: { ingredientId?: number }) {
  const [view, setView] = useState<"lots" | "movements">("lots");
  const [lotId, setLotId] = useState<number | undefined>();
  const [kind, setKind] = useState("");
  const [orderLineId, setOrderLineId] = useState("");
  const [status, setStatus] = useState("");
  const [range, setRange] = useState({ from: "", to: "" });
  const [page, setPage] = useState(1);
  const load = useCallback(() => {
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(PAGE_SIZE),
    });
    if (ingredientId !== undefined)
      params.set("ingredient_id", String(ingredientId));
    if (view === "lots" && status) params.set("status", status);
    if (view === "movements") {
      if (lotId !== undefined) params.set("lot_id", String(lotId));
      if (kind) params.set("kind", kind);
      if (orderLineId.trim()) params.set("order_line_id", orderLineId.trim());
      if (range.from) params.set("date_from", range.from);
      if (range.to) params.set("date_to", range.to);
    }
    return apiFetch<Page<LotRow | MovementRow>>(`/inventory/${view}?${params}`);
  }, [ingredientId, view, lotId, status, kind, orderLineId, range, page]);
  const resource = useResource(load);
  function changeView(next: "lots" | "movements") {
    setView(next);
    setPage(1);
    setLotId(undefined);
  }
  return (
    <div className="space-y-4">
      <div
        className="flex flex-wrap gap-2"
        role="group"
        aria-label="Nội dung tra cứu kho"
      >
        <Button
          variant={view === "lots" ? "primary" : "secondary"}
          onClick={() => changeView("lots")}
        >
          Chi tiết lô
        </Button>
        <Button
          variant={view === "movements" ? "primary" : "secondary"}
          onClick={() => changeView("movements")}
        >
          Lịch sử nhập, xuất và hoàn
        </Button>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        {view === "lots" ? (
          <SelectFilter
            label="Trạng thái lô"
            value={status}
            allLabel="Tất cả lô"
            options={["Còn hạn", "Sắp hết hạn", "Hết hạn", "Đã hết"].map(
              (value) => ({
                value,
                label: value,
              }),
            )}
            onChange={(value) => {
              setStatus(value);
              setPage(1);
            }}
          />
        ) : (
          <>
            <SelectFilter
              label="Loại biến động"
              value={kind}
              allLabel="Tất cả biến động"
              options={KINDS.map((value) => ({ value, label: value }))}
              onChange={(value) => {
                setKind(value);
                setPage(1);
              }}
            />
            <label className="grid gap-1 text-xs text-subtle">
              <span>Mã dòng món</span>
              <Input
                aria-label="Mã dòng món"
                type="number"
                min={1}
                className="h-9 w-36"
                value={orderLineId}
                onChange={(e) => {
                  setOrderLineId(e.target.value);
                  setPage(1);
                }}
                placeholder="Ví dụ: 42"
              />
            </label>
            <DateRangeFilter
              from={range.from}
              to={range.to}
              onChange={(value) => {
                setRange(value);
                setPage(1);
              }}
            />
            {lotId !== undefined && (
              <Button
                variant="ghost"
                onClick={() => {
                  setLotId(undefined);
                  setPage(1);
                }}
              >
                Bỏ lọc lô #{lotId}
              </Button>
            )}
          </>
        )}
        <Button variant="secondary" onClick={resource.reload}>
          Làm mới
        </Button>
      </div>
      {resource.status === "loading" ? (
        <LoadingState />
      ) : resource.status === "error" ? (
        <ErrorState message={resource.message} onRetry={resource.reload} />
      ) : (
        <>
          <Table>
            <caption className="sr-only">
              {view === "lots" ? "Chi tiết lô nguyên liệu" : "Sổ biến động kho"}
            </caption>
            <TableHeader>
              <TableRow>
                {(view === "lots"
                  ? [
                      "Lô",
                      "Nguyên liệu",
                      "Ngày nhập",
                      "Hạn dùng",
                      "Còn lại",
                      "Đang giữ",
                      "Khả dụng",
                      "Trạng thái",
                      "Thao tác",
                    ]
                  : [
                      "Thời điểm",
                      "Ngày kinh doanh",
                      "Nguyên liệu",
                      "Lô",
                      "Loại",
                      "Số lượng",
                      "Chứng từ nguồn",
                    ]
                ).map((label) => (
                  <TableHead key={label}>{label}</TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {resource.data.items.map((row) =>
                "MaGiaoDichKho" in row ? (
                  <TableRow key={row.MaGiaoDichKho}>
                    <TableCell>{row.ThoiDiem}</TableCell>
                    <TableCell>{row.BusinessDate}</TableCell>
                    <TableCell>{row.TenNguyenLieu}</TableCell>
                    <TableCell>
                      {row.MaLoNguyenLieu ? `#${row.MaLoNguyenLieu}` : "—"}
                    </TableCell>
                    <TableCell>{row.LoaiGiaoDich}</TableCell>
                    <TableCell>
                      {formatNumber(row.SoLuongThayDoi)} {row.DonViTinh}
                    </TableCell>
                    <TableCell>
                      {row.MaChiTietOrder
                        ? `Dòng món #${row.MaChiTietOrder}`
                        : row.MaChiTietNhap
                          ? `Dòng nhập #${row.MaChiTietNhap}`
                          : row.MaChiTietXuat
                            ? `Dòng xuất #${row.MaChiTietXuat}`
                            : row.MaChiTietKiemKe
                              ? `Dòng kiểm kê #${row.MaChiTietKiemKe}`
                              : "—"}
                    </TableCell>
                  </TableRow>
                ) : (
                  <TableRow key={row.MaLoNguyenLieu}>
                    <TableCell>#{row.MaLoNguyenLieu}</TableCell>
                    <TableCell>
                      {row.TenNguyenLieu} ({row.DonViTinh})
                    </TableCell>
                    <TableCell>{row.NgayNhap}</TableCell>
                    <TableCell>
                      {row.HanSuDung ?? "Không quản lý hạn"}
                    </TableCell>
                    <TableCell>{formatNumber(row.SoLuongConLai)}</TableCell>
                    <TableCell>{formatNumber(row.SoLuongGiu)}</TableCell>
                    <TableCell>{formatNumber(row.SoLuongKhaDung)}</TableCell>
                    <TableCell>{row.TrangThai}</TableCell>
                    <TableCell>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          setLotId(row.MaLoNguyenLieu);
                          setView("movements");
                          setPage(1);
                        }}
                      >
                        Xem biến động lô #{row.MaLoNguyenLieu}
                      </Button>
                    </TableCell>
                  </TableRow>
                ),
              )}
              {resource.data.items.length === 0 && (
                <TableRow>
                  <TableCell colSpan={view === "lots" ? 9 : 7}>
                    Chưa có dữ liệu khớp bộ lọc.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
          <DataPagination
            page={page}
            pageSize={PAGE_SIZE}
            total={resource.data.total}
            onPageChange={setPage}
          />
        </>
      )}
    </div>
  );
}
