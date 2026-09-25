import type { ChartSpec } from "@/types/api";

const LABELS: Record<string, string> = {
  line: "Biểu đồ đường",
  bar: "Biểu đồ cột",
  doughnut: "Biểu đồ tròn",
};

const COLORS = [
  "#f59e0b",
  "#0ea5e9",
  "#10b981",
  "#8b5cf6",
  "#ef4444",
  "#64748b",
];
const WIDTH = 320;
const HEIGHT = 120;

function values(rows: Record<string, unknown>[], spec: ChartSpec): number[] {
  return rows.map((row) => {
    const raw = Number(row[spec.y[0]]);
    return Number.isFinite(raw) ? raw : 0;
  });
}

export function ChartView({
  spec,
  rows,
}: {
  spec: ChartSpec | null;
  rows: Record<string, unknown>[];
}) {
  if (spec === null || rows.length === 0) {
    return null;
  }

  const series = values(rows, spec);
  const peak = Math.max(...series, 1);
  const step = series.length > 1 ? WIDTH / (series.length - 1) : WIDTH;

  return (
    <svg
      role="img"
      aria-label={LABELS[spec.type] ?? "Biểu đồ"}
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      className="h-40 w-full max-w-xl"
    >
      {spec.type === "line" && (
        <polyline
          fill="none"
          stroke={COLORS[0]}
          strokeWidth={2}
          points={series
            .map(
              (value, index) =>
                `${index * step},${HEIGHT - (value / peak) * (HEIGHT - 10)}`,
            )
            .join(" ")}
        />
      )}

      {spec.type === "bar" &&
        series.map((value, index) => {
          const barWidth = WIDTH / series.length - 4;
          const height = (value / peak) * (HEIGHT - 10);
          return (
            <rect
              key={index}
              x={index * (WIDTH / series.length) + 2}
              y={HEIGHT - height}
              width={barWidth}
              height={Math.max(height, 1)}
              fill={COLORS[0]}
            />
          );
        })}

      {spec.type === "doughnut" &&
        (() => {
          const total = series.reduce((sum, value) => sum + value, 0) || 1;
          const circumference = 2 * Math.PI * 40;
          let consumed = 0;
          return series.map((value, index) => {
            const fraction = value / total;
            const segment = (
              <circle
                key={index}
                cx={WIDTH / 2}
                cy={HEIGHT / 2}
                r={40}
                fill="none"
                strokeWidth={20}
                stroke={COLORS[index % COLORS.length]}
                strokeDasharray={`${fraction * circumference} ${circumference}`}
                strokeDashoffset={-consumed * circumference}
                transform={`rotate(-90 ${WIDTH / 2} ${HEIGHT / 2})`}
              />
            );
            consumed += fraction;
            return segment;
          });
        })()}
    </svg>
  );
}
