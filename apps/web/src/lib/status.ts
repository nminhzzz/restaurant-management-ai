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
  "Chờ xác nhận thanh toán": "primary",
  "Chờ xác minh thanh toán": "warning",
  "Đóng – chưa thu được tiền": "danger",
  "Tự động đóng": "neutral",
  "Chờ xử lý": "warning",
  "Đã hoàn tiền": "neutral",
  "Đã áp dụng cho order": "success",
  "Tạm dừng phục vụ": "warning",
  "Thành công": "success",
  "Tạm tính": "warning",
  "Hết nguyên liệu": "danger",
  "Đã hủy": "danger",
  "Hết hạn": "danger",
  "Đang mở": "primary",
  Chờ: "primary",
  "Chờ làm": "primary",
  "Đã xác nhận xong": "neutral",
  "Chờ in": "primary",
  "Chờ xác nhận": "primary",
  "Đang phục vụ": "primary",
  Ẩn: "neutral",
  "Đã khóa": "neutral",
  "Đã phục vụ": "neutral",
  "Đã đặt": "neutral",
  Nháp: "muted",
};

export function statusTone(status: string | null | undefined): StatusTone {
  return (status && TONES[status]) || "neutral";
}
