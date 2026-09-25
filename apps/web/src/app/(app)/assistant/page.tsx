import { PageHeader } from "@/components/page-states";
import { ChatPanel } from "@/features/assistant/chat-panel";

export default function AssistantPage() {
  return (
    <div className="space-y-5">
      <PageHeader
        title="Trợ lý AI"
        description="Hỏi về doanh thu, order và tồn kho bằng tiếng Việt."
      />
      <ChatPanel />
    </div>
  );
}
