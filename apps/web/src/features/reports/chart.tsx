"use client";

/** Shared hand-drawn SVG bar chart for the reports module (FR-REP-09). */
export type ChartItem = { key: string | number; label: string; value: number };

/** Round the axis up to 1, 2 or 5 × 10ⁿ so gridlines land on readable values. */
export function niceStep(peak: number, lines = 4): number {
  if (peak <= 0) return 1;
  const raw = peak / lines;
  const magnitude = 10 ** Math.floor(Math.log10(raw));
  const normalized = raw / magnitude;
  const factor =
    normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10;
  return factor * magnitude;
}

export function Bars({
  items,
  ariaLabel,
  tickFormat,
  tooltipFormat,
  colorAt,
}: {
  items: ChartItem[];
  ariaLabel: string;
  tickFormat: (value: number) => string;
  tooltipFormat: (item: ChartItem) => string;
  colorAt?: (index: number, isPeak: boolean) => string;
}) {
  const W = 720;
  const H = 240;
  const left = 44;
  const right = 8;
  const top = 12;
  const bottom = 28;
  const values = items.map((item) => item.value);
  const peak = Math.max(...values, 0);
  const step = niceStep(peak);
  const ceiling = Math.max(step * Math.ceil(peak / step), step);
  const ticks = Array.from(
    { length: Math.round(ceiling / step) + 1 },
    (_, i) => i * step,
  );
  const y = (v: number) => top + (H - top - bottom) * (1 - v / ceiling);
  const slot = (W - left - right) / Math.max(items.length, 1);
  const labelEvery = Math.ceil(items.length / 12) || 1;
  const peakIndex = values.indexOf(peak);

  return (
    <svg
      role="img"
      aria-label={ariaLabel}
      viewBox={`0 0 ${W} ${H}`}
      className="h-auto w-full"
    >
      {ticks.map((t) => (
        <g key={t}>
          <line
            x1={left}
            x2={W - right}
            y1={y(t)}
            y2={y(t)}
            stroke="var(--color-border)"
          />
          <text
            x={left - 8}
            y={y(t) + 4}
            textAnchor="end"
            fontSize={11}
            fill="var(--color-subtle)"
          >
            {tickFormat(t)}
          </text>
        </g>
      ))}
      {items.map((item, index) => {
        const value = values[index];
        const width = Math.min(slot * 0.64, 40);
        const x = left + index * slot + (slot - width) / 2;
        const isPeak = index === peakIndex && peak > 0;
        return (
          <g key={String(item.key)}>
            <rect
              x={x}
              y={y(value)}
              width={width}
              height={Math.max(y(0) - y(value), value > 0 ? 1 : 0)}
              rx={3}
              fill={
                colorAt
                  ? colorAt(index, isPeak)
                  : isPeak
                    ? "var(--color-chart-1)"
                    : "var(--color-chart-2)"
              }
            >
              <title>{tooltipFormat(item)}</title>
            </rect>
            {index % labelEvery === 0 && (
              <text
                x={x + width / 2}
                y={H - 8}
                textAnchor="middle"
                fontSize={11}
                fill="var(--color-subtle)"
              >
                {item.label}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
