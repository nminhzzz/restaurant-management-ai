"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CancelledReport } from "@/features/reports/cancelled-report";
import { ComparisonReport } from "@/features/reports/comparison-report";
import { DishRanking } from "@/features/reports/dish-ranking";
import { HourlyReport } from "@/features/reports/hourly-report";
import { MarginReport } from "@/features/reports/margin-report";
import { RevenueChart } from "@/features/reports/revenue-chart";

const TABS = [
  { value: "revenue", label: "Doanh thu" },
  { value: "dishes", label: "Món ăn" },
  { value: "hours", label: "Khung giờ" },
  { value: "margin", label: "Lợi nhuận" },
  { value: "comparison", label: "So sánh" },
  { value: "cancelled", label: "Order hủy" },
];

export function ReportsWorkspace() {
  return (
    <Tabs defaultValue="revenue">
      <TabsList>
        {TABS.map((tab) => (
          <TabsTrigger key={tab.value} value={tab.value}>
            {tab.label}
          </TabsTrigger>
        ))}
      </TabsList>
      <TabsContent value="revenue">
        <RevenueChart />
      </TabsContent>
      <TabsContent value="dishes">
        <DishRanking />
      </TabsContent>
      <TabsContent value="hours">
        <HourlyReport />
      </TabsContent>
      <TabsContent value="margin">
        <MarginReport />
      </TabsContent>
      <TabsContent value="comparison">
        <ComparisonReport />
      </TabsContent>
      <TabsContent value="cancelled">
        <CancelledReport />
      </TabsContent>
    </Tabs>
  );
}
