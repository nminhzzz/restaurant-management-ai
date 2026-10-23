"use client";

import { Clock, TriangleAlert } from "lucide-react";
import { useCallback, useState } from "react";

import { EmptyState, ErrorState, LoadingState } from "@/components/page-states";
import { Button } from "@/components/ui/button";
import { MonthPicker, currentMonth } from "@/features/reports/period-picker";
import { Bars } from "@/features/reports/chart";
import { ReportTable } from "@/features/reports/report-table";
import { apiFetch } from "@/lib/api-client";
import { formatDateTime, formatNumber, formatVnd } from "@/lib/format";
import { useAction } from "@/lib/use-action";
import { useResource } from "@/lib/use-resource";

type PendingPayment = {
  MaOrder: number;
  MaOrderHienThi: string | null;
  MaGiaoDich: number;
  PhuongThuc: string;
  SoTien: string;
  TrangThai: string;
  ThoiGianChoPhut: number;
  KetQuaGanNhat: string | null;
  LichSu?: {
    ThoiDiem: string | null;
    HanhDong: string;
    GhiChu: string | null;
    KetQua: string | null;
  }[];
};

type PaymentException = {
  MaNgoaiLe: number;
  MaOrder: number | null;
  MaOrderHienThi: string | null;
  MaGiaoDich: number | null;
  MaGiaoDichCong: string;
  SoTien: string;
  TrangThai: string;
  LyDo: string | null;
  GhiChu: string | null;
  MaThamChieuHoan: string | null;
  SoTienHoan: string | null;
  ThoiDiemTao: string | null;
  ThoiDiemXuLy: string | null;
};

type ReviewData = {
  pending: PendingPayment[];
  exceptions: PaymentException[];
};

function orderLabel(code: string | null, id: number | null): string {
  if (code) return code;
  return id === null ? "Không xác định" : `#${id}`;
}

