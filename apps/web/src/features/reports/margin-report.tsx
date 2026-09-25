"use client";

import { useCallback, useState } from "react";

import { ConfirmDialog } from "@/components/confirm-dialog";
import { ErrorState, LoadingState, StatCard } from "@/components/page-states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Bars } from "@/features/reports/chart";
import { currentMonth, MonthPicker } from "@/features/reports/period-picker";
import { ReportTable } from "@/features/reports/report-table";
import { apiFetch } from "@/lib/api-client";
import { formatNumber, formatVnd } from "@/lib/format";
import { useAction } from "@/lib/use-action";
import { useResource } from "@/lib/use-resource";

type MarginResponse = {
  DoanhThu: string;
  GiaVon: string;
  BienLoiNhuanGop: string;
};

type CostBreakdownResponse = {
  NguyenLieu: string;
  HaoHut: string;
  TongGiaVon: string;
  TamTinh: boolean;
  SoDongChuaTinhGiaVon: number;
};

type DishCostResponse = {
  items: { MaMon: number; TenMon: string; GiaVon: string }[];
};

type MonthlyProfit = {
  margin: MarginResponse;
  costs: CostBreakdownResponse;
  dishCosts: DishCostResponse;
};

export function MarginReport() {
  const [month, setMonth] = useState(currentMonth);
  const fetchProfit = useCallback(async (): Promise<MonthlyProfit> => {
    const [margin, costs, dishCosts] = await Promise.all([
      apiFetch<MarginResponse>(`/reports/margin?month=${month}`),
      apiFetch<CostBreakdownResponse>(`/reports/costs?month=${month}`),
      apiFetch<DishCostResponse>(`/reports/costs/dishes?month=${month}`),
    ]);
    return { margin, costs, dishCosts };
  }, [month]);
  const profit = useResource(fetchProfit);
  const closing = useAction();
  const [confirmClose, setConfirmClose] = useState(false);

  async function closeMonth() {
    // The API keys months as YYYYMM; the picker yields "YYYY-MM".
    const key = month.replace("-", "");
    const result = await closing.run(
      () => apiFetch(`/inventory/costing/${key}/close`, { method: "POST" }),
      `Đã chốt giá vốn tháng ${month}.`,
    );
    if (result !== undefined) {
      setConfirmClose(false);
      profit.reload();
    }
  }

  const toolbar = (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <MonthPicker value={month} onChange={setMonth} />
      <Button variant="secondary" onClick={() => setConfirmClose(true)}>
        Chốt giá vốn tháng
      </Button>
      <ConfirmDialog
        open={confirmClose}
        onOpenChange={setConfirmClose}
        title={`Chốt giá vốn tháng ${month}`}
        description="Tính đơn giá bình quân gia quyền của từng nguyên liệu theo các phiếu nhập trong tháng, rồi tính giá cho các dòng xuất hủy còn tạm tính. Chốt lại lần nữa sẽ tính lại theo số liệu mới nhất."
        confirmLabel="Chốt giá vốn"
        pending={closing.pending}
        onConfirm={closeMonth}
      />
    </div>
  );

  if (profit.status === "loading")
    return (
      <div className="space-y-4">
        {toolbar}
        <LoadingState />
      </div>
    );
  if (profit.status === "error")
    return (
      <div className="space-y-4">
        {toolbar}
        <ErrorState message={profit.message} onRetry={profit.reload} />
      </div>
    );

  const { margin, costs, dishCosts } = profit.data;
  const revenue = Number(margin.DoanhThu);
  const marginPercent =
    revenue !== 0 ? (Number(margin.BienLoiNhuanGop) / revenue) * 100 : null;

  const costItems = [
    {
      key: "NguyenLieu",
      label: "Nguyên liệu",
      value: Number(costs.NguyenLieu),
    },
    { key: "HaoHut", label: "Hao hụt", value: Number(costs.HaoHut) },
  ];

  const dishItems = [...dishCosts.items]
    .sort((a, b) => Number(b.GiaVon) - Number(a.GiaVon))
    .slice(0, 10)
    .map((dish) => ({
      key: dish.MaMon,
      label:
        dish.TenMon.length > 10 ? `${dish.TenMon.slice(0, 9)}…` : dish.TenMon,
      value: Number(dish.GiaVon),
    }));

  return (
    <div className="space-y-4">
      {toolbar}

      <div className="grid gap-3 sm:grid-cols-3">
        <StatCard label="Doanh thu" value={formatVnd(margin.DoanhThu)} />
        <StatCard label="Giá vốn" value={formatVnd(margin.GiaVon)} />
        <StatCard
          label="Biên lợi nhuận gộp"
          value={formatVnd(margin.BienLoiNhuanGop)}
          hint={
            marginPercent === null
              ? "Chưa có doanh thu trong tháng"
              : `${formatNumber(marginPercent)}% doanh thu`
          }
        />
      </div>

      <section className="space-y-3 rounded-container border border-border bg-surface p-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-[15px] font-semibold">Cơ cấu giá vốn</h2>
          {costs.TamTinh ? <Badge tone="warning">Tạm tính</Badge> : null}
        </div>
        {costs.TamTinh ? (
          <p className="text-warning-fg">
            Còn {formatNumber(costs.SoDongChuaTinhGiaVon)} dòng xuất hủy chưa
            được tính giá vốn trong tháng này, số liệu giá vốn và lợi nhuận trên
            đây chỉ là tạm tính.
          </p>
        ) : null}
        <Bars
          items={costItems}
          ariaLabel={`Biểu đồ cơ cấu giá vốn, tổng ${formatVnd(costs.TongGiaVon)}`}
          tickFormat={(t) => `${formatNumber(t / 1_000_000)}tr`}
          tooltipFormat={(item) => `${item.label}: ${formatVnd(item.value)}`}
        />
        <ReportTable
          headers={["Khoản mục", "Giá trị"]}
          rows={[
            ["Nguyên liệu", formatVnd(costs.NguyenLieu)],
            ["Hao hụt", formatVnd(costs.HaoHut)],
            ["Tổng giá vốn", formatVnd(costs.TongGiaVon)],
          ]}
        />
      </section>

      <section className="space-y-3 rounded-container border border-border bg-surface p-4">
        <h2 className="text-[15px] font-semibold">
          Giá vốn theo món (tham khảo)
        </h2>
        <p className="text-xs text-subtle">
          Chỉ tính chi phí nguyên liệu cho từng món, không trừ hao hụt và không
          phải là lợi nhuận từng món.
        </p>
        {dishItems.length === 0 ? (
          <p className="text-muted">Chưa có món nào được bán trong tháng.</p>
        ) : (
          <Bars
            items={dishItems}
            ariaLabel="Biểu đồ giá vốn nguyên liệu theo món, cao nhất trước"
            tickFormat={(t) => `${formatNumber(t / 1_000_000)}tr`}
            tooltipFormat={(item) => `${item.label}: ${formatVnd(item.value)}`}
          />
        )}
        <ReportTable
          headers={["Món", "Giá vốn nguyên liệu"]}
          rows={dishCosts.items.map((dish) => [
            dish.TenMon,
            formatVnd(dish.GiaVon),
          ])}
        />
      </section>
    </div>
  );
}
