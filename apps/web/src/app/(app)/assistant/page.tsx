import { ChatPanel } from "@/features/assistant/chat-panel";
import { ModulePlaceholder } from "@/components/module-placeholder";
import { MODULES } from "@/lib/modules";

export default function AssistantPage() {
  return (
    <div className="space-y-6">
      <ModulePlaceholder descriptor={MODULES.assistant} />
      <ChatPanel />
    </div>
  );
}
