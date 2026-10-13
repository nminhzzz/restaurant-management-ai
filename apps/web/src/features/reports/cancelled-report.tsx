"use client";

import { Ban } from "lucide-react";
import { useCallback, useState } from "react";

import {
  EmptyState,
  ErrorState,
  LoadingState,
  StatCard,
} from "@/components/page-states";
import { Bars } from "@/features/reports/chart";
import {
  currentMonth,
  DayPicker,
  GranularityPicker,
  GRANULARITIES,
  MonthPicker,
  today,
} from "@/features/reports/period-picker";
import { ReportTable } from "@/features/reports/report-table";
import { apiFetch } from "@/lib/api-client";
import {
  formatDate,
  formatDateTime,
  formatNumber,
  formatVnd,
} from "@/lib/format";
import { useResource } from "@/lib/use-resource";

type CancelledOrder = {
  MaOrder: number;
  MaOrderHienThi: string | null;
  TongTien: string;
  LyDoHuy: string | null;
};

type ClosedUnpaidOrder = {
  MaOrder: number;
  MaOrderHienThi: string | null;
  SoTienChuaThu: string;
  GiaVonDaTieuHao: string;
  LyDo: string | null;
  ThoiDiemDong: string | null;
};

type CancelledResponse = {
  SoLuong: number;
  TongGiaTri: string;
  items: CancelledOrder[];
  period?: { start: string; end: string; granularity: string };
  /** FR-REP-10 second group: never added to the cancelled totals above. */
  DongChuaThuDuocTien?: {
    SoLuong: number;
    TongSoTienChuaThu: string;
    TongGiaVonDaTieuHao: string;
    items: ClosedUnpaidOrder[];
  } | null;
};

const CANCELLED_GRANULARITIES = GRANULARITIES.filter((g) =>
  ["day", "week", "month"].includes(g.value),
);

const NO_REASON = "Không ghi lý do";

function byReason(
  items: CancelledOrder[],
): { reason: string; count: number; total: number }[] {
  const groups = new Map<string, { count: number; total: number }>();
  for (const item of items) {
    const reason = item.LyDoHuy?.trim() || NO_REASON;
    const group = groups.get(reason) ?? { count: 0, total: 0 };
    group.count += 1;
    group.total += Number(item.TongTien);
    groups.set(reason, group);
  }
  return [...groups.entries()]
    .map(([reason, group]) => ({ reason, ...group }))
    .sort((a, b) => b.count - a.count);
}

