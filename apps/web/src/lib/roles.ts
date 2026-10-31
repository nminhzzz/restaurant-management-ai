const ROLE_LABELS: Record<string, string> = {
  MANAGER: "Quản lý",
  CASHIER: "Thu ngân",
  WAREHOUSE: "Bếp",
};

export function roleLabel(role: string): string {
  return ROLE_LABELS[role] ?? role;
}
