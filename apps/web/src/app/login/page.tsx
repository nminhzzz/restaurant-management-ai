import { UtensilsCrossed } from "lucide-react";

import { LoginForm } from "@/features/auth/login-form";

export default function LoginPage() {
  return (
    <main className="grid min-h-screen place-items-center px-4 py-10">
      <div className="w-full max-w-sm space-y-6">
        <div className="flex items-center gap-2.5 text-[15px] font-bold tracking-tight">
          <span className="grid size-9 place-items-center rounded-control bg-primary text-white">
            <UtensilsCrossed className="size-5" aria-hidden />
          </span>
          Quản lý nhà hàng
        </div>
        <div className="space-y-5 rounded-container border border-border bg-surface p-6 shadow-[inset_0_4px_0_0_var(--color-ink)]">
          <div className="space-y-1">
            <h1 className="text-2xl font-bold tracking-tight">Đăng nhập</h1>
            <p className="text-muted">Dùng tài khoản do quản lý cấp cho bạn.</p>
          </div>
          <LoginForm />
        </div>
      </div>
    </main>
  );
}
