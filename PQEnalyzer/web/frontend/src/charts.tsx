/*
 * Flat-mono SVG charts for PQEnalyzer Web (LOCAL-ONLY preview).
 * Square corners, hairline grid, mono ticks, tabular numerals.
 * Null values break paths into honest gaps instead of bridging them.
 */

import { useEffect, useMemo, useState } from "react";
import { formatTick, formatValue } from "./api";

/** Series hues follow the flat-mono data order (accent first). */
export const SERIES_COLORS = [
  "#0f62fe",
  "#005d5d",
  "#6929c4",
  "#198038",
  "#0043ce",
  "#393939",
  "#8e6a00",
  "#da1e28",
];

export interface OverlayStyle {
  color: string;
  dash?: string;
  width: number;
}

/** Derived overlays read as technical linework, not new data. */
export const OVERLAY_STYLES: Record<string, OverlayStyle> = {
  mean: { color: "#393939", dash: "6 4", width: 1.5 },
  median: { color: "#6929c4", dash: "2 3", width: 1.5 },
  cummulative_average: { color: "#0043ce", dash: "8 4", width: 1.5 },
  self_correlation_mean: { color: "#6f6f6f", dash: "1 3", width: 1.5 },
  // Solid ink: unmistakable against every file hue, including file one's blue.
  running_average: { color: "#161616", width: 2 },
  difference: { color: "#da1e28", width: 2 },
};

export interface LineDataset {
  key: string;
  label: string;
  time: (number | null)[];
  values: (number | null)[];
  color: string;
  dash?: string;
  width: number;
  /** Mark the latest finite point (raw series, not derived overlays). */
  endpoint?: boolean;
}

export function niceTicks(min: number, max: number, count: number): number[] {
  if (!Number.isFinite(min) || !Number.isFinite(max) || min === max) {
    return [min];
  }
  const span = max - min;
  const step0 = span / Math.max(count - 1, 1);
  const magnitude = 10 ** Math.floor(Math.log10(step0));
  const residual = step0 / magnitude;
  const step =
    residual >= 5 ? 5 * magnitude
    : residual >= 2 ? 2 * magnitude
    : magnitude;
  const ticks: number[] = [];
  for (
    let value = Math.ceil(min / step) * step;
    value <= max + step * 1e-9;
    value += step
  ) {
    ticks.push(Number(value.toPrecision(12)));
  }
  return ticks.length ? ticks : [min, max];
}

export function Legend({
  items,
  hidden,
  onToggle,
  values,
}: {
  items: { key: string; label: string; color: string; dash?: string }[];
  hidden: Set<string>;
  onToggle: (key: string) => void;
  /** Latest value per item key (Grafana-style legend values). */
  values?: Map<string, number | null>;
}) {
  if (!items.length) return null;
  // Files first, derived overlays after a divider (datasets arrive ordered).
  const splitAt = items.findIndex((item) => item.key.startsWith("overlay-"));
  return (
    <div className="chart-legend" role="group" aria-label="Series visibility">
      {items.map((item, index) => {
        const off = hidden.has(item.key);
        const value = values?.get(item.key);
        return (
          <span className="legend-item" key={item.key}>
            {index === splitAt && index > 0 && (
              <i className="legend-sep" aria-hidden="true" />
            )}
            <button
              type="button"
              className={`legend-chip${off ? " off" : ""}`}
              aria-pressed={!off}
              onClick={() => onToggle(item.key)}
              title={off ? `Show ${item.label}` : `Hide ${item.label}`}
            >
              <svg width="26" height="8" aria-hidden="true">
                <line
                  x1="0"
                  y1="4"
                  x2="26"
                  y2="4"
                  stroke={item.color}
                  strokeWidth="2"
                  strokeDasharray={item.dash}
                />
              </svg>
              <span>{item.label}</span>
              {value !== undefined && (
                <strong>{value === null ? "n/a" : formatValue(value)}</strong>
              )}
            </button>
          </span>
        );
      })}
    </div>
  );
}

