import { PageHeader } from "@/components/page-states";
import { ReportsWorkspace } from "@/features/reports/reports-workspace";

export default function ReportsPage() {
  return (
    <div className="space-y-5">
      <PageHeader
        title="Báo cáo"
        description="Báo cáo tính theo Business Date, từ 06:00 hôm nay tới 06:00 hôm sau."
      />
      <ReportsWorkspace />
    </div>
  );
}
