import { ModulePlaceholder } from "@/components/module-placeholder";
import { MODULES } from "@/lib/modules";

export default function SettingsPage() {
  return <ModulePlaceholder descriptor={MODULES.settings} />;
}
