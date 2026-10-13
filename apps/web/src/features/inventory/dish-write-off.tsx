"use client";

import { ChefHat } from "lucide-react";
import { useCallback, useId, useState } from "react";

import { ConfirmDialog } from "@/components/confirm-dialog";
import { DataPagination } from "@/components/data-pagination";
import { FormField } from "@/components/form-field";
import {
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
} from "@/components/page-states";
import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
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
import { useAction } from "@/lib/use-action";
import { useResource } from "@/lib/use-resource";

import type { DishIssueResult, DishLine } from "./types";

const PAGE_SIZE = 20;
const REASON_MAX = 50;
const NOTE_MAX = 500;

type LinesResponse = { items: DishLine[]; total: number };

/** Servings typed per order line, kept across pages; blank or 0 means "not written off". */
type Draft = Record<number, string>;

function servingsOf(raw: string | undefined): number {
  const value = Number(raw);
  return Number.isInteger(value) && value > 0 ? value : 0;
}

export function DishWriteOff() {
  const formId = useId();
  const [businessDate, setBusinessDate] = useState("");
  const [page, setPage] = useState(1);
  const [draft, setDraft] = useState<Draft>({});
  const [reason, setReason] = useState("");
  const [note, setNote] = useState("");
  const [validation, setValidation] = useState<string | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const { run, pending, error: serverError, clearError } = useAction();

  const fetchLines = useCallback(() => {
    const params = new URLSearchParams();
    if (businessDate) params.set("business_date", businessDate);
    params.set("page", String(page));
    params.set("page_size", String(PAGE_SIZE));
    return apiFetch<LinesResponse>(
      `/inventory/issues/dish-lines?${params.toString()}`,
    );
  }, [businessDate, page]);
  const lines = useResource(fetchLines);

  const items = lines.status === "ready" ? lines.data.items : [];
  const total = lines.status === "ready" ? lines.data.total : 0;
  const selected = Object.entries(draft)
    .map(([id, raw]) => ({
      order_line_id: Number(id),
      servings: servingsOf(raw),
    }))
    .filter((l) => l.servings > 0);

  function changeDate(value: string) {
    setBusinessDate(value);
    setPage(1);
    setDraft({});
    setValidation(null);
    clearError();
  }

  function setServings(line: DishLine, raw: string) {
    const typed = Math.floor(Number(raw));
    // Cap at what is still writable so the server never sees an over-limit line.
    const capped =
      raw === "" || !Number.isFinite(typed)
        ? ""
        : String(Math.min(Math.max(typed, 0), line.SoSuatConLai));
    setDraft((prev) => ({ ...prev, [line.MaChiTietOrder]: capped }));
  }

  function requestSubmit() {
    clearError();
    if (selected.length === 0) {
      setValidation("Nhập số suất hủy cho ít nhất một dòng món.");
      return;
    }
    if (reason.trim() === "") {
      setValidation("Nhập lý do hủy.");
      return;
    }
    setValidation(null);
    setConfirmOpen(true);
  }

  async function submit() {
    const result = await run(
      () =>
        apiFetch<DishIssueResult>("/inventory/issues/dishes", {
          method: "POST",
          body: {
            reason: reason.trim(),
            ...(note.trim() ? { note: note.trim() } : {}),
            lines: selected,
          },
        }),
      (r) => `Đã tạo phiếu hủy #${r.MaPhieuXuat}.`,
    );
    setConfirmOpen(false);
    if (result !== undefined) {
      setDraft({});
      setReason("");
      setNote("");
      lines.reload();
    }
  }

  const message = validation ?? serverError;

  return (
    <div className="space-y-5">
      <PageHeader
        title="Hủy món đã chế biến"
        description="Ghi nhận món đã nấu nhưng không phục vụ được. Nguyên liệu đã trừ khi bếp làm món nên phiếu này không trừ kho thêm."
      />

      <div className="max-w-xs">
        <FormField
          id={`${formId}-date`}
          label="Ngày kinh doanh"
          help="Để trống để dùng ngày kinh doanh hiện tại."
        >
          <Input
            id={`${formId}-date`}
            type="date"
            value={businessDate}
            onChange={(e) => changeDate(e.target.value)}
          />
        </FormField>
      </div>

      {lines.status === "loading" ? (
        <LoadingState />
      ) : lines.status === "error" ? (
        <ErrorState message={lines.message} onRetry={lines.reload} />
      ) : items.length === 0 && total === 0 ? (
        <EmptyState
          icon={ChefHat}
          title="Không có món nào để hủy"
          description="Chưa có dòng món đã chế biến còn suất có thể hủy trong ngày này."
        />
      ) : (
        <>
          <Table>
            <caption className="sr-only">Dòng món có thể hủy</caption>
            <TableHeader>
              <TableRow>
                <TableHead>Món</TableHead>
                <TableHead>Order</TableHead>
                <TableHead className="text-right">Số suất</TableHead>
                <TableHead className="text-right">Còn hủy được</TableHead>
                <TableHead className="w-32">Số suất hủy</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((line) => (
                <TableRow key={line.MaChiTietOrder}>
                  <TableCell className="font-medium">{line.TenMon}</TableCell>
                  <TableCell className="tabular-nums">
                    {line.MaOrderHienThi ?? `#${line.MaOrder}`}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatNumber(line.SoLuong)}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatNumber(line.SoSuatConLai)}
                  </TableCell>
                  <TableCell>
                    <Input
                      type="number"
                      inputMode="numeric"
                      min={0}
                      max={line.SoSuatConLai}
                      step={1}
                      aria-label={`Số suất hủy ${line.TenMon} ${line.MaOrderHienThi ?? `#${line.MaOrder}`}`}
                      value={draft[line.MaChiTietOrder] ?? ""}
                      onChange={(e) => setServings(line, e.target.value)}
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          <DataPagination
            page={page}
            pageSize={PAGE_SIZE}
            total={total}
            onPageChange={setPage}
          />

          <div className="grid gap-4 sm:grid-cols-2">
            <FormField
              id={`${formId}-reason`}
              label="Lý do"
              help={`Tối đa ${REASON_MAX} ký tự.`}
            >
              <Input
                id={`${formId}-reason`}
                maxLength={REASON_MAX}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
              />
            </FormField>
            <FormField id={`${formId}-note`} label="Ghi chú (không bắt buộc)">
              <Textarea
                id={`${formId}-note`}
                maxLength={NOTE_MAX}
                rows={2}
                value={note}
                onChange={(e) => setNote(e.target.value)}
              />
            </FormField>
          </div>

          {message ? (
            <p role="alert" className="text-danger-fg">
              {message}
            </p>
          ) : null}

          <div className="flex justify-end border-t border-border pt-4">
            <Button onClick={requestSubmit} disabled={pending}>
              Hủy món đã chọn
            </Button>
          </div>

          <ConfirmDialog
            open={confirmOpen}
            onOpenChange={setConfirmOpen}
            title="Xác nhận hủy món"
            description={`Hủy ${formatNumber(selected.reduce((sum, l) => sum + l.servings, 0))} suất trên ${selected.length} dòng món. Phiếu không trừ kho thêm và không thể sửa sau khi tạo.`}
            confirmLabel="Xác nhận hủy"
            danger
            pending={pending}
            onConfirm={submit}
          />
        </>
      )}
    </div>
  );
}
