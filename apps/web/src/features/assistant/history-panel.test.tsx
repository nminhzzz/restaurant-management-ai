import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { groupLabel, HistoryPanel } from "./history-panel";

const now = new Date("2026-09-26T15:00:00");

describe("groupLabel", () => {
  it("buckets by day", () => {
    expect(groupLabel("2026-09-26T09:00:00", now)).toBe("Hôm nay");
    expect(groupLabel("2026-09-25T21:00:00", now)).toBe("Hôm qua");
    expect(groupLabel("2026-09-21T10:00:00", now)).toBe("7 ngày trước");
    expect(groupLabel("2026-08-01T10:00:00", now)).toBe("Cũ hơn");
  });
});

describe("HistoryPanel", () => {
  it("marks the active session and opens another one", async () => {
    (apiFetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      items: [
        {
          id: 2,
          title: "Doanh thu?",
          turn_count: 3,
          created_at: "",
          last_at: new Date().toISOString(),
        },
        {
          id: 1,
          title: "Kho?",
          turn_count: 1,
          created_at: "",
          last_at: new Date().toISOString(),
        },
      ],
      total: 2,
      page: 1,
      size: 50,
    });
    const onSelect = vi.fn();
    render(
      <HistoryPanel
        activeId={2}
        refreshKey={0}
        onSelect={onSelect}
        onNew={vi.fn()}
      />,
    );
    expect(
      await screen.findByRole("button", { name: /Doanh thu\?/ }),
    ).toHaveAttribute("aria-current", "true");
    fireEvent.click(screen.getByRole("button", { name: /Kho\?/ }));
    expect(onSelect).toHaveBeenCalledWith(1);
  });
});