const MARGIN = { left: 58, right: 14, top: 12, bottom: 44 };

export interface MiniGuide {
  value: number;
  color: string;
  dashed?: boolean;
}

/** Map a value onto mini-histogram pixels (clamped inside the frame). */
export function guideX(value: number, edges: number[], width: number): number {
  const lo = edges[0];
  const hi = edges[edges.length - 1];
  if (!Number.isFinite(value) || !(hi > lo)) return 0;
  const frac = (value - lo) / (hi - lo);
  return Math.min(Math.max(frac * width, 1), width - 1);
}

export function MiniHist({
  edges,
  counts,
  color,
  guides = [],
  width = 132,
  height = 34,
}: {
  edges: number[];
  counts: number[];
  color: string;
  guides?: MiniGuide[];
  width?: number;
  height?: number;
}) {
  const bins = edges.length - 1;
  const maxCount = Math.max(1, ...counts);
  const stepX = width / Math.max(bins, 1);
  const bars = [];
  for (let bin = 0; bin < bins; bin += 1) {
    const count = counts[bin] ?? 0;
    if (count <= 0) continue;
    const barH = Math.max(1, (count / maxCount) * (height - 2));
    bars.push(
      <rect
        key={bin}
        x={bin * stepX + 0.5}
        y={height - 1 - barH}
        width={Math.max(stepX - 1, 1)}
        height={barH}
        fill={color}
        fillOpacity={0.75}
      />,
    );
  }
  if (!bars.length) return null;
  return (
    <svg width={width} height={height} aria-hidden="true">
      {bars}
      {guides.map((guide, index) => (
        <line
          key={index}
          x1={guideX(guide.value, edges, width)}
          y1={1}
          x2={guideX(guide.value, edges, width)}
          y2={height - 1}
          stroke={guide.color}
          strokeWidth="1"
          strokeDasharray={guide.dashed ? "2 2" : undefined}
        />
      ))}
    </svg>
  );
}

export function Sparkline({  values,
  color,
  width = 132,
  height = 34,
}: {
  values: (number | null)[];
  color: string;
  width?: number;
  height?: number;
}) {
  const points = useMemo(() => {
    const finite = values.filter(
      (value): value is number => typeof value === "number",
    );
    if (finite.length < 2) return null;
    const min = Math.min(...finite);
    const max = Math.max(...finite);
    const span = max - min || 1;
    return values
      .map((value, index) => {
        if (typeof value !== "number") return null;
        const px = (index / (values.length - 1)) * (width - 4) + 2;
        const py = height - 3 - ((value - min) / span) * (height - 6);
        return `${px.toFixed(1)},${py.toFixed(1)}`;
      })
      .filter((point): point is string => point !== null)
      .join(" ");
  }, [values, width, height]);

  if (!points) {
    return (
      <svg width={width} height={height} aria-hidden="true">
        <line
          x1="2"
          y1={height / 2}
          x2={width - 2}
          y2={height / 2}
          stroke="#8d8d8d"
          strokeWidth="1"
          strokeDasharray="3 4"
        />
      </svg>
    );
  }
  const last = points.split(" ").at(-1)!.split(",");
  return (
    <svg width={width} height={height} aria-hidden="true">
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" />
      <circle cx={Number(last[0])} cy={Number(last[1])} r="2.5" fill={color} />
    </svg>
  );
}

