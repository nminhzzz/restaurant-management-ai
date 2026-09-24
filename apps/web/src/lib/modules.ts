export type ModuleKey =
  "catalog" | "sales" | "inventory" | "reports" | "settings" | "assistant";

export interface ModuleDescriptor {
  key: ModuleKey;
  path: string;
  title: string;
  allowedRoles: string[]; // UI only; API still enforces NFR-05
  requirements: string;
  owner: string;
  summary: string;
}

export const MODULE_LIST: readonly ModuleDescriptor[] = [
  {
    key: "catalog",
    path: "/catalog",
    title: "Quản lý danh mục",
    requirements: "FR-CAT-01 … FR-CAT-28",
    owner: "Hùng",
    allowedRoles: ["MANAGER", "WAREHOUSE"],
    summary:
      "Nhóm món, món ăn, phiên bản giá và công thức, nguyên liệu, nhà cung cấp, sơ đồ bàn.",
  },
  {
    key: "sales",
    path: "/sales",
    title: "Quản lý bán hàng",
    requirements: "FR-SALE-01 … FR-SALE-29",
    owner: "Hùng",
    allowedRoles: ["MANAGER", "CASHIER"],
    summary: "Order, ghi chú món, đổi bàn, thanh toán, hóa đơn và phiếu bếp.",
  },
  {
    key: "inventory",
    path: "/inventory",
    title: "Quản lý kho",
    requirements: "FR-INV-01 … FR-INV-12",
    owner: "Minh",
    allowedRoles: ["MANAGER", "WAREHOUSE"],
    summary:
      "Nhập kho theo lô, trừ kho FIFO, xuất thủ công, kiểm kê và cảnh báo tồn tối thiểu.",
  },
  {
    key: "reports",
    path: "/reports",
    title: "Báo cáo thống kê",
    requirements: "FR-REP-01 … FR-REP-10",
    owner: "Minh",
    allowedRoles: ["MANAGER"],
    summary:
      "Doanh thu, xếp hạng món, biên lợi nhuận gộp, phân bố theo khung giờ.",
  },
  {
    key: "settings",
    path: "/settings",
    title: "Cài đặt hệ thống",
    requirements: "FR-SET-01 … FR-SET-09",
    owner: "Minh",
    allowedRoles: ["MANAGER"],
    summary:
      "Tài khoản, phân quyền, cấu hình chung, sao lưu và nhật ký thao tác rủi ro cao.",
  },
  {
    key: "assistant",
    path: "/assistant",
    title: "Trợ lý AI",
    requirements: "FR-AI-01 … FR-AI-09",
    owner: "Hùng · Minh",
    allowedRoles: ["MANAGER", "CASHIER", "WAREHOUSE"],
    summary:
      "Hỏi đáp và phân tích dữ liệu kinh doanh bằng tiếng Việt qua Text-to-SQL.",
  },
];

export const MODULES = Object.fromEntries(
  MODULE_LIST.map((descriptor) => [descriptor.key, descriptor]),
) as Record<ModuleKey, ModuleDescriptor>;
