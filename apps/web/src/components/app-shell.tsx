import Link from "next/link";
import type { ReactNode } from "react";

import { MODULE_LIST } from "@/lib/modules";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <nav className="w-64 shrink-0 border-r border-slate-200 bg-white p-4">
        <Link href="/" className="block text-base font-semibold text-slate-900">
          Quản lý nhà hàng
        </Link>
        <ul className="mt-6 space-y-1">
          {MODULE_LIST.map((descriptor) => (
            <li key={descriptor.key}>
              <Link
                href={descriptor.path}
                className="block rounded-md px-3 py-2 text-sm text-slate-700 hover:bg-slate-100"
              >
                {descriptor.title}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
      <main className="flex-1 bg-slate-50 p-8">{children}</main>
    </div>
  );
}
