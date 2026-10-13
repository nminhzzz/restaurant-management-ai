"use client";

import { Landmark } from "lucide-react";
import { useCallback, useState } from "react";

import { ConfirmDialog } from "@/components/confirm-dialog";
import { SelectFilter } from "@/components/filter-bar";
import {
  EmptyState,
  ErrorState,
  LoadingState,
  StatusBadge,
} from "@/components/page-states";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { apiFetch } from "@/lib/api-client";
import { formatDateTime, formatVnd } from "@/lib/format";
import { useAction } from "@/lib/use-action";
import { useResource } from "@/lib/use-resource";

import { FieldsDialog } from "./fields-dialog";
import type { PaymentException } from "./types";

const PENDING = "Chờ xử lý";

const STATUS_OPTIONS = [
  { value: PENDING, label: PENDING },
  { value: "Đã hoàn tiền", label: "Đã hoàn tiền" },
  { value: "Đã áp dụng cho order", label: "Đã áp dụng cho order" },
];

/**
 * FR-SALE-16/17, FR-REP-02: money that reached the bank but was not applied to its order.
 * Manager only; the API rejects every other role.
 */
export function PaymentExceptions() {
  const [status, setStatus] = useState(PENDING);
  const fetcher = useCallback(
    () =>
      apiFetch<{ items: PaymentException[] }>(
        `/sales/payment-exceptions${status ? `?status=${encodeURIComponent(status)}` : ""}`,
      ),
    [status],
  );
  const list = useResource(fetcher);
  const [applyTarget, setApplyTarget] = useState<PaymentException | null>(null);
  const [refundTarget, setRefundTarget] = useState<PaymentException | null>(
    null,
  );
  const apply = useAction();
  const refund = useAction();

  async function confirmApply() {
    if (!applyTarget) return;
    const result = await apply.run(
      () =>
        apiFetch(`/sales/payment-exceptions/${applyTarget.MaGiaoDich}/apply`, {
          method: "POST",
          body: {},
        }),
      "Đã áp dụng khoản tiền cho order.",
    );
    if (result !== undefined) {
      setApplyTarget(null);
      list.reload();
    }
  }

  async function submitRefund(values: Record<string, string>) {
    if (!refundTarget) return;
    const result = await refund.run(
      () =>
        apiFetch(
          `/sales/payment-exceptions/${refundTarget.MaGiaoDich}/refund`,
          {
            method: "POST",
            body: {
              MaThamChieuHoan: values.MaThamChieuHoan,
              ...(values.GhiChu ? { GhiChu: values.GhiChu } : {}),
            },
          },
        ),
      "Đã ghi nhận hoàn tiền.",
    );
    if (result !== undefined) {
      setRefundTarget(null);
      list.reload();
    }
  }

  return (
    <section
      aria-label="Ngoại lệ thanh toán"
      className="space-y-3 rounded-container border border-border bg-surface p-4"
    >
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-base font-bold">Ngoại lệ thanh toán</h2>
          <p className="text-muted">
            Tiền đã vào tài khoản nhưng chưa áp dụng cho order. Khoản này chưa
            tính vào doanh thu.
          </p>
        </div>
        <SelectFilter
          label="Trạng thái ngoại lệ"
          value={status}
          onChange={setStatus}
          options={STATUS_OPTIONS}
          allLabel="Tất cả"
        />
      </div>

      {list.status === "loading" ? (
        <LoadingState rows={3} />
      ) : list.status === "error" ? (
        <ErrorState message={list.message} onRetry={list.reload} />
      ) : list.data.items.length === 0 ? (
        <EmptyState
          icon={Landmark}
          title="Không có khoản ngoại lệ nào"
          description="Các khoản chuyển khoản lệch số tiền hoặc đến muộn sẽ hiện ở đây."
        />
      ) : (
        <Table>
          <caption className="sr-only">Danh sách ngoại lệ thanh toán</caption>
          <TableHeader>
            <TableRow>
              <TableHead>Order</TableHead>
              <TableHead className="text-right">Tiền nhận</TableHead>
              <TableHead className="text-right">Tổng order</TableHead>
              <TableHead>Mã giao dịch cổng</TableHead>
              <TableHead>Nhận lúc</TableHead>
              <TableHead>Trạng thái</TableHead>
              <TableHead className="text-right">Thao tác</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {list.data.items.map((item) => (
              <TableRow key={item.MaGiaoDich}>
                <TableCell>
                  <span className="block font-mono font-medium">
                    {item.MaOrderHienThi ?? `#${item.MaOrder}`}
                  </span>
                  <StatusBadge status={item.TrangThaiOrder} />
                </TableCell>
                <TableCell className="text-right font-semibold tabular-nums">
                  {formatVnd(item.SoTienNgoaiLe)}
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatVnd(item.TongTienOrder)}
                </TableCell>
                <TableCell className="font-mono text-xs">
                  {item.MaGiaoDichCong ?? ""}
                </TableCell>
                <TableCell className="text-muted tabular-nums">
                  {formatDateTime(item.ThoiDiemNhan)}
                </TableCell>
                <TableCell>
                  <StatusBadge status={item.TrangThaiNgoaiLe} />
                  {item.MaThamChieuHoan && (
                    <span className="block font-mono text-xs text-muted">
                      {item.MaThamChieuHoan}
                    </span>
                  )}
                </TableCell>
                <TableCell>
                  {item.TrangThaiNgoaiLe === PENDING && (
                    <div className="flex justify-end gap-1.5">
                      <Button
                        size="sm"
                        disabled={!item.CoTheApDung}
                        title={
                          item.CoTheApDung
                            ? undefined
                            : "Số tiền không khớp hoặc order không còn nhận được khoản này."
                        }
                        aria-label={`Áp dụng khoản ${item.MaGiaoDich} cho order`}
                        onClick={() => setApplyTarget(item)}
                      >
                        Áp dụng cho order
                      </Button>
                      <Button
                        size="sm"
                        variant="secondary"
                        aria-label={`Ghi nhận hoàn tiền khoản ${item.MaGiaoDich}`}
                        onClick={() => setRefundTarget(item)}
                      >
                        Ghi nhận hoàn tiền
                      </Button>
                    </div>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      <ConfirmDialog
        open={applyTarget !== null}
        onOpenChange={(open) => {
          if (!open) {
            setApplyTarget(null);
            apply.clearError();
          }
        }}
        title="Áp dụng khoản tiền cho order"
        description={
          apply.error ??
          (applyTarget
            ? `Order ${applyTarget.MaOrderHienThi ?? applyTarget.MaOrder} sẽ được ghi nhận đã thanh toán ${formatVnd(applyTarget.SoTienNgoaiLe)} và xuất hóa đơn.`
            : undefined)
        }
        confirmLabel="Áp dụng"
        pending={apply.pending}
        onConfirm={confirmApply}
      />

      <FieldsDialog
        open={refundTarget !== null}
        onOpenChange={(open) => {
          if (!open) {
            setRefundTarget(null);
            refund.clearError();
          }
        }}
        title="Ghi nhận hoàn tiền"
        description={
          refundTarget
            ? `Nhập mã tham chiếu của lần hoàn ${formatVnd(refundTarget.SoTienNgoaiLe)} đã thực hiện ngoài hệ thống.`
            : undefined
        }
        fields={[
          {
            name: "MaThamChieuHoan",
            label: "Mã tham chiếu hoàn tiền",
            required: true,
          },
          { name: "GhiChu", label: "Ghi chú", multiline: true },
        ]}
        confirmLabel="Ghi nhận hoàn tiền"
        pending={refund.pending}
        error={refund.error}
        onSubmit={submitRefund}
      />
    </section>
  );
}
