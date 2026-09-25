import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { ConfigPanel } from "./config-panel";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

const config = {
  MaCauHinh: 1,
  TenNhaHang: "Nhà hàng ABC",
  DiaChi: "123 Lê Lợi",
  MauHoaDon: null,
  NguongTonMacDinh: 5,
  GioBatDauBusinessDate: "06:00:00",
};

describe("ConfigPanel", () => {
  beforeEach(() => vi.resetAllMocks());
  afterEach(cleanup);

  it("saves edits through PUT /settings/config", async () => {
    fetchMock.mockImplementation(
      (path: string, options?: { method?: string }) => {
        if (options?.method === "PUT")
          return Promise.resolve({ ...config, TenNhaHang: "Nhà hàng mới" });
        return Promise.resolve(config);
      },
    );

    render(<ConfigPanel />);

    const nameInput = await screen.findByLabelText("Tên nhà hàng");
    fireEvent.change(nameInput, { target: { value: "Nhà hàng mới" } });
    fireEvent.click(screen.getByRole("button", { name: "Lưu cấu hình" }));

    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/settings/config",
        expect.objectContaining({
          method: "PUT",
          body: expect.objectContaining({ TenNhaHang: "Nhà hàng mới" }),
        }),
      ),
    );
  });

  it("shows the Business Date start hour as read-only", async () => {
    fetchMock.mockResolvedValue(config);
    render(<ConfigPanel />);

    const field = await screen.findByLabelText("Giờ bắt đầu Business Date");
    expect(field).toBeDisabled();
    expect(field).toHaveValue("06:00:00");
  });
});