/** FR-REP-02 + FR-SALE-17: money still waiting, and transfers a manager must resolve. */
export function PaymentReview() {
  const [month, setMonth] = useState(currentMonth);
  const [status, setStatus] = useState<"Chờ xử lý" | "">("Chờ xử lý");
  const { run, pending: busy, error: actionError } = useAction();

  const fetcher = useCallback(async (): Promise<ReviewData> => {
    const [pending, exceptions] = await Promise.all([
      apiFetch<{ items: PendingPayment[] }>(
        `/reports/pending-payments?month=${month}`,
      ),
      apiFetch<{ items: PaymentException[] }>(
        `/sales/payment-exceptions${status ? `?status=${encodeURIComponent(status)}` : ""}`,
      ),
    ]);
    return { pending: pending.items, exceptions: exceptions.items };
  }, [month, status]);
  const resource = useResource(fetcher);

  const resolve = (
    exception: PaymentException,
    outcome: "applied" | "refunded",
  ) =>
    run(
      async () => {
        let body: Record<string, unknown> = { outcome, note: null };
        if (outcome === "refunded") {
          // FR-SALE-17(c): record the bank/cash-voucher reference and how much
          // actually went back, not just a free-text note.
          const reference = window.prompt(
            "Mã tham chiếu hoàn tiền (giao dịch ngân hàng hoặc phiếu chi, bắt buộc):",
          );
          if (!reference?.trim()) return;
          const amount = window.prompt("Số tiền đã hoàn:", exception.SoTien);
          if (amount === null) return;
          const note = window.prompt("Ghi chú hoàn tiền (bắt buộc):");
          if (!note?.trim()) return;
          body = {
            outcome,
            note,
            refund_ref: reference.trim(),
            refund_amount: amount.trim() || exception.SoTien,
          };
        }
        await apiFetch(
          `/sales/payment-exceptions/${exception.MaNgoaiLe}/resolve`,
          {
            method: "POST",
            body,
          },
        );
        await resource.reload();
      },
      outcome === "applied"
        ? "Đã áp dụng khoản tiền và phát hành hóa đơn."
        : "Đã ghi nhận hoàn tiền ngoài hệ thống.",
    );

  const toolbar = (
    <div className="flex flex-wrap items-center justify-between gap-2">
      <MonthPicker value={month} onChange={setMonth} />
      <label className="flex items-center gap-2 text-sm text-muted">
        Ngoại lệ
        <select
          aria-label="Lọc ngoại lệ theo trạng thái"
          className="h-9 rounded-control border border-border-strong bg-surface px-2"
          value={status}
          onChange={(e) => setStatus(e.target.value as "Chờ xử lý" | "")}
        >
          <option value="Chờ xử lý">Chờ xử lý</option>
          <option value="">Tất cả</option>
        </select>
      </label>
    </div>
  );

  if (resource.status === "loading")
    return (
      <div className="space-y-4">
        {toolbar}
        <LoadingState rows={4} />
      </div>
    );
  if (resource.status === "error")
    return (
      <div className="space-y-4">
        {toolbar}
        <ErrorState message={resource.message} onRetry={resource.reload} />
      </div>
    );

  const { pending, exceptions } = resource.data;

  return (
    <div className="space-y-6">
      {toolbar}
      {actionError && (
        <p role="alert" className="text-sm text-danger-fg">
          {actionError}
        </p>
      )}

      <section className="space-y-3">
        <h2 className="text-[15px] font-bold">Thanh toán chờ xác minh</h2>
        {pending.length === 0 ? (
          <EmptyState
            icon={Clock}
            title="Không có khoản nào đang chờ"
            description="Giao dịch QR chờ xác nhận hoặc chờ đối soát sẽ hiện ở đây."
          />
        ) : (
          <>
            <Bars
              items={pending.map((row) => ({
                key: row.MaOrder,
                label: orderLabel(row.MaOrderHienThi, row.MaOrder),
                value: Number(row.SoTien) || 0,
              }))}
              ariaLabel="Biểu đồ số tiền đang chờ xác minh theo order"
              tickFormat={(t) => `${formatNumber(t / 1_000_000)}tr`}
              tooltipFormat={(item) =>
                `${item.label}: ${formatVnd(item.value)}`
              }
            />
            <ReportTable
              headers={[
                "Order",
                "Số tiền",
                "Trạng thái",
                "Đã chờ",
                "Kết quả gần nhất",
                "Lịch sử xác minh",
              ]}
              rows={pending.map((row) => [
                orderLabel(row.MaOrderHienThi, row.MaOrder),
                formatVnd(row.SoTien),
                row.TrangThai,
                `${formatNumber(row.ThoiGianChoPhut)} phút`,
                row.KetQuaGanNhat ?? "—",
                (row.LichSu?.length ?? 0) === 0
                  ? "—"
                  : row.LichSu?.map(
                      (entry) =>
                        `${formatDateTime(entry.ThoiDiem)}${
                          entry.GhiChu ? ` · ${entry.GhiChu}` : ""
                        }${entry.KetQua ? ` · ${entry.KetQua}` : ""}`,
                    ).join(" / "),
              ])}
              pageSize={10}
            />
          </>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-[15px] font-bold">Khoản chuyển khoản ngoại lệ</h2>
        <p className="text-sm text-muted">
          Tiền về nhưng không khớp order. Quản lý áp dụng vào order hoặc ghi
          nhận đã hoàn tiền ngoài hệ thống; khoản chưa xử lý không cộng doanh
          thu.
        </p>
        {exceptions.length === 0 ? (
          <EmptyState
            icon={TriangleAlert}
            title="Không có khoản ngoại lệ"
            description="Webhook không khớp order sẽ được lưu ở đây để đối chiếu."
          />
        ) : (
          <>
            <Bars
              items={exceptions.map((row) => ({
                key: row.MaNgoaiLe,
                label: row.MaGiaoDichCong,
                value: Number(row.SoTien) || 0,
              }))}
              ariaLabel="Biểu đồ số tiền các khoản ngoại lệ"
              tickFormat={(t) => `${formatNumber(t / 1_000_000)}tr`}
              tooltipFormat={(item) =>
                `${item.label}: ${formatVnd(item.value)}`
              }
            />
            <ReportTable
              headers={[
                "Mã chuyển khoản",
                "Order",
                "Số tiền",
                "Lý do",
                "Trạng thái",
                "Thời điểm",
                "Xử lý",
              ]}
              rows={exceptions.map((row) => [
                row.MaGiaoDichCong,
                orderLabel(row.MaOrderHienThi, row.MaOrder),
                formatVnd(row.SoTien),
                row.LyDo ?? "—",
                row.TrangThai,
                formatDateTime(row.ThoiDiemXuLy ?? row.ThoiDiemTao),
                row.TrangThai === "Chờ xử lý" ? (
                  <span key={row.MaNgoaiLe} className="flex flex-wrap gap-1.5">
                    <Button
                      size="sm"
                      disabled={busy}
                      onClick={() => resolve(row, "applied")}
                    >
                      Áp dụng
                    </Button>
                    <Button
                      size="sm"
                      variant="secondary"
                      disabled={busy}
                      onClick={() => resolve(row, "refunded")}
                    >
                      Đã hoàn tiền
                    </Button>
                  </span>
                ) : (
                  <span key={row.MaNgoaiLe}>
                    {row.GhiChu ?? "—"}
                    {row.MaThamChieuHoan
                      ? ` · ${row.MaThamChieuHoan}${
                          row.SoTienHoan
                            ? ` (${formatVnd(row.SoTienHoan)})`
                            : ""
                        }`
                      : ""}
                  </span>
                ),
              ])}
              pageSize={10}
            />
          </>
        )}
      </section>
    </div>
  );
}
