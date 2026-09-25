import {
  BookOpen,
  ChartColumn,
  MessageSquareText,
  Package,
  ReceiptText,
  Settings,
  type LucideIcon,
} from "lucide-react";

export type ModuleKey =
  "catalog" | "sales" | "inventory" | "reports" | "settings" | "assistant";

export interface ModuleDescriptor {
  key: ModuleKey;
  path: string;
  title: string;
  icon: LucideIcon;
  allowedRoles: string[]; // UI only; API still enforces NFR-05
}

export const MODULE_LIST: readonly ModuleDescriptor[] = [
  {
    key: "catalog",
    path: "/catalog",
    title: "Danh mục",
    icon: BookOpen,
    // Cashier reads dishes and table status (report §3.4.2, Bảng 33).
    allowedRoles: ["MANAGER", "CASHIER", "WAREHOUSE"],
  },
  {
    key: "sales",
    path: "/sales",
    title: "Bán hàng",
    icon: ReceiptText,
    allowedRoles: ["MANAGER", "CASHIER"],
  },
  {
    key: "inventory",
    path: "/inventory",
    title: "Kho",
    icon: Package,
    allowedRoles: ["MANAGER", "WAREHOUSE"],
  },
  {
    key: "reports",
    path: "/reports",
    title: "Báo cáo",
    icon: ChartColumn,
    allowedRoles: ["MANAGER"],
  },
  {
    key: "settings",
    path: "/settings",
    title: "Cài đặt",
    icon: Settings,
    allowedRoles: ["MANAGER"],
  },
  {
    key: "assistant",
    path: "/assistant",
    title: "Trợ lý AI",
    icon: MessageSquareText,
    allowedRoles: ["MANAGER", "CASHIER", "WAREHOUSE"],
  },
];

export const MODULES = Object.fromEntries(
  MODULE_LIST.map((descriptor) => [descriptor.key, descriptor]),
) as Record<ModuleKey, ModuleDescriptor>;

// Each role lands on the screen it opens most, not on the first module in the list.
const HOME_BY_ROLE: Record<string, ModuleKey> = {
  MANAGER: "reports",
  CASHIER: "sales",
  WAREHOUSE: "inventory",
};

export function homePathFor(role: string | null | undefined): string {
  const key = role ? HOME_BY_ROLE[role] : undefined;
  return key ? MODULES[key].path : "/login";
}
