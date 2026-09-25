"use client";

import { Download } from "lucide-react";

import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api-client";
import { useAction } from "@/lib/use-action";

/** FR-SET-06: export a point-in-time backup dump as a downloadable JSON file. */
export function BackupPanel() {
  const { run, pending } = useAction();

  async function exportBackup() {
    const dump = await run(
      () =>
        apiFetch<Record<string, unknown>>("/settings/backup", {
          method: "POST",
          body: {},
        }),
      "Đã xuất bản sao dữ liệu.",
    );
    if (dump === undefined) return;

    const blob = new Blob([JSON.stringify(dump, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `backup-${new Date().toISOString().slice(0, 10)}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="max-w-xl space-y-3">
      <p className="text-muted">
        Xuất một bản sao dữ liệu hệ thống tại thời điểm hiện tại dưới dạng tệp
        JSON để lưu trữ ngoài hệ thống.
      </p>
      <Button onClick={exportBackup} disabled={pending}>
        <Download />
        Xuất bản sao
      </Button>
      <p className="text-xs text-subtle">
        Khôi phục từ bản sao là phần mở rộng, chưa nằm trong phạm vi MVP.
      </p>
    </div>
  );
}
