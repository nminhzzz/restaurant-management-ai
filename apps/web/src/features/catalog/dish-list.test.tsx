import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { DishList } from "./dish-list";
import { PriceScheduler } from "./price-scheduler";

const mockFetch = vi.fn();

vi.mock("@/lib/api-client", () => ({
  apiFetch: (...args: unknown[]) => mockFetch(...args),
}));

function stubFetch(data: unknown) {
  mockFetch.mockResolvedValue(data);
}

describe("catalog screens", () => {
  beforeEach(() => mockFetch.mockReset());

  it("shows the four display states of the screen", async () => {
    let resolve!: (v: unknown) => void;
    mockFetch.mockReturnValue(new Promise((r) => (resolve = r)));
    render(<DishList />);
    expect(screen.getByText("Đang tải…")).toBeInTheDocument();
    resolve({
      items: [{ MaMon: 1, TenMon: "Phở bò", TrangThai: "Hoạt động" }],
    });
    expect(await screen.findByText("Phở bò")).toBeInTheDocument();
  });

  it("shows an empty state with a next step when there are no dishes", async () => {
    stubFetch({ items: [], total: 0 });
    render(<DishList />);
    expect(await screen.findByText(/Chưa có món nào/)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Thêm món" }),
    ).toBeInTheDocument();
  });

  it("rejects a scheduled date in the past before calling the API", async () => {
    render(<PriceScheduler dishId={1} />);
    fireEvent.change(screen.getByLabelText("Business Date áp dụng"), {
      target: { value: "2020-01-01" },
    });
    expect(
      screen.getByText(/phải là một Business Date trong tương lai/),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Lưu" })).toBeDisabled();
  });
});
