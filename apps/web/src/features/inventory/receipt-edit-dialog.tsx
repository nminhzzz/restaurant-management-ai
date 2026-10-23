"use client";

import { useCallback, useState } from "react";

import { ErrorState, LoadingState } from "@/components/page-states";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { apiFetch } from "@/lib/api-client";
import { formatVnd } from "@/lib/format";
import { useAction } from "@/lib/use-action";
import { useResource } from "@/lib/use-resource";

type ReceiptLine = {
  MaChiTietNhap: number;
  MaNguyenLieu: number;
  TenNguyenLieu: string;
  DonViTinh: string;
  SoLuong: number;
  DonGia: number;
};

export type ReceiptDetail = {
  MaPhieuNhap: number;
  MaNhaCungCap: number | null;
  NgayNhap: string | null;
  TrangThai: string;
  TongTien: number;
  lines: ReceiptLine[];
};

export function ReceiptEditDialog({
  receiptId,
  onClose,
  onSaved,
}: {
  receiptId: number;
  onClose: () => void;
  onSaved: () => void;
}) {
  const load = useCallback(
    () => apiFetch<ReceiptDetail>(`/inventory/receipts/${receiptId}`),
    [receiptId],
  );
  const fetcher = useResource(load);
  const action = useAction();
  const [draft, setDraft] = useState<
    Record<number, { qty: string; price: string }>
  >({});

  if (fetcher.status === "loading") return <LoadingState rows={3} />;
  if (fetcher.status === "error")
    return <ErrorState message={fetcher.message} onRetry={fetcher.reload} />;

  const detail = fetcher.data;
  const valueOf = (line: ReceiptLine) =>
    draft[line.MaChiTietNhap] ?? {
      qty: String(line.SoLuong),
      price: String(line.DonGia),
    };

  function update(line: ReceiptLine, patch: { qty?: string; price?: string }) {
    setDraft((previous) => ({
      ...previous,
      [line.MaChiTietNhap]: { ...valueOf(line), ...patch },
    }));
  }

  async function save() {
    const lines = detail.lines.map((line) => {
      const value = valueOf(line);
      return {
        line_id: line.MaChiTietNhap,
        quantity: Number(value.qty),
        unit_price: Number(value.price),
      };
    });
    if (lines.some((line) => !(line.quantity > 0) || line.unit_price < 0)) {
      return;
    }
    const result = await action.run(
      () =>
        apiFetch(`/inventory/receipts/${receiptId}`, {
          method: "PATCH",
          body: { lines },
        }),
      "Đã cập nhật phiếu nhập.",
    );
    if (result !== undefined) {
      onSaved();
      onClose();
    }
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="w-[min(40rem,calc(100vw-2rem))]">
        <DialogHeader>
          <DialogTitle>Sửa phiếu nhập #{detail.MaPhieuNhap}</DialogTitle>
        </DialogHeader>
        <p className="text-sm text-muted">
          Chỉ sửa được khi lô của phiếu chưa phát sinh xuất kho hoặc lượt giữ.
        </p>
        <div className="space-y-3">
          {detail.lines.map((line) => {
            const value = valueOf(line);
            return (
              <div
                key={line.MaChiTietNhap}
                className="grid gap-2 rounded-container border border-border p-3 sm:grid-cols-[1fr_8rem_10rem]"
              >
                <div>
                  <p className="font-medium">{line.TenNguyenLieu}</p>
                  <p className="text-xs text-muted">{line.DonViTinh}</p>
                </div>
                <label className="grid gap-1 text-xs text-subtle">
                  <span>Số lượng</span>
                  <Input
                    aria-label={`Số lượng ${line.TenNguyenLieu}`}
                    type="number"
                    min={0}
                    step="0.0001"
                    value={value.qty}
                    onChange={(e) => update(line, { qty: e.target.value })}
                  />
                </label>
                <label className="grid gap-1 text-xs text-subtle">
                  <span>Đơn giá</span>
                  <Input
                    aria-label={`Đơn giá ${line.TenNguyenLieu}`}
                    type="number"
                    min={0}
                    value={value.price}
                    onChange={(e) => update(line, { price: e.target.value })}
                  />
                </label>
              </div>
            );
          })}
        </div>
        {action.error && (
          <p role="alert" className="text-sm text-danger-fg">
            {action.error}
          </p>
        )}
        <p className="text-right text-sm text-muted">
          Tổng hiện tại: {formatVnd(detail.TongTien)}
        </p>
        <DialogFooter>
          <Button variant="secondary" onClick={onClose}>
            Đóng
          </Button>
          <Button onClick={save} disabled={action.pending}>
            Lưu thay đổi
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
