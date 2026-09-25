import {
  act,
  fireEvent,
  render,
  renderHook,
  screen,
} from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { DataPagination, pageWindow } from "@/components/data-pagination";
import { useClientPagination } from "@/lib/use-client-pagination";

describe("pageWindow", () => {
  it("lists every page when there are few", () => {
    expect(pageWindow(2, 5)).toEqual([1, 2, 3, 4, 5]);
  });

  it("keeps the ends and the neighbours, with gaps between", () => {
    expect(pageWindow(6, 12)).toEqual([1, null, 5, 6, 7, null, 12]);
    expect(pageWindow(1, 12)).toEqual([1, 2, null, 12]);
  });
});

describe("DataPagination", () => {
  it("says which rows are shown and moves between pages", () => {
    const onPageChange = vi.fn();
    render(
      <DataPagination
        page={2}
        pageSize={20}
        total={68}
        onPageChange={onPageChange}
      />,
    );

    expect(screen.getByText("Hiển thị 21–40 trên 68")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Trang sau" }));
    expect(onPageChange).toHaveBeenCalledWith(3);
    expect(screen.getByRole("button", { name: "Trang 2" })).toHaveAttribute(
      "aria-current",
      "page",
    );
  });

  it("disables both arrows on a single empty page", () => {
    render(
      <DataPagination
        page={1}
        pageSize={20}
        total={0}
        onPageChange={vi.fn()}
      />,
    );

    expect(screen.getByText("Hiển thị 0–0 trên 0")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Trang trước" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Trang sau" })).toBeDisabled();
  });
});

describe("useClientPagination", () => {
  const items = Array.from({ length: 45 }, (_, i) => i + 1);

  it("slices the current page", () => {
    const { result } = renderHook(() => useClientPagination(items, "", 20));

    act(() => result.current.setPage(3));

    expect(result.current.pageItems).toEqual([41, 42, 43, 44, 45]);
  });

  it("goes back to page 1 when the filters change", () => {
    const { result, rerender } = renderHook(
      ({ key }) => useClientPagination(items, key, 20),
      { initialProps: { key: "a" } },
    );
    act(() => result.current.setPage(3));

    rerender({ key: "b" });

    expect(result.current.page).toBe(1);
  });

  it("clamps to the last page when the list shrinks", () => {
    const { result, rerender } = renderHook(
      ({ list }) => useClientPagination(list, "", 20),
      { initialProps: { list: items } },
    );
    act(() => result.current.setPage(3));

    rerender({ list: items.slice(0, 25) });

    expect(result.current.page).toBe(2);
  });
});
