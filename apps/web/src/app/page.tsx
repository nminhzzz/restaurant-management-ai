import Link from "next/link";

import { MODULE_LIST } from "@/lib/modules";

export default function HomePage() {
  return (
    <main className="mx-auto w-full max-w-3xl space-y-8 p-10">
      <header className="space-y-2">
        <h1 className="text-3xl font-semibold">
          Hệ thống quản lý nhà hàng tích hợp AI
        </h1>
        <p className="text-slate-600">
          Sáu module nghiệp vụ và khối trợ lý AI hỏi đáp dữ liệu kinh doanh bằng
          tiếng Việt.
        </p>
      </header>
      <ul className="grid gap-3 sm:grid-cols-2">
        {MODULE_LIST.map((descriptor) => (
          <li key={descriptor.key}>
            <Link
              href={descriptor.path}
              className="block h-full rounded-lg border border-slate-200 bg-white p-4 hover:border-slate-400"
            >
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                {descriptor.requirements}
              </p>
              <p className="mt-1 font-medium">{descriptor.title}</p>
              <p className="mt-1 text-sm text-slate-600">
                {descriptor.summary}
              </p>
            </Link>
          </li>
        ))}
      </ul>
      <Link
        href="/login"
        className="inline-block text-sm font-medium underline"
      >
        Đăng nhập
      </Link>
    </main>
  );
}
