"use client";

import { useEffect, useState } from "react";

import { FormField } from "@/components/form-field";
import { ErrorState, LoadingState } from "@/components/page-states";
import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import { apiFetch } from "@/lib/api-client";
import { useAction } from "@/lib/use-action";
import { useResource } from "@/lib/use-resource";

type Config = {
  MaCauHinh: number;
  TenNhaHang: string;
  DiaChi: string | null;
  MauHoaDon: string | null;
  NguongTonMacDinh: number;
  GioBatDauBusinessDate: string;
  GioBatDauBusinessDateMoi: string | null;
  NgayHieuLucGioMoi: string | null;
  SoNgayCanhBaoHetHan: number;
  SoCauHoiAIMoiNgay: number;
  ThoiGianGiuChoPhut: number;
};

const loadConfig = () => apiFetch<Config>("/settings/config");

function positiveIntegerError(value: string): string | null {
  const parsed = Number(value);
  return /^\d+$/.test(value.trim()) &&
    Number.isSafeInteger(parsed) &&
    parsed > 0
    ? null
    : "Nhập một số nguyên dương.";
}

/** FR-SET-04/05: restaurant details and runtime settings. */
export function ConfigPanel() {
  const config = useResource(loadConfig);
  if (config.status === "loading") return <LoadingState />;
  if (config.status === "error")
    return <ErrorState message={config.message} onRetry={config.reload} />;
  return <ConfigForm config={config.data} onSaved={config.reload} />;
}

