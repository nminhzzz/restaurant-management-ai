"use client";

import {
  ArrowRightLeft,
  CircleAlert,
  Lock,
  Plus,
  PrinterIcon,
  TriangleAlert,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { ConfirmDialog } from "@/components/confirm-dialog";
import { FormField } from "@/components/form-field";
import {
  ErrorState,
  LoadingState,
  StatusBadge,
} from "@/components/page-states";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DishPickerDialog,
  type PickableDish,
} from "@/features/sales/dish-picker";
import { apiFetch } from "@/lib/api-client";
import { formatVnd } from "@/lib/format";
import { useAction } from "@/lib/use-action";
import { useResource } from "@/lib/use-resource";

type OrderLine = {
  MaChiTietOrder: number;
  MaMon: number;
  SoLuong: number;
  DonGia: number;
  GhiChu: string | null;
  TrangThai: string;
};

type Order = {
  MaOrder: number;
  MaOrderHienThi: string;
  MaBan: number | null;
  TrangThai: string;
  lines?: OrderLine[];
};

type Ticket = {
  MaPhieuBep: number;
  NoiDung: string | null;
  TrangThai: string;
  TrangThaiIn: string;
  SoLanIn: number;
  LoiIn?: string | null;
};

type DiningTable = { MaBan: number; TenBan: string; TrangThai?: string };

type Hold = {
  MaGiuCho: number;
  MaMon: number;
  TenMon?: string | null;
  SoLuong: number;
  GhiChu?: string | null;
  ThoiDiemHetHan: string;
};

const NEXT_STATUS: Record<string, string> = {
  Chờ: "Đã xác nhận xong",
  "Đã xác nhận xong": "Đã phục vụ",
};

async function loadDetail(orderId: number) {
  const [order, dishPage, tickets, tables] = await Promise.all([
    apiFetch<Order>(`/sales/orders/${orderId}`),
    apiFetch<{ items?: PickableDish[] }>("/catalog/dishes?size=200").catch(
      () => ({ items: [] }),
    ),
    apiFetch<{ items: Ticket[] }>(`/sales/orders/${orderId}/tickets`).catch(
      () => ({ items: [] }),
    ),
    apiFetch<DiningTable[]>("/catalog/tables").catch(() => []),
  ]);
  const holds = await apiFetch<Hold[]>(
    `/sales/holds?order_id=${orderId}`,
  ).catch(() => []);
  return {
    order,
    dishes: dishPage.items ?? [],
    names: new Map((dishPage.items ?? []).map((d) => [d.MaMon, d.TenMon])),
    tickets: tickets.items,
    tables: Array.isArray(tables) ? tables : [],
    holds,
  };
}

