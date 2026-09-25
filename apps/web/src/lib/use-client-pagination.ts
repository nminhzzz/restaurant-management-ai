"use client";

import { useState } from "react";

/**
 * Page an in-memory list (bounded catalogues, report rows). Pass a `resetKey` that
 * changes with the filters, so a new filter starts again from page 1 without an effect.
 */
export function useClientPagination<T>(
  items: readonly T[],
  resetKey = "",
  initialPageSize = 20,
) {
  const [state, setState] = useState({ page: 1, key: resetKey });
  const [pageSize, setPageSizeState] = useState(initialPageSize);

  const pageCount = Math.max(1, Math.ceil(items.length / pageSize));
  const requested = state.key === resetKey ? state.page : 1;
  const page = Math.min(requested, pageCount);
  const pageItems = items.slice((page - 1) * pageSize, page * pageSize);

  return {
    page,
    pageSize,
    total: items.length,
    pageItems,
    setPage: (next: number) => setState({ page: next, key: resetKey }),
    setPageSize: (next: number) => {
      setPageSizeState(next);
      setState({ page: 1, key: resetKey });
    },
  };
}
