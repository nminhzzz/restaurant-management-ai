export type StatusTone =
  "neutral" | "primary" | "success" | "warning" | "danger" | "muted";

// docs/design/tokens.md §2.3 — keys are the status values stored in the database.
const TONES: Record<string, StatusTone> = {
  "Hoạt động": "success",
  "Đã thanh toán": "success",
  "Còn hạn": "success",
  "Đang áp dụng": "success",
  "Chờ áp dụng": "muted",
  Trống: "success",
  "Chờ xác minh thanh toán": "warning",
  "Tạm tính": "warning",
  "Hết nguyên liệu": "danger",
  "Đã hủy": "danger",
  "Hết hạn": "danger",
  "Đang mở": "primary",
  "Chờ làm": "primary",
  "Chờ in": "primary",
  "Chờ xác nhận": "primary",
  "Đang phục vụ": "primary",
  Ẩn: "neutral",
  "Đã khóa": "neutral",
  "Đã phục vụ": "neutral",
  "Đã đặt": "neutral",
  Nháp: "muted",
  "Hiệu lực": "success",
  "Đang kiểm kê": "primary",
  "Đã xác nhận": "success",
};

export function statusTone(status: string | null | undefined): StatusTone {
  return (status && TONES[status]) || "neutral";
}