export function OrderDetail({ orderId }: { orderId: number }) {
  const fetcher = useCallback(() => loadDetail(orderId), [orderId]);
  const detail = useResource(fetcher);
  const action = useAction();

  const [pickerOpen, setPickerOpen] = useState(false);
  const [pickedDish, setPickedDish] = useState<PickableDish | null>(null);
  const [addQty, setAddQty] = useState("1");
  const [addNote, setAddNote] = useState("");
  const [moveOpen, setMoveOpen] = useState(false);
  const [moveTarget, setMoveTarget] = useState("");
  const [cancelLine, setCancelLine] = useState<OrderLine | null>(null);
  const [editingLine, setEditingLine] = useState<number | null>(null);
  const [qtyDraft, setQtyDraft] = useState("");
  const [quantityRequestId, setQuantityRequestId] = useState("");

  const awaitingPrinter =
    detail.status === "ready" &&
    detail.data.tickets.some((ticket) =>
      ["Chờ in", "Đang in"].includes(ticket.TrangThaiIn),
    );
  useEffect(() => {
    if (!awaitingPrinter) return;
    const timer = window.setInterval(detail.reload, 5000);
    return () => window.clearInterval(timer);
  }, [awaitingPrinter, detail.reload]);

  if (detail.status === "loading") return <LoadingState rows={5} />;
  if (detail.status === "error")
    return <ErrorState message={detail.message} onRetry={detail.reload} />;

  const { order, names, dishes, tickets, tables, holds } = detail.data;
  const lines = order.lines ?? [];
  const locked = order.TrangThai !== "Đang mở";
  const freeTables = tables.filter(
    (t) => t.MaBan !== order.MaBan && (t.TrangThai ?? "Trống") === "Trống",
  );

  async function addDish(dish: PickableDish, quantity: number, note: string) {
    await action.run(async () => {
      await apiFetch(`/sales/orders/${orderId}/lines`, {
        method: "POST",
        body: {
          dish_id: dish.MaMon,
          quantity,
          note: note.trim() || null,
        },
      });
      setPickedDish(null);
      detail.reload();
    }, `Đã thêm ${dish.TenMon}.`);
  }

  async function saveQuantity(line: OrderLine) {
    const quantity = Math.max(1, Number(qtyDraft) || 1);
    await action.run(
      async () => {
        await apiFetch(
          `/sales/orders/${orderId}/lines/${line.MaChiTietOrder}`,
          {
            method: "PATCH",
            body: {
              quantity,
              ...(quantity > line.SoLuong
                ? { request_line_id: quantityRequestId }
                : {}),
            },
          },
        );
        setEditingLine(null);
        detail.reload();
      },
      quantity > line.SoLuong
        ? "Đã gọi thêm thành dòng món mới theo giá và công thức hiện tại."
        : "Đã cập nhật số lượng.",
    );
  }

  async function advanceStatus(line: OrderLine) {
    const to = NEXT_STATUS[line.TrangThai];
    if (!to) return;
    await action.run(async () => {
      await apiFetch(
        `/sales/orders/${orderId}/lines/${line.MaChiTietOrder}/status`,
        {
          method: "PATCH",
          body: { to },
        },
      );
      detail.reload();
    }, `Đã chuyển sang ${to}.`);
  }

  async function confirmCancelLine(reason: string) {
    if (!cancelLine) return;
    await action.run(async () => {
      await apiFetch(
        `/sales/orders/${orderId}/lines/${cancelLine.MaChiTietOrder}/cancel`,
        {
          method: "POST",
          body: { reason },
        },
      );
      setCancelLine(null);
      detail.reload();
    }, "Đã hủy món.");
  }

  async function moveTable() {
    if (!moveTarget) return;
    await action.run(async () => {
      await apiFetch(`/sales/orders/${orderId}/move`, {
        method: "POST",
        body: { to_table_id: Number(moveTarget) },
      });
      setMoveOpen(false);
      setMoveTarget("");
      detail.reload();
    }, "Đã chuyển bàn.");
  }

  async function reprintTicket(ticket: Ticket) {
    await action.run(async () => {
      await apiFetch(
        `/sales/orders/${orderId}/tickets/${ticket.MaPhieuBep}/reprint`,
        { method: "POST", body: {} },
      );
      detail.reload();
    }, "Đã gửi in lại phiếu bếp.");
  }

  async function reportPrintFailed(ticket: Ticket) {
    await action.run(async () => {
      await apiFetch(
        `/sales/orders/${orderId}/tickets/${ticket.MaPhieuBep}/print-result`,
        { method: "POST", body: { ok: false } },
      );
      detail.reload();
    }, "Đã báo in lỗi.");
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-container border border-border bg-surface p-4">
        <div className="flex items-center gap-3">
          <div>
            <p className="text-xs text-subtle">Order</p>
            <p className="font-mono text-base font-medium">
              {order.MaOrderHienThi}
            </p>
          </div>
          <StatusBadge status={order.TrangThai} />
          {locked && (
            <span className="flex items-center gap-1 text-xs text-subtle">
              <Lock className="size-3.5" aria-hidden />
              Order đã khóa, không thể sửa
            </span>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setMoveOpen(true)}
            disabled={locked || freeTables.length === 0}
          >
            <ArrowRightLeft />
            Chuyển bàn
          </Button>
          <Button
            size="sm"
            onClick={() => setPickerOpen(true)}
            disabled={locked}
          >
            <Plus />
            Thêm món
          </Button>
        </div>
      </div>

      {action.error && (
        <p role="alert" className="flex items-center gap-1.5 text-danger-fg">
          <CircleAlert className="size-4 shrink-0" aria-hidden />
          {action.error}
        </p>
      )}

      {holds.length > 0 && (
        <section className="rounded-container border border-border bg-surface p-4">
          <h2 className="text-sm font-bold">Lượt giữ chưa gửi</h2>
          <p className="text-xs text-muted">
            Các lượt giữ này chưa thành dòng món. Giải phóng trước khi chốt
            thanh toán nếu khách không lấy.
          </p>
          <ul className="mt-2 divide-y divide-border">
            {holds.map((hold) => (
              <li
                key={hold.MaGiuCho}
                className="flex flex-wrap items-center justify-between gap-2 py-2"
              >
                <span>
                  {hold.TenMon ?? names.get(hold.MaMon) ?? `Món #${hold.MaMon}`}{" "}
                  × {hold.SoLuong}
                  {hold.GhiChu ? ` · ${hold.GhiChu}` : ""}
                </span>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() =>
                    action.run(async () => {
                      await apiFetch(`/sales/holds/${hold.MaGiuCho}`, {
                        method: "DELETE",
                      });
                      detail.reload();
                    }, "Đã giải phóng lượt giữ.")
                  }
                >
                  Giải phóng
                </Button>
              </li>
            ))}
          </ul>
        </section>
      )}

      <ul className="divide-y divide-border rounded-container border border-border bg-surface">
        {lines.map((line) => {
          const canEdit = !locked && line.TrangThai === "Chờ";
          const nextStatus = NEXT_STATUS[line.TrangThai];
          return (
            <li
              key={line.MaChiTietOrder}
              className="flex flex-wrap items-center gap-3 px-4 py-3"
            >
              <div className="min-w-0 flex-1">
                <p className="font-medium">
                  {names.get(line.MaMon) ?? `Món #${line.MaMon}`}
                </p>
                {line.GhiChu && (
                  <p className="text-xs text-muted">{line.GhiChu}</p>
                )}
              </div>

              {editingLine === line.MaChiTietOrder ? (
                <div className="flex items-center gap-1.5">
                  <Input
                    aria-label={`Số lượng ${names.get(line.MaMon) ?? line.MaMon}`}
                    type="number"
                    min={1}
                    className="h-9 w-16"
                    value={qtyDraft}
                    onChange={(e) => setQtyDraft(e.target.value)}
                  />
                  <Button size="sm" onClick={() => saveQuantity(line)}>
                    Lưu
                  </Button>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => setEditingLine(null)}
                  >
                    Hủy
                  </Button>
                </div>
              ) : (
                <button
                  type="button"
                  className="tabular-nums underline-offset-2 disabled:no-underline"
                  disabled={!canEdit}
                  onClick={() => {
                    setEditingLine(line.MaChiTietOrder);
                    setQuantityRequestId(crypto.randomUUID());
                    setQtyDraft(String(line.SoLuong));
                  }}
                >
                  × {line.SoLuong}
                </button>
              )}

              <span className="w-24 text-right tabular-nums">
                {formatVnd(line.DonGia * line.SoLuong)}
              </span>

              <StatusBadge status={line.TrangThai} />

              <div className="flex gap-1.5">
                {nextStatus && (
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => advanceStatus(line)}
                  >
                    {nextStatus}
                  </Button>
                )}
                {canEdit && (
                  <Button
                    size="sm"
                    variant="outlineDanger"
                    onClick={() => setCancelLine(line)}
                  >
                    Hủy món
                  </Button>
                )}
              </div>
            </li>
          );
        })}
        {lines.length === 0 && (
          <li className="px-4 py-6 text-center text-muted">Chưa có món nào.</li>
        )}
      </ul>

      <div className="space-y-2">
        <h3 className="font-medium">Phiếu bếp</h3>
        <p className="text-xs text-subtle">
          Trạng thái gửi lệnh không xác nhận giấy đã in. Nếu chưa rõ kết quả,
          kiểm tra máy in trước khi in lại.
        </p>
        {tickets.length === 0 ? (
          <p className="text-muted">Chưa có phiếu bếp nào.</p>
        ) : (
          <ul className="divide-y divide-border rounded-container border border-border bg-surface">
            {tickets.map((ticket) => (
              <li
                key={ticket.MaPhieuBep}
                className="flex flex-wrap items-center justify-between gap-2 px-4 py-2.5"
              >
                <div className="flex items-center gap-2">
                  <span className="font-mono">#{ticket.MaPhieuBep}</span>
                  <StatusBadge status={ticket.TrangThaiIn} />
                  <span className="text-xs text-subtle">
                    Đã thử gửi {ticket.SoLanIn} lần
                  </span>
                </div>
                {ticket.LoiIn && (
                  <p role="alert" className="w-full text-sm text-danger">
                    {ticket.LoiIn}
                  </p>
                )}
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="secondary"
                    disabled={
                      action.pending ||
                      ["Chờ in", "Đang in"].includes(ticket.TrangThaiIn)
                    }
                    onClick={() => reprintTicket(ticket)}
                  >
                    <PrinterIcon />
                    In lại
                  </Button>
                  <Button
                    size="sm"
                    variant="outlineDanger"
                    disabled={
                      action.pending || ticket.TrangThaiIn === "Đang in"
                    }
                    onClick={() => reportPrintFailed(ticket)}
                  >
                    <TriangleAlert />
                    Báo in lỗi
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <DishPickerDialog
        open={pickerOpen}
        onOpenChange={setPickerOpen}
        dishes={dishes}
        onPick={(dish) => {
          setPickedDish(dish);
          setAddQty("1");
          setAddNote("");
          setPickerOpen(false);
        }}
      />

      <Dialog
        open={pickedDish !== null}
        onOpenChange={(open) => !open && setPickedDish(null)}
      >
        <DialogContent className="w-[min(24rem,calc(100vw-2rem))]">
          <DialogHeader>
            <DialogTitle>Thêm {pickedDish?.TenMon}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <FormField id="add-dish-qty" label="Số lượng">
              <Input
                id="add-dish-qty"
                type="number"
                min={1}
                value={addQty}
                onChange={(e) => setAddQty(e.target.value)}
              />
            </FormField>
            <FormField id="add-dish-note" label="Ghi chú cho món">
              <Input
                id="add-dish-note"
                value={addNote}
                onChange={(e) => setAddNote(e.target.value)}
                placeholder="Ví dụ: ít cay, không hành"
              />
            </FormField>
          </div>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setPickedDish(null)}>
              Đóng
            </Button>
            <Button
              onClick={() =>
                pickedDish &&
                addDish(pickedDish, Math.max(1, Number(addQty) || 1), addNote)
              }
              disabled={action.pending}
            >
              Thêm món
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={moveOpen} onOpenChange={setMoveOpen}>
        <DialogContent className="w-[min(24rem,calc(100vw-2rem))]">
          <DialogHeader>
            <DialogTitle>Chuyển bàn</DialogTitle>
          </DialogHeader>
          <Select value={moveTarget} onValueChange={setMoveTarget}>
            <SelectTrigger aria-label="Bàn đích">
              <SelectValue placeholder="Chọn bàn trống" />
            </SelectTrigger>
            <SelectContent>
              {freeTables.map((t) => (
                <SelectItem key={t.MaBan} value={String(t.MaBan)}>
                  {t.TenBan}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setMoveOpen(false)}>
              Quay lại
            </Button>
            <Button disabled={!moveTarget} onClick={moveTable}>
              Chuyển bàn
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={cancelLine !== null}
        onOpenChange={(open) => !open && setCancelLine(null)}
        title={`Hủy ${cancelLine ? (names.get(cancelLine.MaMon) ?? `món #${cancelLine.MaMon}`) : ""}?`}
        confirmLabel="Hủy món"
        danger
        requireReason
        pending={action.pending}
        onConfirm={confirmCancelLine}
      />
    </div>
  );
}
