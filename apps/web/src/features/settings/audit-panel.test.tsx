import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { AuditPanel } from "./audit-panel";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

/** Route the mocked apiFetch by path prefix; the first matching prefix wins. */
function stubByPath(routes: Record<string, unknown>) {
  const entries = Object.entries(routes);
  fetchMock.mockImplementation((path: string) =>
    Promise.resolve(
      entries.find(([prefix]) => path.startsWith(prefix))?.[1] ?? {},
    ),
  );
}

const users = {
  items: [{ MaNguoiDung: 2, HoTen: "Phạm Thu Hà" }],
  total: 1,
};

const actions = ["CREATE_USER", "LOCK_USER"];

const oneEntry = {
  items: [
    {
      MaNhatKy: 1,
      MaNguoiDung: 2,
      ThoiDiem: "2026-09-20T08:00:00",
      LoaiThaoTac: "LOCK_USER",
      DoiTuong: "NGUOI_DUNG",
      MaDoiTuong: "5",
      DuLieuTruoc: null,
      DuLieuSau: null,
      LyDo: null,
    },
  ],
  total: 25,
  page: 1,
  size: 20,
};

describe("AuditPanel", () => {
  beforeEach(() => vi.resetAllMocks());
  afterEach(cleanup);

  it("sends the action, user and date range filters as query params", async () => {
    stubByPath({
      "/settings/audit-log/actions": actions,
      "/settings/audit-log": oneEntry,
      "/settings/users": users,
    });
    render(<AuditPanel />);

    await screen.findByRole("cell", { name: "LOCK_USER" });

    fireEvent.change(screen.getByLabelText("Loại thao tác"), {
      target: { value: "LOCK_USER" },
    });
    fireEvent.change(screen.getByLabelText("Người thực hiện"), {
      target: { value: "2" },
    });
    fireEvent.change(screen.getByLabelText("Từ ngày"), {
      target: { value: "2026-09-01" },
    });
    fireEvent.change(screen.getByLabelText("Đến ngày"), {
      target: { value: "2026-09-30" },
    });

    await vi.waitFor(() => {
      const calls = fetchMock.mock.calls.filter((call: unknown[]) =>
        (call[0] as string).startsWith("/settings/audit-log?"),
      );
      expect(calls.length).toBeGreaterThan(0);
      const url = new URLSearchParams(calls[calls.length - 1][0].split("?")[1]);
      expect(url.get("action")).toBe("LOCK_USER");
      expect(url.get("user_id")).toBe("2");
      expect(url.get("date_from")).toBe("2026-09-01");
      expect(url.get("date_to")).toBe("2026-09-30");
    });
  });

  it("shows the paging summary from the server total", async () => {
    stubByPath({
      "/settings/audit-log/actions": actions,
      "/settings/audit-log": oneEntry,
      "/settings/users": users,
    });
    render(<AuditPanel />);

    expect(
      await screen.findByText(/Hiển thị 1–20 trên 25/),
    ).toBeInTheDocument();
  });
});