export function HistogramChart({
  edges,
  series,
  guides,
  kde,
  fileColors,
  height = 380,
}: {
  edges: number[];
  series: { label: string; rows: number; counts: number[] }[];
  guides: { label: string; value: number }[];
  kde: { label: string; x: number[]; y: number[] }[];
  fileColors: string[];
  height?: number;
}) {
  const [wrapEl, setWrapEl] = useState<HTMLDivElement | null>(null);
  const [size, setSize] = useState({ w: 760, h: height });

  useEffect(() => {
    if (!wrapEl) return;
    const measure = () => {
      setSize({
        w: Math.max(280, Math.round(wrapEl.clientWidth)),
        h: Math.max(220, Math.round(wrapEl.clientHeight)),
      });
    };
    const observer = new ResizeObserver(() => measure());
    observer.observe(wrapEl);
    measure();
    window.addEventListener("resize", measure);
    return () => {
      observer.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, [wrapEl]);

  const bins = edges.length - 1;
  const maxCount = Math.max(
    1,
    ...series.flatMap((item) => item.counts),
  );
  const plotW = Math.max(size.w - MARGIN.left - MARGIN.right, 100);
  const plotH = Math.max(size.h - MARGIN.top - MARGIN.bottom, 100);
  const x = (edge: number) =>
    MARGIN.left + ((edge - edges[0]) / (edges[bins] - edges[0] || 1)) * plotW;
  const y = (count: number) =>
    MARGIN.top + (1 - count / (maxCount * 1.08)) * plotH;
  const binW = plotW / Math.max(bins, 1);
  const yTicks = niceTicks(0, maxCount, 4);
  const xTicks = niceTicks(edges[0], edges[bins], 6).filter(
    (tick) =>
      MARGIN.left +
        ((tick - edges[0]) / (edges[bins] - edges[0] || 1)) * plotW <
      MARGIN.left + plotW - 20,
  );

  return (
    <div className="chart-wrap" ref={setWrapEl}>
      <svg width={size.w} height={size.h} role="img" aria-label="Histogram">
        {yTicks.map((tick) => (
          <g key={tick}>
            <line
              x1={MARGIN.left}
              y1={y(tick)}
              x2={MARGIN.left + plotW}
              y2={y(tick)}
              className="chart-grid"
            />
            <text x={MARGIN.left - 8} y={y(tick) + 4} className="chart-tick" textAnchor="end">
              {formatTick(tick)}
            </text>
          </g>
        ))}
        {xTicks.map((tick) => (
          <text
            key={tick}
            x={MARGIN.left + ((tick - edges[0]) / (edges[bins] - edges[0] || 1)) * plotW}
            y={MARGIN.top + plotH + 20}
            className="chart-tick"
            textAnchor="middle"
          >
            {formatTick(tick)}
          </text>
        ))}
        {series.map((item, fileIndex) =>
          item.counts.map((count, bin) =>
            count > 0 ? (
              <rect
                key={`${fileIndex}-${bin}`}
                x={x(edges[bin]) + 0.5}
                y={y(count)}
                width={Math.max(binW - 1, 1)}
                height={MARGIN.top + plotH - y(count)}
                fill={fileColors[fileIndex % fileColors.length]}
                fillOpacity={series.length > 1 ? 0.45 : 0.8}
                stroke={fileColors[fileIndex % fileColors.length]}
                strokeWidth="1"
              />
            ) : null,
          ),
        )}
        {guides.map((guide, guideIndex) => (
          <g key={guide.label}>
            <line
              x1={x(guide.value)}
              y1={MARGIN.top}
              x2={x(guide.value)}
              y2={MARGIN.top + plotH}
              className="chart-guide"
            />
            <text
              x={x(guide.value) + 4}
              y={MARGIN.top + 12 + (guideIndex % 2) * 14}
              className="chart-guide-label"
            >
              {guide.label} {formatValue(guide.value)}
            </text>
          </g>
        ))}
        {kde.map((curve, curveIndex) => (
          <path
            key={curve.label}
            d={kdePath(curve.x, curve.y, x, y)}
            fill="none"
            stroke={fileColors[curveIndex % fileColors.length]}
            strokeWidth="2"
          />
        ))}
      </svg>
    </div>
  );
}

function kdePath(
  xs: number[],
  ys: number[],
  x: (v: number) => number,
  y: (v: number) => number,
): string {
  let path = "";
  const count = Math.min(xs.length, ys.length);
  for (let i = 0; i < count; i += 1) {
    path += `${i === 0 ? "M" : "L"}${x(xs[i]).toFixed(2)},${y(ys[i]).toFixed(2)}`;
  }
  return path;
}
