"use client";
import { Package, PackagePlus } from "lucide-react";
import { useCallback, useState } from "react";

import { DataPagination } from "@/components/data-pagination";
import { SearchFilter } from "@/components/filter-bar";
import {
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
} from "@/components/page-states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
import { formatNumber } from "@/lib/format";
import { useResource } from "@/lib/use-resource";
import { cn } from "@/lib/utils";
import { InventoryHistory } from "./inventory-history";

type StockRow = {
  MaNguyenLieu: number;
  TenNguyenLieu: string;
  DonViTinh?: string;
  SoLuongDuDieuKien?: number;
  SoLuongGiu?: number;
  SoLuongKhaDung?: number;
  ThoiDiemTinh?: string;
  SoLuongTon?: number;
  MucTonToiThieuApDung?: number;
  CanhBaoTonThap: boolean;
  HanSuDungGanNhat?: string | null;
  SoLoHetHan?: number;
  SoLoSapHetHan?: number;
  CanhBaoHanSuDung?: boolean;
};

type StockResponse = { items: StockRow[]; total?: number };

type Filter = "all" | "low";

const PAGE_SIZE = 20;

function queryOf(search: string, filter: Filter, page: number): string {
  const params = new URLSearchParams();
  if (search.trim()) params.set("search", search.trim());
  if (filter === "low") params.set("alerting", "true");
  params.set("page", String(page));
  params.set("page_size", String(PAGE_SIZE));
  return `/inventory/stock?${params.toString()}`;
}

function StockBadge({ row }: { row: StockRow }) {
  if (row.CanhBaoTonThap && (row.SoLuongKhaDung ?? row.SoLuongTon ?? 1) <= 0)
    return <Badge tone="danger">Hết hàng</Badge>;
  if (row.CanhBaoTonThap) return <Badge tone="warning">Sắp hết</Badge>;
  return <Badge tone="success">Đủ hàng</Badge>;
}

