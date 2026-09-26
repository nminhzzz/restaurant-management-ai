import { Suspense } from "react";

import { LoadingState } from "@/components/page-states";
import { SalesWorkspace } from "@/features/sales/sales-workspace";

export default function SalesPage() {
  return (
    <Suspense fallback={<LoadingState rows={6} />}>
      <SalesWorkspace />
    </Suspense>
  );
}
