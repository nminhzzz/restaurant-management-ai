"use client";

import { KeyRound, LogOut, Menu, UtensilsCrossed, X } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useMemo, useState, useSyncExternalStore, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { ChangePasswordDialog } from "@/features/settings/change-password-dialog";
import { MODULE_LIST, homePathFor } from "@/lib/modules";
import { roleLabel } from "@/lib/roles";
import {
  clearSession,
  parseSession,
  serverSessionSnapshot,
  sessionSnapshot,
  subscribeSession,
} from "@/lib/session";
import { cn } from "@/lib/utils";

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [changePasswordOpen, setChangePasswordOpen] = useState(false);

  // The session lives in sessionStorage: `useSyncExternalStore` reads it on the client
  // and answers `null` on the server, so the two renders cannot disagree.
  const stored = useSyncExternalStore(
    subscribeSession,
    sessionSnapshot,
    serverSessionSnapshot,
  );
  const session = useMemo(() => parseSession(stored), [stored]);

  const modules = MODULE_LIST.filter(
    (descriptor) =>
      session === null || descriptor.allowedRoles.includes(session.role),
  );
  const current = MODULE_LIST.find((descriptor) =>
    pathname.startsWith(descriptor.path),
  );

  function logout() {
    clearSession();
    router.push("/login");
  }

  const navigation = (
    <nav className="flex h-full flex-col gap-5 px-3 py-4">
      <Link
        href={homePathFor(session?.role)}
        className="flex items-center gap-2.5 px-2 text-[15px] font-semibold text-ink"
      >
        <span className="grid size-8 place-items-center rounded-control bg-primary text-white">
          <UtensilsCrossed className="size-4" aria-hidden />
        </span>
        Quản lý nhà hàng
      </Link>

      <ul className="flex-1 space-y-0.5">
        {modules.map((descriptor) => {
          const active = current?.key === descriptor.key;
          const Icon = descriptor.icon;
          return (
            <li key={descriptor.key}>
              <Link
                href={descriptor.path}
                aria-current={active ? "page" : undefined}
                onClick={() => setDrawerOpen(false)}
                className={cn(
                  "flex min-h-11 items-center gap-2.5 rounded-control px-2.5 font-medium transition-colors",
                  active
                    ? "bg-primary-subtle text-primary-subtle-fg"
                    : "text-muted hover:bg-surface-sunken hover:text-ink",
                )}
              >
                <Icon className="size-[18px]" aria-hidden />
                {descriptor.title}
              </Link>
            </li>
          );
        })}
      </ul>

      {session === null ? null : (
        <div className="flex items-center gap-2.5 border-t border-border px-2 pt-3">
          <span
            className="grid size-8 shrink-0 place-items-center rounded-full bg-surface-sunken text-xs font-semibold text-muted uppercase"
            aria-hidden
          >
            {session.username.slice(0, 2)}
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate font-medium">{session.username}</p>
            <p className="text-xs text-subtle">{roleLabel(session.role)}</p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            aria-label="Đổi mật khẩu"
            onClick={() => setChangePasswordOpen(true)}
          >
            <KeyRound />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            aria-label="Đăng xuất"
            onClick={logout}
          >
            <LogOut />
          </Button>
        </div>
      )}
    </nav>
  );

  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 border-r border-border bg-surface lg:block">
        {navigation}
      </aside>

      {drawerOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button
            aria-label="Đóng menu"
            className="absolute inset-0 bg-ink/40"
            onClick={() => setDrawerOpen(false)}
          />
          <aside className="relative h-full w-64 border-r border-border bg-surface">
            <button
              aria-label="Đóng menu"
              className="absolute top-4 right-3 rounded-control p-1 text-subtle hover:bg-surface-sunken"
              onClick={() => setDrawerOpen(false)}
            >
              <X className="size-4" />
            </button>
            {navigation}
          </aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex items-center gap-2 border-b border-border bg-surface px-3 py-2 lg:hidden">
          <Button
            variant="ghost"
            size="icon"
            aria-label="Mở menu"
            onClick={() => setDrawerOpen(true)}
          >
            <Menu />
          </Button>
          <span className="font-semibold">
            {current?.title ?? "Quản lý nhà hàng"}
          </span>
        </header>
        <main className="flex-1 p-4 lg:p-6">
          <div className="mx-auto w-full max-w-7xl">{children}</div>
        </main>
      </div>

      <ChangePasswordDialog
        open={changePasswordOpen}
        onOpenChange={setChangePasswordOpen}
      />
    </div>
  );
}