function ConfigForm({
  config,
  onSaved,
}: {
  config: Config;
  onSaved: () => void;
}) {
  const { run, pending } = useAction();
  const [name, setName] = useState(config.TenNhaHang);
  const [address, setAddress] = useState(config.DiaChi ?? "");
  const [invoiceTemplate, setInvoiceTemplate] = useState(
    config.MauHoaDon ?? "",
  );
  const [threshold, setThreshold] = useState(String(config.NguongTonMacDinh));
  const [newBusinessDayStart, setNewBusinessDayStart] = useState("");
  const [expiryWarningDays, setExpiryWarningDays] = useState(
    String(config.SoNgayCanhBaoHetHan),
  );
  const [aiDailyQuota, setAiDailyQuota] = useState(
    String(config.SoCauHoiAIMoiNgay),
  );
  const [holdMinutes, setHoldMinutes] = useState(
    String(config.ThoiGianGiuChoPhut),
  );
  const [nowMs, setNowMs] = useState(() => Date.now());
  const activationMs =
    config.GioBatDauBusinessDateMoi && config.NgayHieuLucGioMoi
      ? Date.parse(
          `${config.NgayHieuLucGioMoi}T${config.GioBatDauBusinessDateMoi}+07:00`,
        )
      : null;
  const waitingForActivation =
    activationMs !== null &&
    Number.isFinite(activationMs) &&
    nowMs < activationMs;
  const hasActivated =
    activationMs !== null &&
    Number.isFinite(activationMs) &&
    nowMs >= activationMs;
  const currentHour = hasActivated
    ? (config.GioBatDauBusinessDateMoi ?? config.GioBatDauBusinessDate)
    : config.GioBatDauBusinessDate;

  useEffect(() => {
    if (activationMs === null || !Number.isFinite(activationMs)) return;
    const currentTime = Date.now();
    const remaining = activationMs - currentTime;
    if (remaining <= 0) {
      if (nowMs < activationMs) {
        const timer = setTimeout(() => setNowMs(Date.now()), 0);
        return () => clearTimeout(timer);
      }
      return;
    }
    const timer = setTimeout(
      () => setNowMs(Date.now()),
      Math.min(remaining, 2_147_483_647),
    );
    return () => clearTimeout(timer);
  }, [activationMs, nowMs]);

  const thresholdError =
    threshold.trim() !== "" && !/^\d+$/.test(threshold.trim())
      ? "Nhập một số nguyên không âm."
      : null;
  const nameError = name.trim() === "" ? "Nhập tên nhà hàng." : null;
  const newBusinessDayStartError =
    newBusinessDayStart !== "" &&
    !/^([01]\d|2[0-3]):[0-5]\d$/.test(newBusinessDayStart)
      ? "Nhập giờ hợp lệ theo định dạng HH:mm."
      : null;
  const expiryWarningDaysError = positiveIntegerError(expiryWarningDays);
  const aiDailyQuotaError = positiveIntegerError(aiDailyQuota);
  const holdMinutesError = positiveIntegerError(holdMinutes);
  const canSave =
    thresholdError === null &&
    nameError === null &&
    newBusinessDayStartError === null &&
    expiryWarningDaysError === null &&
    aiDailyQuotaError === null &&
    holdMinutesError === null;

  async function save() {
    if (!canSave) return;
    const result = await run(
      () =>
        apiFetch("/settings/config", {
          method: "PUT",
          body: {
            TenNhaHang: name.trim(),
            DiaChi: address.trim() || null,
            MauHoaDon: invoiceTemplate.trim() || null,
            NguongTonMacDinh: Number(threshold),
            ...(newBusinessDayStart
              ? { GioBatDauBusinessDateMoi: newBusinessDayStart }
              : {}),
            SoNgayCanhBaoHetHan: Number(expiryWarningDays),
            SoCauHoiAIMoiNgay: Number(aiDailyQuota),
            ThoiGianGiuChoPhut: Number(holdMinutes),
          },
        }),
      "Đã lưu cấu hình.",
    );
    if (result !== undefined) {
      setNewBusinessDayStart("");
      onSaved();
    }
  }

  return (
    <div className="max-w-xl space-y-4">
      <FormField id="cfg-name" label="Tên nhà hàng" error={nameError}>
        <Input
          id="cfg-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </FormField>
      <FormField id="cfg-address" label="Địa chỉ">
        <Input
          id="cfg-address"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
        />
      </FormField>
      <FormField id="cfg-invoice" label="Mẫu hóa đơn">
        <Textarea
          id="cfg-invoice"
          rows={4}
          value={invoiceTemplate}
          onChange={(e) => setInvoiceTemplate(e.target.value)}
        />
      </FormField>
      <FormField
        id="cfg-threshold"
        label="Ngưỡng tồn tối thiểu mặc định"
        error={thresholdError}
      >
        <Input
          id="cfg-threshold"
          inputMode="numeric"
          value={threshold}
          onChange={(e) => setThreshold(e.target.value)}
        />
      </FormField>
      <FormField
        id="cfg-business-date"
        label="Giờ bắt đầu Business Date"
        help="Giờ đang áp dụng; nhập giờ mới ở bên dưới để lên lịch thay đổi."
      >
        <Input id="cfg-business-date" value={currentHour} disabled readOnly />
      </FormField>
      <p className="text-sm text-subtle">
        {waitingForActivation &&
        config.GioBatDauBusinessDateMoi &&
        config.NgayHieuLucGioMoi
          ? `Giờ đang chờ áp dụng: ${config.GioBatDauBusinessDateMoi.slice(0, 5)} từ Business Date ${config.NgayHieuLucGioMoi.split("-").reverse().join("/")}.`
          : "Chưa có giờ mới đang chờ áp dụng."}
      </p>
      <FormField
        id="cfg-new-business-date"
        label="Giờ bắt đầu Business Date mới"
        error={newBusinessDayStartError}
        help="Để trống nếu không đổi giờ. Ngày hiệu lực sẽ được xác định khi lưu."
      >
        <Input
          id="cfg-new-business-date"
          type="time"
          value={newBusinessDayStart}
          onChange={(e) => setNewBusinessDayStart(e.target.value)}
          aria-invalid={newBusinessDayStartError !== null}
          aria-describedby="cfg-new-business-date-message"
        />
      </FormField>
      <FormField
        id="cfg-expiry-warning"
        label="Số ngày cảnh báo sắp hết hạn"
        error={expiryWarningDaysError}
      >
        <Input
          id="cfg-expiry-warning"
          inputMode="numeric"
          value={expiryWarningDays}
          onChange={(e) => setExpiryWarningDays(e.target.value)}
          aria-invalid={expiryWarningDaysError !== null}
          aria-describedby={
            expiryWarningDaysError ? "cfg-expiry-warning-message" : undefined
          }
        />
      </FormField>
      <FormField
        id="cfg-ai-quota"
        label="Hạn mức câu hỏi AI mỗi người mỗi ngày"
        error={aiDailyQuotaError}
      >
        <Input
          id="cfg-ai-quota"
          inputMode="numeric"
          value={aiDailyQuota}
          onChange={(e) => setAiDailyQuota(e.target.value)}
          aria-invalid={aiDailyQuotaError !== null}
          aria-describedby={
            aiDailyQuotaError ? "cfg-ai-quota-message" : undefined
          }
        />
      </FormField>
      <FormField
        id="cfg-hold-minutes"
        label="Thời gian giữ chỗ (phút)"
        error={holdMinutesError}
        help="Lượt giữ chỗ hiện có giữ nguyên thời điểm hết hạn đã ghi nhận khi thay đổi thời gian giữ chỗ."
      >
        <Input
          id="cfg-hold-minutes"
          inputMode="numeric"
          value={holdMinutes}
          onChange={(e) => setHoldMinutes(e.target.value)}
          aria-invalid={holdMinutesError !== null}
          aria-describedby="cfg-hold-minutes-message"
        />
      </FormField>
      <Button disabled={pending || !canSave} onClick={save}>
        Lưu cấu hình
      </Button>
    </div>
  );
}
