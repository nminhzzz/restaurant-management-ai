import { RevenueChart } from "@/features/reports/revenue-chart";

export default function ReportsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Báo cáo thống kê</h1>
      <RevenueChart />
    </div>
  );
}