export function StockTable({
  onRestock,
}: {
  onRestock?: (ingredientId: number, name: string) => void;
} = {}) {
  const [filter, setFilter] = useState<Filter>("all");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<StockRow | null>(null);

  const fetchStock = useCallback(
    () => apiFetch<StockResponse>(queryOf(query, filter, page)),
    [query, filter, page],
  );
  const stock = useResource(fetchStock);

  function updateFilter(next: Filter) {
    setFilter(next);
    setPage(1);
  }

  function updateQuery(next: string) {
    setQuery(next);
    setPage(1);
  }

  const items = stock.status === "ready" ? stock.data.items : [];
  const total =
    stock.status === "ready" ? (stock.data.total ?? items.length) : 0;
  const filtered = query.trim() !== "" || filter !== "all";

  return (
    <div className="space-y-5">
      <PageHeader
        title="Tồn kho"
        description={
          stock.status === "ready"
            ? `${total} nguyên liệu.`
            : "Số lượng tồn của từng nguyên liệu so với mức tối thiểu."
        }
      />

      {items[0]?.ThoiDiemTinh && (
        <p className="text-muted">
          Dữ liệu lúc {items[0].ThoiDiemTinh}.{" "}
          <Button variant="ghost" size="sm" onClick={stock.reload}>
            Làm mới
          </Button>
        </p>
      )}

      {stock.status === "loading" ? (
        <LoadingState />
      ) : stock.status === "error" ? (
        <ErrorState message={stock.message} onRetry={stock.reload} />
      ) : items.length === 0 && !filtered ? (
        <EmptyState
          icon={Package}
          title="Chưa có tồn kho"
          description="Tồn kho xuất hiện sau phiếu nhập đầu tiên."
        />
      ) : (
        <>
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div
              role="tablist"
              aria-label="Lọc theo trạng thái"
              className="flex gap-1 border-b border-border"
            >
              {(
                [
                  ["all", "Tất cả"],
                  ["low", "Cần nhập thêm"],
                ] as const
              ).map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  role="tab"
                  aria-selected={filter === value}
                  onClick={() => updateFilter(value)}
                  className={cn(
                    "-mb-px border-b-2 px-3 pt-2 pb-2.5 font-medium transition-colors",
                    filter === value
                      ? "border-primary text-primary-subtle-fg"
                      : "border-transparent text-muted hover:text-ink",
                  )}
                >
                  {label}
                </button>
              ))}
            </div>
            <SearchFilter
              label="Tìm nguyên liệu"
              value={query}
              onChange={updateQuery}
            />
          </div>

          <Table>
            <caption className="sr-only">Tồn kho nguyên liệu</caption>
            <TableHeader>
              <TableRow>
                <TableHead>Nguyên liệu</TableHead>
                <TableHead>Đơn vị</TableHead>
                <TableHead className="text-right">Tồn sổ sách</TableHead>
                <TableHead className="text-right">Đủ điều kiện</TableHead>
                <TableHead className="text-right">Đang giữ</TableHead>
                <TableHead className="text-right">Khả dụng</TableHead>
                <TableHead className="text-right">Mức tối thiểu</TableHead>
                <TableHead>Hạn dùng gần nhất</TableHead>
                <TableHead>Trạng thái</TableHead>
                <TableHead>Chi tiết</TableHead>
                {onRestock ? (
                  <TableHead className="text-right">Thao tác</TableHead>
                ) : null}
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((it) => (
                <TableRow
                  key={it.MaNguyenLieu}
                  data-testid={it.CanhBaoTonThap ? "alert-row" : "ok-row"}
                >
                  <TableCell className="font-medium">
                    {it.TenNguyenLieu}
                  </TableCell>
                  <TableCell>{it.DonViTinh ?? "—"}</TableCell>
                  <TableCell
                    className={cn(
                      "text-right tabular-nums",
                      it.CanhBaoTonThap && "font-semibold text-danger-fg",
                    )}
                  >
                    {formatNumber(it.SoLuongTon)}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatNumber(it.SoLuongDuDieuKien)}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatNumber(it.SoLuongGiu)}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatNumber(it.SoLuongKhaDung)}
                  </TableCell>
                  <TableCell className="text-right text-muted tabular-nums">
                    {formatNumber(it.MucTonToiThieuApDung)}
                  </TableCell>
                  <TableCell>
                    {it.HanSuDungGanNhat ? (
                      <span className="flex flex-wrap items-center gap-1.5">
                        <span className="tabular-nums">
                          {it.HanSuDungGanNhat}
                        </span>
                        {it.SoLoHetHan ? (
                          <Badge tone="danger">
                            {it.SoLoHetHan} lô hết hạn
                          </Badge>
                        ) : null}
                        {it.SoLoSapHetHan ? (
                          <Badge tone="warning">
                            {it.SoLoSapHetHan} lô sắp hết hạn
                          </Badge>
                        ) : null}
                      </span>
                    ) : (
                      <span className="text-muted">—</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <StockBadge row={it} />
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      aria-label={`Xem lô và lịch sử ${it.TenNguyenLieu}`}
                      onClick={() => setSelected(it)}
                    >
                      Lô và lịch sử
                    </Button>
                  </TableCell>
                  {onRestock ? (
                    <TableCell className="text-right">
                      {it.CanhBaoTonThap ? (
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() =>
                            onRestock(it.MaNguyenLieu, it.TenNguyenLieu)
                          }
                        >
                          <PackagePlus aria-hidden />
                          Nhập thêm
                        </Button>
                      ) : null}
                    </TableCell>
                  ) : null}
                </TableRow>
              ))}
              {items.length === 0 && (
                <TableRow>
                  <TableCell
                    colSpan={onRestock ? 11 : 10}
                    className="py-8 text-center text-muted"
                  >
                    Không có nguyên liệu nào khớp bộ lọc.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>

          <DataPagination
            page={page}
            pageSize={PAGE_SIZE}
            total={total}
            onPageChange={setPage}
          />
        </>
      )}
      <Dialog
        open={selected !== null}
        onOpenChange={(open) => {
          if (!open) setSelected(null);
        }}
      >
        <DialogContent className="max-h-[90vh] overflow-auto sm:max-w-6xl">
          <DialogHeader>
            <DialogTitle>Lô và lịch sử — {selected?.TenNguyenLieu}</DialogTitle>
          </DialogHeader>
          {selected && (
            <InventoryHistory
              key={selected.MaNguyenLieu}
              ingredientId={selected.MaNguyenLieu}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
