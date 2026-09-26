import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

let pathname = "/inventory";
const push = vi.fn();
vi.mock("next/navigation", () => ({
  usePathname: () => pathname,
  useRouter: () => ({ push }),
}));
vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { saveSession } from "@/lib/session";
import { AssistantWidget } from "./assistant-widget";

const reply = {
  answer: "a",
  headline: "Có 3 nguyên liệu sắp hết.",
  highlights: [],
  follow_ups: [],
  scope_note: null,
  columns: [],
  kind: "answer",
  data: [],
  chart: null,
  detail: null,
  session_id: 12,
};

describe("AssistantWidget", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    pathname = "/inventory";
    saveSession({ token: "t", role: "MANAGER", username: "quanly" });
  });

  it("is hidden on the assistant and sales screens", () => {
    pathname = "/sales";
    const { rerender } = render(<AssistantWidget />);
    expect(
      screen.queryByRole("button", { name: /Hỏi trợ lý/ }),
    ).not.toBeInTheDocument();
    pathname = "/assistant";
    rerender(<AssistantWidget />);
    expect(
      screen.queryByRole("button", { name: /Hỏi trợ lý/ }),
    ).not.toBeInTheDocument();
  });

  it("opens with Ctrl+K, suggests questions for the current module and closes with Escape", () => {
    render(<AssistantWidget />);
    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    expect(
      screen.getByRole("dialog", { name: "Trợ lý AI" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Đang ở màn Kho/)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /dưới mức tối thiểu/ }),
    ).toBeInTheDocument();
    fireEvent.keyDown(window, { key: "Escape" });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("leaves a dialog's own Escape alone and does not also minimise the panel", () => {
    render(<AssistantWidget />);
    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    expect(
      screen.getByRole("dialog", { name: "Trợ lý AI" }),
    ).toBeInTheDocument();

    act(() => {
      const event = new KeyboardEvent("keydown", {
        key: "Escape",
        cancelable: true,
      });
      event.preventDefault();
      window.dispatchEvent(event);
    });
    expect(
      screen.getByRole("dialog", { name: "Trợ lý AI" }),
    ).toBeInTheDocument();

    fireEvent.keyDown(window, { key: "Escape" });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("keeps the conversation across screens and opens it full-screen", async () => {
    (apiFetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(reply);
    const { rerender } = render(<AssistantWidget />);
    fireEvent.click(screen.getByRole("button", { name: /Hỏi trợ lý/ }));
    fireEvent.click(screen.getByRole("button", { name: /dưới mức tối thiểu/ }));
    expect(
      await screen.findByText("Có 3 nguyên liệu sắp hết."),
    ).toBeInTheDocument();

    pathname = "/reports";
    rerender(<AssistantWidget />);
    expect(screen.getByText("Có 3 nguyên liệu sắp hết.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Mở toàn màn hình" }));
    expect(push).toHaveBeenCalledWith("/assistant?session=12");
  });
});
