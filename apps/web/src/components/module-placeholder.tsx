import type { ModuleDescriptor } from "@/lib/modules";

export function ModulePlaceholder({
  descriptor,
}: {
  descriptor: ModuleDescriptor;
}) {
  return (
    <section className="space-y-4">
      <header className="space-y-1">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
          {descriptor.requirements}
        </p>
        <h1 className="text-2xl font-semibold text-slate-900">
          {descriptor.title}
        </h1>
        <p className="text-sm text-slate-600">{descriptor.summary}</p>
      </header>
      <p className="rounded-lg border border-dashed border-slate-300 bg-white p-4 text-sm text-slate-500">
        Màn hình nghiệp vụ chưa được triển khai. Phụ trách: {descriptor.owner}.
      </p>
    </section>
  );
}
