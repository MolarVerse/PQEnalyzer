/*
 * Flat-mono SVG charts for PQEnalyzer Web.
 * Square corners, hairline grid, mono ticks, tabular numerals.
 * Null values break paths into honest gaps instead of bridging them.
 */

import { useMemo, useState } from "react";
import { formatTick, formatValue } from "./api";
import { inspectIndex } from "./chartNavigation";
import { useChartSize } from "./hooks/useChartSize";

/**
 * Line hues for combined data and distribution guides.
 */
export const SERIES_COLORS = [
  "#0f62fe",
  "#d12771",
  "#007d79",
  "#ba4e00",
  "#6929c4",
  "#198038",
  "#da1e28",
  "#8e6a00",
];

export interface OverlayStyle {
  color: string;
  dash?: string;
  width: number;
}

/**
 * Derived overlays read as instruments, not data: near-ink strokes wide
 * enough to survive under vivid files. Dash patterns (never hue alone)
 * tell them apart; the data hue stays distinct from these near-blacks.
 */
export const OVERLAY_STYLES: Record<string, OverlayStyle> = {
  mean: { color: "#161616", dash: "6 4", width: 2 },
  median: { color: "#6929c4", dash: "2 3", width: 2 },
  cummulative_average: { color: "#0043ce", dash: "8 4", width: 2 },
  running_average: { color: "#161616", width: 2 },
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
}: {
  items: { key: string; label: string; color: string; dash?: string }[];
  hidden: Set<string>;
  onToggle: (key: string) => void;
}) {
  if (!items.length) return null;
  // Data first, derived overlays after a divider (datasets arrive ordered).
  const splitAt = items.findIndex((item) => item.key.startsWith("overlay-"));
  return (
    <div className="chart-legend" role="group" aria-label="Series visibility">
      {items.map((item, index) => {
        const off = hidden.has(item.key);
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
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" aria-hidden="true">
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
          vectorEffect="non-scaling-stroke"
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
  const paths = useMemo(() => {
    const finite = values.filter(
      (value): value is number => typeof value === "number" && Number.isFinite(value),
    );
    if (finite.length < 2) return null;
    const min = Math.min(...finite);
    const max = Math.max(...finite);
    const span = max - min || 1;
    const segments: string[] = [];
    let current: string[] = [];
    values.forEach((value, index) => {
        if (value === null || !Number.isFinite(value)) {
          if (current.length > 1) segments.push(current.join(" "));
          current = [];
          return;
        }
        const px = (index / (values.length - 1)) * (width - 4) + 2;
        const py = height - 3 - ((value - min) / span) * (height - 6);
        current.push(`${px.toFixed(1)},${py.toFixed(1)}`);
      });
    if (current.length > 1) segments.push(current.join(" "));
    return segments;
  }, [values, width, height]);

  if (!paths) {
    return (
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" aria-hidden="true">
        <line
          x1="2"
          y1={height / 2}
          x2={width - 2}
          y2={height / 2}
          stroke="#8d8d8d"
          strokeWidth="1"
          vectorEffect="non-scaling-stroke"
          strokeDasharray="3 4"
        />
      </svg>
    );
  }
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" aria-hidden="true">
      {paths.map((points, index) => (
        <polyline key={index} points={points} fill="none" stroke={color} strokeWidth="1.5" vectorEffect="non-scaling-stroke" />
      ))}
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
  const { setElement: setWrapEl, size } = useChartSize(height);
  const [hoveredBin, setHoveredBin] = useState<number | null>(null);

  const bins = edges.length - 1;
  const counts = edges.slice(0, -1).map((_, bin) =>
    series.reduce((total, item) => total + (item.counts[bin] ?? 0), 0),
  );
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
  const tickCandidates = niceTicks(edges[0], edges[bins], 6);
  const tickGap = Math.max(
    64,
    ...tickCandidates.map((tick) => formatTick(tick).length * 7 + 12),
  );
  let lastTickX = -Infinity;
  const xTicks = tickCandidates.filter((tick) => {
    const tickX = x(tick);
    if (tickX > MARGIN.left + plotW - tickGap / 2 || tickX - lastTickX < tickGap) {
      return false;
    }
    lastTickX = tickX;
    return true;
  });

  return (
    <div
      className="chart-wrap"
      ref={setWrapEl}
      tabIndex={0}
      role="group"
      aria-label={`Histogram, ${counts.reduce((total, count) => total + count, 0)} samples in ${bins} bins. Use left and right arrow keys to inspect bins.`}
      onKeyDown={(event) => {
        if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
        event.preventDefault();
        setHoveredBin(inspectIndex(edges.slice(0, -1).map((_, index) => index), hoveredBin, event.key));
      }}
    >
      <svg
        width={size.w}
        height={size.h}
        aria-hidden="true"
        onMouseLeave={(event) => {
          if (document.activeElement !== event.currentTarget.parentElement) setHoveredBin(null);
        }}
      >
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
            x={x(tick)}
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
        {edges.slice(0, -1).map((_, bin) => (
          <rect
            key={`hover-${bin}`}
            x={x(edges[bin])}
            y={MARGIN.top}
            width={binW}
            height={plotH}
            fill="transparent"
            aria-hidden="true"
            onMouseEnter={() => setHoveredBin(bin)}
            onClick={() => setHoveredBin(bin)}
          />
        ))}
      </svg>
      {hoveredBin !== null && (
        <div
          className="chart-tooltip"
          aria-hidden="true"
          style={{
            left: Math.min(Math.max(x(edges[hoveredBin]), 8), Math.max(8, size.w - 190)),
            top: 8,
          }}
        >
          <strong>{formatValue(edges[hoveredBin])}–{formatValue(edges[hoveredBin + 1])}</strong>
          <span>{counts[hoveredBin].toLocaleString()} samples</span>
        </div>
      )}
      <span className="visually-hidden" aria-live="polite">
        {hoveredBin === null ? "" : `Bin ${hoveredBin + 1} of ${bins}: ${formatValue(edges[hoveredBin])} to ${formatValue(edges[hoveredBin + 1])}, ${counts[hoveredBin]} samples`}
      </span>
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
