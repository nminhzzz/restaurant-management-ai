/** Money arrives as a number or as the API's Decimal-as-string. */
export function formatVnd(value: number | string | null | undefined): string {
  const amount = Number(value);
  if (value === null || value === undefined || !Number.isFinite(amount))
    return "";
  return `${amount.toLocaleString("vi-VN")} ₫`;
}

export function formatNumber(
  value: number | string | null | undefined,
): string {
  const amount = Number(value);
  if (value === null || value === undefined || !Number.isFinite(amount))
    return "";
  return amount.toLocaleString("vi-VN", { maximumFractionDigits: 2 });
}

/** `2026-09-25` → `25/09/2026`; anything that is not an ISO date passes through. */
export function formatDate(value: string | null | undefined): string {
  if (!value) return "";
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
  return match ? `${match[3]}/${match[2]}/${match[1]}` : value;
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
