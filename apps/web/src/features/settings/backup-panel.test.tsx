import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { BackupPanel } from "./backup-panel";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

describe("BackupPanel", () => {
  beforeEach(() => vi.resetAllMocks());
  afterEach(cleanup);

  it("downloads the backup dump returned by the API", async () => {
    fetchMock.mockResolvedValue({ created_at: "2026-09-25T00:00:00Z" });

    const createObjectURL = vi.fn(() => "blob:mock");
    const revokeObjectURL = vi.fn();
    Object.assign(URL, { createObjectURL, revokeObjectURL });
    const clickSpy = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => {});

    render(<BackupPanel />);
    fireEvent.click(screen.getByRole("button", { name: "Xuất bản sao" }));

    await vi.waitFor(() => expect(clickSpy).toHaveBeenCalled());

    expect(fetchMock).toHaveBeenCalledWith(
      "/settings/backup",
      expect.objectContaining({ method: "POST" }),
    );
    expect(createObjectURL).toHaveBeenCalled();
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:mock");

    clickSpy.mockRestore();
  });
});
