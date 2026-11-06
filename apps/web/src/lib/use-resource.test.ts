import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api-client";
import { useResource } from "@/lib/use-resource";

describe("useResource", () => {
  it("starts loading and then exposes the data", async () => {
    const fetcher = vi.fn().mockResolvedValue([1, 2]);
    const { result } = renderHook(() => useResource(fetcher));

    expect(result.current.status).toBe("loading");
    await waitFor(() => expect(result.current.status).toBe("ready"));
    expect(result.current).toMatchObject({ data: [1, 2] });
  });

  it("surfaces the API's own message on failure", async () => {
    const fetcher = vi
      .fn()
      .mockRejectedValue(new ApiError(403, "FORBIDDEN", "Không có quyền."));
    const { result } = renderHook(() => useResource(fetcher));

    await waitFor(() => expect(result.current.status).toBe("error"));
    expect(result.current).toMatchObject({ message: "Không có quyền." });
  });

  it("hides non-API errors behind a generic Vietnamese message", async () => {
    const fetcher = vi.fn().mockRejectedValue(new TypeError("fetch failed"));
    const { result } = renderHook(() => useResource(fetcher));

    await waitFor(() => expect(result.current.status).toBe("error"));
    expect(result.current).toMatchObject({
      message: expect.stringContaining("Không tải được dữ liệu"),
    });
  });

  it("fetches again on reload", async () => {
    const fetcher = vi
      .fn()
      .mockRejectedValueOnce(new TypeError("offline"))
      .mockResolvedValueOnce("ok");
    const { result } = renderHook(() => useResource(fetcher));
    await waitFor(() => expect(result.current.status).toBe("error"));

    act(() => result.current.reload());

    await waitFor(() => expect(result.current.status).toBe("ready"));
    expect(fetcher).toHaveBeenCalledTimes(2);
  });

  it("refreshes in the background without leaving the ready state", async () => {
    let resolveSecond: (value: string) => void = () => {};
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce("first")
      .mockImplementationOnce(
        () =>
          new Promise<string>((resolve) => {
            resolveSecond = resolve;
          }),
      );
    const { result } = renderHook(() => useResource(fetcher));
    await waitFor(() => expect(result.current.status).toBe("ready"));

    act(() => result.current.refresh());

    expect(result.current).toMatchObject({ status: "ready", data: "first" });
    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(2));
    act(() => resolveSecond("second"));
    await waitFor(() =>
      expect(result.current).toMatchObject({ data: "second" }),
    );
  });

  it("keeps the data on screen when a background refresh fails", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce("first")
      .mockRejectedValueOnce(new TypeError("offline"));
    const { result } = renderHook(() => useResource(fetcher));
    await waitFor(() => expect(result.current.status).toBe("ready"));

    act(() => result.current.refresh());

    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(2));
    await act(async () => {});
    expect(result.current).toMatchObject({ status: "ready", data: "first" });
  });
});
