"use client";

import { useState } from "react";

import { FormField } from "@/components/form-field";
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
import { useAction } from "@/lib/use-action";

const EMPTY = { current: "", next: "", confirm: "" };

/** FR-SET-02: any signed-in user changes their own password. */
export function ChangePasswordDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [form, setForm] = useState(EMPTY);
  const { run, pending } = useAction();

  const mismatch = form.confirm.length > 0 && form.next !== form.confirm;
  const tooShort = form.next.length > 0 && form.next.length < 6;
  const canSubmit =
    form.current !== "" && form.next.length >= 6 && form.confirm === form.next;

  function close(next: boolean) {
    if (!next) setForm(EMPTY);
    onOpenChange(next);
  }

  async function submit() {
    if (!canSubmit) return;
    const result = await run(
      () =>
        apiFetch("/settings/auth/change-password", {
          method: "POST",
          body: { old_password: form.current, new_password: form.next },
        }),
      "Đã đổi mật khẩu.",
    );
    if (result !== undefined) close(false);
  }

  return (
    <Dialog open={open} onOpenChange={close}>
      <DialogContent className="w-[min(26rem,calc(100vw-2rem))]">
        <DialogHeader>
          <DialogTitle>Đổi mật khẩu</DialogTitle>
        </DialogHeader>
        <div className="space-y-3">
          <FormField id="pwd-current" label="Mật khẩu hiện tại">
            <Input
              id="pwd-current"
              type="password"
              value={form.current}
              onChange={(e) => setForm({ ...form, current: e.target.value })}
            />
          </FormField>
          <FormField
            id="pwd-next"
            label="Mật khẩu mới"
            error={tooShort ? "Mật khẩu tối thiểu 6 ký tự." : null}
          >
            <Input
              id="pwd-next"
              type="password"
              value={form.next}
              onChange={(e) => setForm({ ...form, next: e.target.value })}
            />
          </FormField>
          <FormField
            id="pwd-confirm"
            label="Xác nhận mật khẩu mới"
            error={mismatch ? "Mật khẩu xác nhận không khớp." : null}
          >
            <Input
              id="pwd-confirm"
              type="password"
              value={form.confirm}
              onChange={(e) => setForm({ ...form, confirm: e.target.value })}
            />
          </FormField>
        </div>
        <DialogFooter>
          <Button variant="secondary" onClick={() => close(false)}>
            Quay lại
          </Button>
          <Button disabled={pending || !canSubmit} onClick={submit}>
            Đổi mật khẩu
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
