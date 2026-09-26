import type { ModuleKey } from "@/lib/modules";

export type Suggestion = { topic: string; module: ModuleKey; text: string };

const BY_ROLE: Record<string, Suggestion[]> = {
  MANAGER: [
    {
      topic: "Doanh thu",
      module: "reports",
      text: "Doanh thu 7 ngày gần nhất theo từng ngày?",
    },
    {
      topic: "Món ăn",
      module: "catalog",
      text: "Món nào bán chạy nhất tuần này?",
    },
    {
      topic: "Thanh toán",
      module: "sales",
      text: "So sánh doanh thu tiền mặt và QR tháng này",
    },
    {
      topic: "Kho",
      module: "inventory",
      text: "Nguyên liệu nào đang dưới mức tối thiểu?",
    },
    {
      topic: "Kho",
      module: "inventory",
      text: "Những lô nào sắp hết hạn trong tuần này?",
    },
    {
      topic: "Báo cáo",
      module: "reports",
      text: "Tỉ lệ order bị hủy tháng này là bao nhiêu?",
    },
    {
      topic: "Cài đặt",
      module: "settings",
      text: "Hôm nay có bao nhiêu hoá đơn đã thanh toán?",
    },
  ],
  CASHIER: [
    {
      topic: "Hoá đơn",
      module: "sales",
      text: "Hôm nay đã có bao nhiêu hóa đơn?",
    },
    {
      topic: "Doanh thu",
      module: "sales",
      text: "Doanh thu ca hôm nay là bao nhiêu?",
    },
    {
      topic: "Đối soát",
      module: "sales",
      text: "Có order nào đang chờ đối soát không?",
    },
    {
      topic: "Món ăn",
      module: "catalog",
      text: "Món nào bán chạy nhất hôm nay?",
    },
  ],
  WAREHOUSE: [
    {
      topic: "Tồn kho",
      module: "inventory",
      text: "Nguyên liệu nào đang dưới mức tối thiểu?",
    },
    {
      topic: "Tồn kho",
      module: "inventory",
      text: "Tồn kho thịt bò hiện còn bao nhiêu?",
    },
    {
      topic: "Lô hàng",
      module: "inventory",
      text: "Những lô nào sắp hết hạn trong tuần này?",
    },
  ],
};

export function suggestionsFor(
  role: string | undefined,
  module?: ModuleKey,
): Suggestion[] {
  const all = BY_ROLE[role ?? ""] ?? BY_ROLE.MANAGER;
  if (!module) return all;
  const matching = all.filter((s) => s.module === module);
  return matching.length > 0 ? matching : all;
}
