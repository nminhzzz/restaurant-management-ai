"use client";

import { useState } from "react";

import { FormField } from "@/components/form-field";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input, Textarea } from "@/components/ui/input";

export type DialogField = {
  name: string;
  label: string;
  required?: boolean;
  multiline?: boolean;
  help?: string;
};

export type FieldValues = Record<string, string>;

/**
 * Small form in a dialog for audited payment actions (verification, reopen, refund...).
 * `requireOneOf` lists fields of which at least one must be filled (FR-SALE-19).
 */
export function FieldsDialog({
  open,
  onOpenChange,
  title,
  description,
  fields,
  requireOneOf,
  confirmLabel,
  danger = false,
  pending = false,
  error,
  onSubmit,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  fields: DialogField[];
  requireOneOf?: string[];
  confirmLabel: string;
  danger?: boolean;
  pending?: boolean;
  error?: string | null;
  onSubmit: (values: FieldValues) => void;
}) {
  const [values, setValues] = useState<FieldValues>({});

  const value = (name: string) => (values[name] ?? "").trim();
  const missingRequired = fields.some(
    (f) => f.required && value(f.name) === "",
  );
  const missingOneOf =
    requireOneOf !== undefined && requireOneOf.every((n) => value(n) === "");
  const trimmed = Object.fromEntries(
    fields.map((f) => [f.name, value(f.name)]),
  );

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!next) setValues({});
        onOpenChange(next);
      }}
    >
      <DialogContent className="w-[min(28rem,calc(100vw-2rem))]">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          {description ? (
            <DialogDescription>{description}</DialogDescription>
          ) : null}
        </DialogHeader>
        <div className="space-y-3">
          {fields.map((field) => {
            const id = `field-${field.name}`;
            const update = (text: string) =>
              setValues((v) => ({ ...v, [field.name]: text }));
            return (
              <FormField
                key={field.name}
                id={id}
                label={field.label}
                help={field.help}
              >
                {field.multiline ? (
                  <Textarea
                    id={id}
                    rows={3}
                    value={values[field.name] ?? ""}
                    onChange={(e) => update(e.target.value)}
                  />
                ) : (
                  <Input
                    id={id}
                    value={values[field.name] ?? ""}
                    onChange={(e) => update(e.target.value)}
                  />
                )}
              </FormField>
            );
          })}
          {error ? (
            <p role="alert" className="text-danger-fg">
              {error}
            </p>
          ) : null}
        </div>
        <DialogFooter>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>
            Quay lại
          </Button>
          <Button
            variant={danger ? "danger" : "primary"}
            disabled={pending || missingRequired || missingOneOf}
            onClick={() => onSubmit(trimmed)}
          >
            {confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
