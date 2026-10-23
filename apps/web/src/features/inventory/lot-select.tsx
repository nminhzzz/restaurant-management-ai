"use client";

import { useCallback, useState } from "react";
import { DataPagination } from "@/components/data-pagination";
import { ErrorState } from "@/components/page-states";
import { apiFetch } from "@/lib/api-client";
import { useResource } from "@/lib/use-resource";
import type { LotRow } from "./inventory-history";

export function LotSelect({
  id,
  ingredientId,
  value,
  onChange,
}: {
  id: string;
  ingredientId: string;
  value: string;
  onChange: (value: string) => void;
}) {
  const [page, setPage] = useState(1);
  const load = useCallback(
    () =>
      ingredientId
        ? apiFetch<{ items: LotRow[]; total: number }>(
            `/inventory/lots?ingredient_id=${encodeURIComponent(ingredientId)}&page=${page}&page_size=20`,
          )
        : Promise.resolve({ items: [], total: 0 }),
    [ingredientId, page],
  );
  const resource = useResource(load);
  const lots = resource.status === "ready" ? (resource.data.items ?? []) : [];
  return (
    <div className="space-y-2">
      <select
        id={id}
        aria-label="Lô nguyên liệu"
        className="h-9 w-full rounded-control border border-border-strong bg-surface px-2"
        disabled={!ingredientId || resource.status === "loading"}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        <option value="">Tự phân bổ FIFO</option>
        {value && !lots.some((lot) => String(lot.MaLoNguyenLieu) === value) && (
          <option value={value}>Lô #{value}</option>
        )}
        {lots
          .filter((lot) => lot.SoLuongConLai > 0)
          .map((lot) => (
            <option key={lot.MaLoNguyenLieu} value={lot.MaLoNguyenLieu}>
              #{lot.MaLoNguyenLieu} · {lot.TrangThai} · còn {lot.SoLuongConLai},
              giữ {lot.SoLuongGiu} · hạn {lot.HanSuDung ?? "không giới hạn"}
            </option>
          ))}
      </select>
      {resource.status === "error" && (
        <ErrorState message={resource.message} onRetry={resource.reload} />
      )}
      {resource.status === "ready" && resource.data.total > 20 && (
        <DataPagination
          page={page}
          pageSize={20}
          total={resource.data.total}
          onPageChange={setPage}
        />
      )}
    </div>
  );
}
