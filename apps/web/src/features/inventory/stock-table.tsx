"use client";
import { Package, PackagePlus, Search } from "lucide-react";
import { useState } from "react";

import {
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
} from "@/components/page-states";
import { Badge } from "@/components/ui/badge";
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
import { cn } from "@/lib/utils";

type StockRow = {
  MaNguyenLieu: number;
  TenNguyenLieu: string;
  SoLuongTon?: number;
  MucTonToiThieuApDung?: number;
  CanhBaoTonThap: boolean;
};

type Filter = "all" | "low";

const loadStock = () =>
  apiFetch<{ items: StockRow[] }>("/inventory/stock").then(
    (d) => d.items || [],
  );

function StockBadge({ row }: { row: StockRow }) {
  if (row.CanhBaoTonThap && (row.SoLuongTon ?? 1) <= 0)
    return <Badge tone="danger">Hết hàng</Badge>;
  if (row.CanhBaoTonThap) return <Badge tone="warning">Sắp hết</Badge>;
  return <Badge tone="success">Đủ hàng</Badge>;
}

export function StockTable({
  onRestock,
}: {
  onRestock?: (ingredientId: number, name: string) => void;
} = {}) {
  const stock = useResource(loadStock);
  const [filter, setFilter] = useState<Filter>("all");
  const [query, setQuery] = useState("");

  const items = stock.status === "ready" ? stock.data : [];
  const lowCount = items.filter((it) => it.CanhBaoTonThap).length;
  const visible = items.filter(
    (it) =>
      (filter === "all" || it.CanhBaoTonThap) &&
      it.TenNguyenLieu.toLowerCase().includes(query.trim().toLowerCase()),
  );

  return (
    <div className="space-y-5">
      <PageHeader
        title="Tồn kho"
        description={
          stock.status === "ready" && items.length > 0
            ? `${items.length} nguyên liệu, ${lowCount} dưới mức tối thiểu.`
            : "Số lượng tồn của từng nguyên liệu so với mức tối thiểu."
        }
      />

      {stock.status === "loading" ? (
        <LoadingState />
      ) : stock.status === "error" ? (
        <ErrorState message={stock.message} onRetry={stock.reload} />
      ) : items.length === 0 ? (
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
                  ["all", "Tất cả", items.length],
                  ["low", "Cần nhập thêm", lowCount],
                ] as const
              ).map(([value, label, count]) => (
                <button
                  key={value}
                  type="button"
                  role="tab"
                  aria-selected={filter === value}
                  onClick={() => setFilter(value)}
                  className={cn(
                    "-mb-px border-b-2 px-3 pt-2 pb-2.5 font-medium transition-colors",
                    filter === value
                      ? "border-primary text-primary-subtle-fg"
                      : "border-transparent text-muted hover:text-ink",
                  )}
                >
                  {label}
                  <span className="ml-1.5 font-normal text-subtle tabular-nums">
                    {count}
                  </span>
                </button>
              ))}
            </div>
            <div className="relative w-full max-w-xs">
              <Search
                className="absolute top-2.5 left-2.5 size-4 text-subtle"
                aria-hidden
              />
              <Input
                type="search"
                aria-label="Tìm nguyên liệu"
                placeholder="Tìm nguyên liệu"
                className="pl-8"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>
          </div>

          <Table>
            <caption className="sr-only">Tồn kho nguyên liệu</caption>
            <TableHeader>
              <TableRow>
                <TableHead>Nguyên liệu</TableHead>
                <TableHead className="text-right">Tồn hiện tại</TableHead>
                <TableHead className="text-right">Mức tối thiểu</TableHead>
                <TableHead>Trạng thái</TableHead>
                {onRestock ? (
                  <TableHead className="text-right">Thao tác</TableHead>
                ) : null}
              </TableRow>
            </TableHeader>
            <TableBody>
              {visible.map((it) => (
                <TableRow
                  key={it.MaNguyenLieu}
                  data-testid={it.CanhBaoTonThap ? "alert-row" : "ok-row"}
                >
                  <TableCell className="font-medium">
                    {it.TenNguyenLieu}
                  </TableCell>
                  <TableCell
                    className={cn(
                      "text-right tabular-nums",
                      it.CanhBaoTonThap && "font-semibold text-danger-fg",
                    )}
                  >
                    {formatNumber(it.SoLuongTon)}
                  </TableCell>
                  <TableCell className="text-right text-muted tabular-nums">
                    {formatNumber(it.MucTonToiThieuApDung)}
                  </TableCell>
                  <TableCell>
                    <StockBadge row={it} />
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
              {visible.length === 0 && (
                <TableRow>
                  <TableCell
                    colSpan={onRestock ? 5 : 4}
                    className="py-8 text-center text-muted"
                  >
                    Không có nguyên liệu nào khớp bộ lọc.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </>
      )}
    </div>
  );
}
