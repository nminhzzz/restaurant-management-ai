import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

let search = "";
const replace = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace }),
  usePathname: () => "/assistant",
  useSearchParams: () => new URLSearchParams(search),
}));
vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { ApiError, apiFetch } from "@/lib/api-client";
import { saveSession } from "@/lib/session";
import { AssistantScreen } from "./assistant-screen";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;
const reply = {
  answer: "a",
  headline: "Có 2 đơn.",
  highlights: [],
  follow_ups: [],
  scope_note: null,
  columns: [],
  kind: "answer",
  data: [],
  chart: null,
  detail: null,
  session_id: 9,
};

describe("AssistantScreen", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    search = "";
    saveSession({ token: "t", role: "MANAGER", username: "quanly" });
  });

  it("greets, asks a starter question and shows the answer", async () => {
    fetchMock.mockImplementation((path: string) =>
      Promise.resolve(
        path.startsWith("/assistant/sessions")
          ? { items: [], total: 0, page: 1, size: 50 }
          : reply,
      ),
    );
    render(<AssistantScreen />);
    expect(screen.getByText(/Chào quanly/)).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: /Doanh thu 7 ngày gần nhất/ }),
    );
    expect(await screen.findByText("Có 2 đơn.")).toBeInTheDocument();
  });

  it("opens the session named in the URL", async () => {
    search = "session=5";
    fetchMock.mockImplementation((path: string) =>
      Promise.resolve(
        path === "/assistant/sessions/5"
          ? {
              id: 5,
              title: "Cũ?",
              turns: [
                {
                  id: 1,
                  question: "Cũ?",
                  headline: "Đáp cũ.",
                  highlights: [],
                  status: "Thành công",
                  occurred_at: "",
                },
              ],
            }
          : { items: [], total: 0, page: 1, size: 50 },
      ),
    );
    render(<AssistantScreen />);
    expect(await screen.findByText("Đáp cũ.")).toBeInTheDocument();
  });

  it("falls back to a new chat when the URL session is not the user's", async () => {
    search = "session=99";
    fetchMock.mockImplementation((path: string) =>
      path === "/assistant/sessions/99"
        ? Promise.reject(
            new ApiError(404, "NOT_FOUND", "Không tìm thấy cuộc trò chuyện."),
          )
        : Promise.resolve({ items: [], total: 0, page: 1, size: 50 }),
    );
    render(<AssistantScreen />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Không tìm thấy cuộc trò chuyện.",
    );
    expect(screen.getByText(/Chào quanly/)).toBeInTheDocument();
    expect(replace).toHaveBeenCalledWith("/assistant");
  });
});
