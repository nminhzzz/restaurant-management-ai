import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

const replace = vi.fn();
const push = vi.fn();

vi.mock("next/navigation", () => ({
  usePathname: () => "/sales",
  useRouter: () => ({ replace, push }),
}));
vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn().mockResolvedValue({ items: [] }) };
});

import { AppShell } from "@/components/app-shell";
import { saveSession } from "@/lib/session";

describe("AppShell", () => {
  afterEach(() => {
    sessionStorage.clear();
    replace.mockReset();
    push.mockReset();
  });

  it("sends an unauthenticated visitor to the login page", () => {
    render(
      <AppShell>
        <p>nội dung bảo vệ</p>
      </AppShell>,
    );

    expect(replace).toHaveBeenCalledWith("/login");
    expect(screen.queryByText("nội dung bảo vệ")).not.toBeInTheDocument();
  });

  it("renders the module content when a session exists", () => {
    saveSession({ token: "t", role: "MANAGER", username: "quanly" });

    render(
      <AppShell>
        <p>nội dung bảo vệ</p>
      </AppShell>,
    );

    expect(screen.getByText("nội dung bảo vệ")).toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();
  });
});
