import { Suspense } from "react";

import { LoadingState } from "@/components/page-states";
import { AssistantScreen } from "@/features/assistant/assistant-screen";

export default function AssistantPage() {
  return (
    <Suspense fallback={<LoadingState rows={4} />}>
      <AssistantScreen />
    </Suspense>
  );
}
