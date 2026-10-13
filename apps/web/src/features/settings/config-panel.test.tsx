import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
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
  GioBatDauBusinessDateMoi: null,
  NgayHieuLucGioMoi: null,
  SoNgayCanhBaoHetHan: 3,
  SoCauHoiAIMoiNgay: 50,
  ThoiGianGiuChoPhut: 5,
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

  it("shows runtime defaults and explains the effect of changing hold time", async () => {
    fetchMock.mockResolvedValue(config);
    render(<ConfigPanel />);

    expect(
      await screen.findByLabelText("Số ngày cảnh báo sắp hết hạn"),
    ).toHaveValue("3");
    expect(
      screen.getByLabelText("Hạn mức câu hỏi AI mỗi người mỗi ngày"),
    ).toHaveValue("50");
    expect(screen.getByLabelText("Thời gian giữ chỗ (phút)")).toHaveValue("5");
    expect(
      screen.getByText(/giữ nguyên thời điểm hết hạn đã ghi nhận/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/chưa có giờ mới đang chờ áp dụng/i),
    ).toBeInTheDocument();
  });

  it("shows the pending hour and effective Business Date", async () => {
    fetchMock.mockResolvedValue({
      ...config,
      GioBatDauBusinessDateMoi: "04:00:00",
      NgayHieuLucGioMoi: "2099-10-12",
    });
    render(<ConfigPanel />);

    expect(
      await screen.findByText(/04:00 từ Business Date 12\/10\/2099/),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Giờ bắt đầu Business Date")).toHaveValue(
      "06:00:00",
    );
  });

  it.each([
    ["2026-10-11T21:00:00.000Z", "04:00:00"],
    ["2026-10-11T21:00:01.000Z", "04:00:00"],
  ])(
    "shows the new hour as active at and after activation (%s)",
    async (instant, hour) => {
      vi.useFakeTimers();
      try {
        vi.setSystemTime(new Date(instant));
        fetchMock.mockResolvedValue({
          ...config,
          GioBatDauBusinessDateMoi: "04:00:00",
          NgayHieuLucGioMoi: "2026-10-12",
        });
        render(<ConfigPanel />);
        await act(async () => {});

        expect(screen.getByLabelText("Giờ bắt đầu Business Date")).toHaveValue(
          hour,
        );
        expect(
          screen.getByText(/chưa có giờ mới đang chờ áp dụng/i),
        ).toBeInTheDocument();
        expect(
          screen.queryByText(/giờ đang chờ áp dụng: 04:00/i),
        ).not.toBeInTheDocument();
      } finally {
        cleanup();
        vi.useRealTimers();
      }
    },
  );

  it("switches the displayed hour when activation arrives while mounted", async () => {
    vi.useFakeTimers();
    try {
      vi.setSystemTime(new Date("2026-10-11T20:59:59.000Z"));
      fetchMock.mockResolvedValue({
        ...config,
        GioBatDauBusinessDateMoi: "04:00:00",
        NgayHieuLucGioMoi: "2026-10-12",
      });
      render(<ConfigPanel />);
      await act(async () => {});

      expect(screen.getByLabelText("Giờ bắt đầu Business Date")).toHaveValue(
        "06:00:00",
      );
      expect(
        screen.getByText(/04:00 từ Business Date 12\/10\/2026/),
      ).toBeInTheDocument();

      await act(async () => {
        vi.advanceTimersByTime(1000);
      });
      expect(screen.getByLabelText("Giờ bắt đầu Business Date")).toHaveValue(
        "04:00:00",
      );
      expect(
        screen.getByText(/chưa có giờ mới đang chờ áp dụng/i),
      ).toBeInTheDocument();
    } finally {
      cleanup();
      vi.useRealTimers();
    }
  });

  it("updates immediately if activation passes between render and effect", async () => {
    const activationMs = Date.parse("2026-10-12T04:00:00+07:00");
    let nowCalls = 0;
    vi.spyOn(Date, "now").mockImplementation(() => {
      nowCalls += 1;
      return nowCalls === 1 ? activationMs - 1 : activationMs;
    });
    fetchMock.mockResolvedValue({
      ...config,
      GioBatDauBusinessDateMoi: "04:00:00",
      NgayHieuLucGioMoi: "2026-10-12",
    });

    render(<ConfigPanel />);

    const businessDateHour = await screen.findByLabelText(
      "Giờ bắt đầu Business Date",
    );
    await vi.waitFor(() => expect(businessDateHour).toHaveValue("04:00:00"));
    expect(
      screen.getByText(/chưa có giờ mới đang chờ áp dụng/i),
    ).toBeInTheDocument();
    expect(nowCalls).toBeGreaterThanOrEqual(2);
  });

  it("sends a replacement pending hour and positive runtime settings", async () => {
    fetchMock.mockResolvedValue(config);
    render(<ConfigPanel />);

    fireEvent.change(
      await screen.findByLabelText("Giờ bắt đầu Business Date mới"),
      {
        target: { value: "07:30" },
      },
    );
    fireEvent.change(screen.getByLabelText("Số ngày cảnh báo sắp hết hạn"), {
      target: { value: "4" },
    });
    fireEvent.change(
      screen.getByLabelText("Hạn mức câu hỏi AI mỗi người mỗi ngày"),
      {
        target: { value: "75" },
      },
    );
    fireEvent.change(screen.getByLabelText("Thời gian giữ chỗ (phút)"), {
      target: { value: "8" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Lưu cấu hình" }));

    await vi.waitFor(() => {
      const request = fetchMock.mock.calls.find(
        ([, options]) => options?.method === "PUT",
      );
      expect(request?.[1].body).toMatchObject({
        GioBatDauBusinessDateMoi: "07:30",
        SoNgayCanhBaoHetHan: 4,
        SoCauHoiAIMoiNgay: 75,
        ThoiGianGiuChoPhut: 8,
        TenNhaHang: "Nhà hàng ABC",
        NguongTonMacDinh: 5,
      });
      expect(request?.[1].body).not.toHaveProperty("GioBatDauBusinessDate");
    });
  });

  it.each([
    ["Số ngày cảnh báo sắp hết hạn", "0"],
    ["Hạn mức câu hỏi AI mỗi người mỗi ngày", "-1"],
    ["Thời gian giữ chỗ (phút)", "1.5"],
  ])(
    "rejects a nonpositive or noninteger value for %s",
    async (label, invalid) => {
      fetchMock.mockResolvedValue(config);
      render(<ConfigPanel />);

      fireEvent.change(await screen.findByLabelText(label), {
        target: { value: invalid },
      });
      expect(
        screen.getByRole("button", { name: "Lưu cấu hình" }),
      ).toBeDisabled();
      expect(
        fetchMock.mock.calls.filter(([, options]) => options?.method === "PUT"),
      ).toHaveLength(0);
    },
  );

  it("does not reschedule a pending hour when another field is saved", async () => {
    fetchMock.mockResolvedValue({
      ...config,
      GioBatDauBusinessDateMoi: "04:00:00",
      NgayHieuLucGioMoi: "2026-10-12",
    });
    render(<ConfigPanel />);

    fireEvent.change(await screen.findByLabelText("Tên nhà hàng"), {
      target: { value: "Nhà hàng mới" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Lưu cấu hình" }));
    await vi.waitFor(() => {
      const request = fetchMock.mock.calls.find(
        ([, options]) => options?.method === "PUT",
      );
      expect(request?.[1].body).not.toHaveProperty("GioBatDauBusinessDateMoi");
    });
  });

  it("accepts a decimal default stock threshold", async () => {
    fetchMock.mockImplementation(
      (_path: string, options?: { method?: string }) =>
        Promise.resolve(options?.method === "PUT" ? config : config),
    );
    render(<ConfigPanel />);

    fireEvent.change(
      await screen.findByLabelText("Ngưỡng tồn tối thiểu mặc định"),
      { target: { value: "2.5" } },
    );
    fireEvent.click(screen.getByRole("button", { name: "Lưu cấu hình" }));

    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/settings/config",
        expect.objectContaining({
          body: expect.objectContaining({ NguongTonMacDinh: 2.5 }),
        }),
      ),
    );
  });

  it("blocks values above the API limits before saving", async () => {
    fetchMock.mockResolvedValue(config);
    render(<ConfigPanel />);

    fireEvent.change(await screen.findByLabelText("Thời gian giữ chỗ (phút)"), {
      target: { value: "2000" },
    });
    expect(screen.getByText("Giá trị tối đa là 1440.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Lưu cấu hình" })).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Thời gian giữ chỗ (phút)"), {
      target: { value: "10" },
    });
    fireEvent.change(screen.getByLabelText("Số ngày cảnh báo sắp hết hạn"), {
      target: { value: "400" },
    });
    expect(screen.getByText("Giá trị tối đa là 365.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Lưu cấu hình" })).toBeDisabled();
  });
});
