import { columnsFor, formatCell } from "@/features/assistant/format-cell";
import type { ChartSpec, ColumnMeta } from "@/types/api";

const LABELS: Record<string, string> = {
  line: "Biểu đồ đường",
  bar: "Biểu đồ cột",
  doughnut: "Biểu đồ tròn",
};

const COLORS = [1, 2, 3, 4, 5, 6].map((i) => `var(--color-chart-${i})`);
const WIDTH = 480;
const HEIGHT = 180;
const PAD = { top: 12, bottom: 24, side: 8 };

function values(rows: Record<string, unknown>[], spec: ChartSpec): number[] {
  return rows.map((row) => {
    const raw = Number(row[spec.y[0]]);
    return Number.isFinite(raw) ? raw : 0;
  });
}

export function ChartView({
  spec,
  rows,
  columns,
}: {
  spec: ChartSpec | null;
  rows: Record<string, unknown>[];
  columns?: ColumnMeta[];
}) {
  if (spec === null || rows.length === 0) {
    return null;
  }

  const meta = columnsFor(rows, columns);
  const kindOf = (key: string) => meta.find((c) => c.key === key)?.kind ?? "text";
  const series = values(rows, spec);
  const peak = Math.max(...series, 1);
  const plotH = HEIGHT - PAD.top - PAD.bottom;
  const plotW = WIDTH - PAD.side * 2;
  const y = (v: number) => PAD.top + plotH * (1 - v / peak);
  // Label the first, middle and last points so the axis never crowds.
  const labelled = new Set([
    0,
    Math.floor((rows.length - 1) / 2),
    rows.length - 1,
  ]);

  if (spec.type === "doughnut") {
    const total = series.reduce((sum, value) => sum + value, 0) || 1;
    const circumference = 2 * Math.PI * 52;
    const starts = series.map(
      (_, index) =>
        series.slice(0, index).reduce((sum, v) => sum + v, 0) / total,
    );
    return (
      <div className="flex flex-wrap items-center gap-6">
        <svg
          role="img"
          aria-label={LABELS.doughnut}
          viewBox="0 0 140 140"
          className="size-36 shrink-0"
        >
          {series.map((value, index) => {
            const fraction = value / total;
            return (
              <circle
                key={index}
                cx={70}
                cy={70}
                r={52}
                fill="none"
                strokeWidth={22}
                stroke={COLORS[index % COLORS.length]}
                strokeDasharray={`${fraction * circumference} ${circumference}`}
                strokeDashoffset={-starts[index] * circumference}
                transform="rotate(-90 70 70)"
              />
            );
          })}
        </svg>
        <ul className="space-y-1.5">
          {rows.map((row, index) => (
            <li key={index} className="flex items-center gap-2">
              <span
                aria-hidden
                className="size-2.5 rounded-xs"
                style={{ background: COLORS[index % COLORS.length] }}
              />
              <span>{formatCell(row[spec.x], kindOf(spec.x))}</span>
              <span className="text-muted tabular-nums">
                {formatCell(series[index], kindOf(spec.y[0]))}
              </span>
            </li>
          ))}
        </ul>
      </div>
    );
  }

  const step = series.length > 1 ? plotW / (series.length - 1) : 0;
  const slot = plotW / series.length;
  const xOf = (index: number) =>
    spec.type === "line"
      ? PAD.side + index * step
      : PAD.side + slot * (index + 0.5);

  return (
    <svg
      role="img"
      aria-label={LABELS[spec.type] ?? "Biểu đồ"}
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      className="h-auto w-full max-w-2xl"
    >
      <line
        x1={PAD.side}
        x2={WIDTH - PAD.side}
        y1={y(0)}
        y2={y(0)}
        stroke="var(--color-border-strong)"
      />
      <line
        x1={PAD.side}
        x2={WIDTH - PAD.side}
        y1={y(peak)}
        y2={y(peak)}
        stroke="var(--color-border)"
        strokeDasharray="3 4"
      />

      {spec.type === "line" && (
        <>
          <polygon
            fill="var(--color-chart-1)"
            fillOpacity={0.1}
            points={[
              `${xOf(0)},${y(0)}`,
              ...series.map((value, index) => `${xOf(index)},${y(value)}`),
              `${xOf(series.length - 1)},${y(0)}`,
            ].join(" ")}
          />
          <polyline
            fill="none"
            stroke="var(--color-chart-1)"
            strokeWidth={2}
            strokeLinejoin="round"
            points={series
              .map((value, index) => `${xOf(index)},${y(value)}`)
              .join(" ")}
          />
          {series.map((value, index) => (
            <circle
              key={index}
              cx={xOf(index)}
              cy={y(value)}
              r={6}
              fill="transparent"
            >
              <title>{`${formatCell(rows[index][spec.x], kindOf(spec.x))}: ${formatCell(value, kindOf(spec.y[0]))}`}</title>
            </circle>
          ))}
        </>
      )}

      {spec.type === "bar" &&
        series.map((value, index) => {
          const width = Math.min(slot * 0.64, 36);
          return (
            <rect
              key={index}
              x={xOf(index) - width / 2}
              y={y(value)}
              width={width}
              height={Math.max(y(0) - y(value), 1)}
              rx={2}
              fill="var(--color-chart-1)"
            >
              <title>{`${formatCell(rows[index][spec.x], kindOf(spec.x))}: ${formatCell(value, kindOf(spec.y[0]))}`}</title>
            </rect>
          );
        })}

      {rows.map((row, index) =>
        labelled.has(index) ? (
          <text
            key={index}
            x={xOf(index)}
            y={HEIGHT - 6}
            fontSize={11}
            fill="var(--color-subtle)"
            textAnchor={
              spec.type === "line" && index === 0
                ? "start"
                : spec.type === "line" && index === rows.length - 1
                  ? "end"
                  : "middle"
            }
          >
            {formatCell(row[spec.x], kindOf(spec.x))}
          </text>
        ) : null,
      )}
    </svg>
  );
}