export function CancelledReport() {
  const [granularity, setGranularity] = useState("month");
  const [month, setMonth] = useState(currentMonth);
  const [day, setDay] = useState(today);
  const fetchCancelled = useCallback(
    () =>
      apiFetch<CancelledResponse>(
        granularity === "month"
          ? `/reports/cancelled-orders?granularity=month&month=${month}`
          : `/reports/cancelled-orders?granularity=${granularity}&anchor=${day}`,
      ),
    [granularity, month, day],
  );
  const cancelled = useResource(fetchCancelled);

  const toolbar = (
    <div className="flex flex-wrap items-end gap-4">
      <GranularityPicker
        value={granularity}
        onChange={setGranularity}
        options={CANCELLED_GRANULARITIES}
      />
      {granularity === "month" ? (
        <MonthPicker value={month} onChange={setMonth} />
      ) : (
        <DayPicker
          value={day}
          onChange={setDay}
          label={granularity === "week" ? "Một ngày trong tuần" : "Ngày"}
        />
      )}
    </div>
  );

  if (cancelled.status === "loading")
    return (
      <div className="space-y-4">
        {toolbar}
        <LoadingState />
      </div>
    );
  if (cancelled.status === "error")
    return (
      <div className="space-y-4">
        {toolbar}
        <ErrorState message={cancelled.message} onRetry={cancelled.reload} />
      </div>
    );

  const data = cancelled.data;

  return (
    <div className="space-y-4">
      {toolbar}
      <div className="grid gap-3 sm:grid-cols-2">
        <StatCard label="Số order bị hủy" value={formatNumber(data.SoLuong)} />
        <StatCard
          label="Tổng giá trị order hủy"
          value={formatVnd(data.TongGiaTri)}
        />
      </div>

      {data.period ? (
        <p className="text-muted tabular-nums">
          {formatDate(data.period.start)} đến {formatDate(data.period.end)}
        </p>
      ) : null}

      {data.items.length === 0 ? (
        <EmptyState
          icon={Ban}
          title="Không có order nào bị hủy trong kỳ"
          description="Chọn kỳ khác để xem lại."
        />
      ) : (
        <>
          {(() => {
            const reasons = byReason(data.items);
            return (
              <section className="space-y-3 rounded-container border border-border bg-surface p-4">
                <h2 className="text-[15px] font-bold">Lý do hủy</h2>
                <Bars
                  items={reasons.map((r) => ({
                    key: r.reason,
                    label: r.reason,
                    value: r.count,
                  }))}
                  ariaLabel="Biểu đồ số order hủy theo lý do"
                  tickFormat={(t) => formatNumber(t)}
                  tooltipFormat={(item) =>
                    `${item.label}: ${formatNumber(item.value)} order`
                  }
                  colorAt={(_, isPeak) =>
                    isPeak ? "var(--color-danger)" : "var(--color-chart-5)"
                  }
                />
                <ReportTable
                  headers={["Lý do", "Số order", "Giá trị"]}
                  rows={reasons.map((r) => [
                    r.reason,
                    formatNumber(r.count),
                    formatVnd(r.total),
                  ])}
                  pageSize={10}
                />
              </section>
            );
          })()}
          <section className="space-y-3">
            <h2 className="text-[15px] font-bold">Danh sách order hủy</h2>
            <ReportTable
              headers={["Order", "Giá trị", "Lý do"]}
              rows={data.items.map((item) => [
                item.MaOrderHienThi ?? `#${item.MaOrder}`,
                formatVnd(item.TongTien),
                item.LyDoHuy?.trim() || NO_REASON,
              ])}
              pageSize={10}
              searchLabel="Tìm theo lý do"
              searchColumn={2}
            />
          </section>
        </>
      )}

      {data.DongChuaThuDuocTien ? (
        <section
          aria-label="Order đóng chưa thu được tiền"
          className="space-y-3 rounded-container border border-border bg-surface p-4"
        >
          <div>
            <h2 className="text-[15px] font-bold">
              Order đóng chưa thu được tiền
            </h2>
            <p className="text-xs text-subtle">
              Nhóm riêng, không cộng vào số order hủy ở trên và không tính vào
              doanh thu.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <StatCard
              label="Số order"
              value={formatNumber(data.DongChuaThuDuocTien.SoLuong)}
            />
            <StatCard
              label="Số tiền chưa thu"
              value={formatVnd(data.DongChuaThuDuocTien.TongSoTienChuaThu)}
            />
            <StatCard
              label="Giá vốn đã tiêu hao"
              value={formatVnd(data.DongChuaThuDuocTien.TongGiaVonDaTieuHao)}
            />
          </div>
          {data.DongChuaThuDuocTien.items.length > 0 ? (
            <ReportTable
              headers={[
                "Order",
                "Số tiền chưa thu",
                "Giá vốn đã tiêu hao",
                "Lý do",
                "Đóng lúc",
              ]}
              rows={data.DongChuaThuDuocTien.items.map((item) => [
                item.MaOrderHienThi ?? `#${item.MaOrder}`,
                formatVnd(item.SoTienChuaThu),
                formatVnd(item.GiaVonDaTieuHao),
                item.LyDo?.trim() || NO_REASON,
                formatDateTime(item.ThoiDiemDong),
              ])}
              pageSize={10}
            />
          ) : (
            <p className="text-muted">
              Không có order nào đóng chưa thu được tiền trong kỳ.
            </p>
          )}
        </section>
      ) : null}
    </div>
  );
}
