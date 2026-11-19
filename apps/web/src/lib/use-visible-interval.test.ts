import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useVisibleInterval } from "./use-visible-interval";

function setVisibility(state: "visible" | "hidden") {
  Object.defineProperty(document, "visibilityState", {
    configurable: true,
    get: () => state,
  });
}

function fireVisibilityChange() {
  act(() => {
    document.dispatchEvent(new Event("visibilitychange"));
  });
}

describe("useVisibleInterval", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    setVisibility("visible");
  });
  afterEach(() => {
    vi.useRealTimers();
    setVisibility("visible");
  });

  it("calls back every interval while the tab is visible", () => {
    const callback = vi.fn();
    renderHook(() => useVisibleInterval(callback, 5000));
    vi.advanceTimersByTime(4999);
    expect(callback).not.toHaveBeenCalled();
    vi.advanceTimersByTime(1);
    expect(callback).toHaveBeenCalledTimes(1);
    vi.advanceTimersByTime(5000);
    expect(callback).toHaveBeenCalledTimes(2);
  });

  it("does not call back while the tab is hidden", () => {
    const callback = vi.fn();
    renderHook(() => useVisibleInterval(callback, 5000));
    setVisibility("hidden");
    vi.advanceTimersByTime(20000);
    expect(callback).not.toHaveBeenCalled();
  });

  it("calls back once when the tab becomes visible again", () => {
    const callback = vi.fn();
    renderHook(() => useVisibleInterval(callback, 5000));
    setVisibility("hidden");
    fireVisibilityChange();
    expect(callback).not.toHaveBeenCalled();
    setVisibility("visible");
    fireVisibilityChange();
    expect(callback).toHaveBeenCalledTimes(1);
  });

  it("stops after unmount", () => {
    const callback = vi.fn();
    const { unmount } = renderHook(() => useVisibleInterval(callback, 5000));
    unmount();
    vi.advanceTimersByTime(20000);
    document.dispatchEvent(new Event("visibilitychange"));
    expect(callback).not.toHaveBeenCalled();
  });

  it("does nothing when disabled and always uses the latest callback", () => {
    const first = vi.fn();
    const second = vi.fn();
    const { rerender } = renderHook(
      ({ cb, on }) => useVisibleInterval(cb, 5000, on),
      { initialProps: { cb: first, on: false } },
    );
    vi.advanceTimersByTime(10000);
    expect(first).not.toHaveBeenCalled();
    rerender({ cb: first, on: true });
    rerender({ cb: second, on: true });
    vi.advanceTimersByTime(5000);
    expect(first).not.toHaveBeenCalled();
    expect(second).toHaveBeenCalledTimes(1);
  });
});
