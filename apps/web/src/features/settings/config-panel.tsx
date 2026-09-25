"use client";

import { useState } from "react";

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
};

const loadConfig = () => apiFetch<Config>("/settings/config");

/** FR-SET-04/05: restaurant info, invoice template and the default stock threshold. */
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

  const thresholdError =
    threshold.trim() !== "" && !/^\d+$/.test(threshold.trim())
      ? "Nhập một số nguyên không âm."
      : null;
  const nameError = name.trim() === "" ? "Nhập tên nhà hàng." : null;
  const canSave = thresholdError === null && nameError === null;

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
          },
        }),
      "Đã lưu cấu hình.",
    );
    if (result !== undefined) onSaved();
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
        help="Cố định 06:00, không thể chỉnh sửa ở đây."
      >
        <Input
          id="cfg-business-date"
          value={config.GioBatDauBusinessDate}
          disabled
          readOnly
        />
      </FormField>
      <Button disabled={pending || !canSave} onClick={save}>
        Lưu cấu hình
      </Button>
    </div>
  );
}
