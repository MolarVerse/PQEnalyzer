/*
 * uPlot time chart for PQEnalyzer Web (LOCAL-ONLY preview).
 * uPlot draws lines, axes, grid, and the brush selection on canvas; React
 * owns everything annotation-like (legend, tooltip, dots, MSER marker,
 * presets) so the flat-mono language stays in one place. Nulls stay gaps
 * (spanGaps off); heterogeneous file grids are union-aligned, never
 * resampled.
 */

import {
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
  type Ref,
  type TouchEvent,
} from "react";
import uPlot, { type AlignedData } from "uplot";
import "uplot/dist/uPlot.min.css";
import { formatTick, formatValue } from "../api";
import { applySoftBounds, pinchRange, type TimeRange } from "../scale";
import { alignSeries } from "../tables";
import type { LineDataset } from "../charts";

const MONO_FONT = '11px "IBM Plex Mono", "JetBrains Mono", ui-monospace, monospace';
const GRID = "#e0e0e0";
const TICK_INK = "#393939";

/** Hex #rrggbb with an alpha channel (raw series recede under overlays). */
function withAlpha(hex: string, alpha: number): string {
  const match = /^#([0-9a-f]{6})$/i.exec(hex);
  if (!match) return hex;
  const int = parseInt(match[1], 16);
  return `rgba(${(int >> 16) & 255},${(int >> 8) & 255},${int & 255},${alpha})`;
}

export interface UPlotChartHandle {
  /** PNG data URL of the plot canvas (axes included, HTML overlays not). */
  exportPNG: () => string | null;
}

export interface UPlotChartProps {
  datasets: LineDataset[];
  hidden: Set<string>;
  timeLabel: string;
  height?: number;
  /** Provenance line for the footer, e.g. "5,000 pts · stride 2". */
  caption?: string;
  /** Vertical event markers (e.g. the MSER equilibration point). */
  markers?: { value: number; label: string }[];
  /** Hide the preset footer (split panels share one instead). */
  hideFooter?: boolean;
  /** Controlled zoom (split compare keeps panels in lockstep). */
  zoom?: TimeRange | null;
  onZoomChange?: (zoom: TimeRange | null) => void;
  /** Expand-only y bounds from the tools panel ("auto" when blank). */
  softBounds?: { min: string; max: string };
  ref?: Ref<UPlotChartHandle>;
}

/** Grafana-style quick ranges anchored on the longest given series. */
export function presetRangeFor(
  datasets: LineDataset[],
  points: number,
): TimeRange | null {
  const longest = datasets.reduce<LineDataset | null>(
    (best, dataset) =>
      !best || dataset.time.length > best.time.length ? dataset : best,
    null,
  );
  if (!longest) return null;
  const finite = longest.time.filter(
    (t): t is number => typeof t === "number",
  );
  if (finite.length < 2) return null;
  const end = finite[finite.length - 1];
  const start = finite[Math.max(0, finite.length - points)];
  return start < end ? { t0: start, t1: end } : null;
}

export function UPlotChart({
  datasets,
  hidden,
  timeLabel,
  height = 380,
  caption,
  markers = [],
  hideFooter = false,
  zoom: controlledZoom,
  onZoomChange,
  softBounds,
  ref,
}: UPlotChartProps) {
  const [wrapEl, setWrapEl] = useState<HTMLDivElement | null>(null);
  const [mountEl, setMountEl] = useState<HTMLDivElement | null>(null);
  const [size, setSize] = useState({ w: 760, h: height });
  const [plot, setPlot] = useState<uPlot | null>(null);
  const [innerZoom, setInnerZoom] = useState<TimeRange | null>(null);
  const [cursorIdx, setCursorIdx] = useState<number | null>(null);
  const [selecting, setSelecting] = useState(false);
  const pinchRef = useRef<{
    startDist: number;
    center: number;
    range: TimeRange;
  } | null>(null);

  const controlled = controlledZoom !== undefined;
  const zoom = controlled ? controlledZoom : innerZoom;
  const setZoom = (next: TimeRange | null) => {
    if (controlled) onZoomChange?.(next);
    else setInnerZoom(next);
  };

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

  const visible = useMemo(
    () => datasets.filter((dataset) => !hidden.has(dataset.key)),
    [datasets, hidden],
  );

  // Focus mode (TensorBoard-style): when derived overlays are on screen,
  // raw series recede so the derived lines lead. Endpoints stay bright.
  const dimmed = useMemo(
    () => visible.some((dataset) => dataset.key.startsWith("overlay-")),
    [visible],
  );

  const aligned = useMemo(
    () => alignSeries(datasets.map((d) => ({ time: d.time, values: d.values }))),
    [datasets],
  );

  // A new parameter resets the zoom; y always spans the full data so
  // zoomed views stay comparable with the unzoomed one.
  useEffect(() => {
    setZoom(null);
    setCursorIdx(null);
  }, [datasets]);

  const yRange = useMemo(() => {
    let v0 = Infinity;
    let v1 = -Infinity;
    visible.forEach((dataset) => {
      const count = Math.min(dataset.time.length, dataset.values.length);
      for (let i = 0; i < count; i += 1) {
        const v = dataset.values[i];
        if (typeof v !== "number" || !Number.isFinite(v)) continue;
        if (v < v0) v0 = v;
        if (v > v1) v1 = v;
      }
    });
    if (!Number.isFinite(v0)) return null;
    let range: [number, number];
    if (v0 === v1) {
      const pad = Math.abs(v0) * 0.05 || 0.5;
      range = [v0 - pad, v1 + pad];
    } else {
      const pad = (v1 - v0) * 0.06;
      range = [v0 - pad, v1 + pad];
    }
    // Soft bounds widen only (memoized on the raw strings so the range
    // identity — and with it the uPlot instance — stays stable).
    if (softBounds) return applySoftBounds(range, softBounds.min, softBounds.max);
    return range;
  }, [visible, softBounds?.min, softBounds?.max]);

  const xFull: [number, number] | null = useMemo(
    () =>
      aligned.x.length > 1
        ? [aligned.x[0], aligned.x[aligned.x.length - 1]]
        : aligned.x.length === 1
          ? [aligned.x[0] - 0.5, aligned.x[0] + 0.5]
          : null,
    [aligned],
  );

  const data = useMemo(
    () => [aligned.x, ...aligned.columns] as AlignedData,
    [aligned],
  );

  useImperativeHandle(
    ref,
    () => ({
      exportPNG: () => {
        const canvas = mountEl?.querySelector("canvas");
        if (!canvas) return null;
        try {
          return canvas.toDataURL("image/png");
        } catch {
          return null;
        }
      },
    }),
    [mountEl],
  );

  useEffect(() => {
    if (!mountEl || !xFull || !yRange || size.w <= 0) return;
    // Creation always starts at the full range; the zoom effect below
    // applies the React zoom state right after (datasets change = rebuild).
    const opts: uPlot.Options = {
      width: size.w,
      height: size.h,
      legend: { show: false },
      cursor: {
        show: true,
        x: true,
        y: false,
        drag: { setScale: false, x: true, y: false },
        points: { show: false },
      },
      select: { show: true, left: 0, top: 0, width: 0, height: 0 },
      scales: {
        // Function range (not a static array): uPlot re-invokes range()
        // on every setScale, and a static array would snap zooms back to
        // the creation domain. Nulls fall back to the full domain.
        x: {
          time: false,
          range: (_u, min, max) => [min ?? xFull[0], max ?? xFull[1]],
        },
        y: { range: [yRange[0], yRange[1]] },
      },
      axes: [
        {
          stroke: TICK_INK,
          grid: { show: false },
          ticks: { show: true, size: 5, width: 1, stroke: "#8d8d8d" },
          font: MONO_FONT,
          values: (_u, vals) => vals.map((v) => formatTick(v)),
          label: timeLabel,
          labelSize: 14,
          labelFont: MONO_FONT,
        },
        {
          stroke: TICK_INK,
          grid: { show: true, stroke: GRID, width: 1 },
          ticks: { show: true, size: 5, width: 1, stroke: "#8d8d8d" },
          font: MONO_FONT,
          size: 58,
          values: (_u, vals) => vals.map((v) => formatTick(v)),
        },
      ],
      series: [
        {},
        ...datasets.map((dataset) => {
          const isOverlay = dataset.key.startsWith("overlay-");
          // Level references (mean/median) arrive as two endpoints, like
          // the GUI draws them with a single ax.plot call: bridge the
          // aligned nulls so they render as continuous lines. Dense
          // overlays keep honest gaps.
          const isLevel =
            dataset.key === "overlay-mean" ||
            dataset.key === "overlay-median";
          return {
            label: dataset.label,
            stroke:
              dimmed && !isOverlay
                ? withAlpha(dataset.color, 0.35)
                : dataset.color,
            width: dataset.width,
            dash: dataset.dash
              ? dataset.dash.split(" ").map(Number)
              : undefined,
            spanGaps: isLevel,
            points: { show: false },
          };
        }),
      ],
      hooks: {
        setSelect: [
          (u) => {
            const sel = u.select;
            if (Math.abs(sel.width) < 8) return;
            const t0 = u.posToVal(sel.left, "x");
            const t1 = u.posToVal(sel.left + sel.width, "x");
            if (t1 > t0) setZoom({ t0, t1 });
            u.setSelect({ left: 0, top: 0, width: 0, height: 0 }, false);
          },
        ],
        setCursor: [(u) => setCursorIdx(u.cursor.idx ?? null)],
      },
    };
    const next = new uPlot(opts, data, mountEl);
    datasets.forEach((dataset, index) => {
      if (hidden.has(dataset.key)) next.setSeries(index + 1, { show: false });
    });
    setPlot(next);
    return () => {
      setPlot(null);
      next.destroy();
    };
    // datasets identity change = new parameter/refresh: rebuild (the
    // [datasets] effect above has already cleared the zoom state).
  }, [mountEl, size, data, yRange, dimmed, timeLabel, datasets]);

  // Legend toggles ride setSeries (no rebuild, zoom preserved); y follows
  // the visible data like the zoom effect below.
  useEffect(() => {
    if (!plot) return;
    datasets.forEach((dataset, index) => {
      plot.setSeries(index + 1, { show: !hidden.has(dataset.key) });
    });
  }, [plot, datasets, hidden]);

  useEffect(() => {
    if (!plot || !xFull) return;
    const range = zoom ?? { t0: xFull[0], t1: xFull[1] };
    plot.setScale("x", { min: range.t0, max: range.t1 });
  }, [plot, zoom, xFull]);

  useEffect(() => {
    if (!plot || !yRange) return;
    plot.setScale("y", { min: yRange[0], max: yRange[1] });
  }, [plot, yRange]);

  /** Grafana-style quick ranges anchored on the longest visible series. */
  const presetRange = (points: number): TimeRange | null =>
    presetRangeFor(visible, points);

  const isPresetActive = (points: number | null): boolean => {
    if (points === null) return zoom === null;
    if (!zoom) return false;
    const range = presetRange(points);
    return (
      range !== null &&
      Math.abs(range.t0 - Math.min(zoom.t0, zoom.t1)) < 1e-9 &&
      Math.abs(range.t1 - Math.max(zoom.t0, zoom.t1)) < 1e-9
    );
  };

  if (!visible.length) {
    return (
      <div className="chart-empty" style={{ height }}>
        All series hidden — toggle the legend to show them.
      </div>
    );
  }
  if (!xFull || !yRange) {
    return (
      <div className="chart-empty" style={{ height }}>
        No finite values to plot.
      </div>
    );
  }

  const bbox = plot?.bbox;
  const scaleX = plot ? { min: plot.scales.x.min!, max: plot.scales.x.max! } : null;
  const inView = (t: number) =>
    scaleX !== null && t >= scaleX.min && t <= scaleX.max;

  const hoverRows =
    cursorIdx !== null && !selecting && pinchRef.current === null && bbox && plot
      ? datasets
          .map((dataset, index) => {
            if (hidden.has(dataset.key)) return null;
            const value = aligned.columns[index]?.[cursorIdx];
            if (typeof value !== "number") return null;
            return {
              key: dataset.key,
              label: dataset.label,
              color: dataset.color,
              time: aligned.x[cursorIdx],
              value,
            };
          })
          .filter((row) => row !== null)
      : [];

  const hoverX =
    hoverRows.length && bbox && plot
      ? bbox.left + plot.valToPos(hoverRows[0].time, "x")
      : 0;
  const tooltipLeft = Math.min(
    Math.max(hoverX + 12, bbox?.left ?? 0),
    size.w - 230,
  );

  const endpoints = visible
    .filter((dataset) => dataset.endpoint)
    .map((dataset) => {
      const count = Math.min(dataset.time.length, dataset.values.length);
      for (let i = count - 1; i >= 0; i -= 1) {
        const t = dataset.time[i];
        const v = dataset.values[i];
        if (typeof t === "number" && typeof v === "number") {
          return { key: dataset.key, color: dataset.color, t, v };
        }
      }
      return null;
    })
    .filter(
      (point): point is { key: string; color: string; t: number; v: number } =>
        point !== null,
    );

  const onTouchStart = (event: TouchEvent<HTMLDivElement>) => {
    if (event.touches.length !== 2 || !plot) return;
    const first = event.touches[0];
    const second = event.touches[1];
    const rect = event.currentTarget.getBoundingClientRect();
    const centerPx =
      (first.clientX + second.clientX) / 2 - rect.left - plot.bbox.left;
    const scales = plot.scales.x;
    if (scales.min == null || scales.max == null) return;
    pinchRef.current = {
      startDist: Math.hypot(
        first.clientX - second.clientX,
        first.clientY - second.clientY,
      ),
      center: plot.posToVal(centerPx, "x"),
      range: { t0: scales.min, t1: scales.max },
    };
    setCursorIdx(null);
  };

  const onTouchMove = (event: TouchEvent<HTMLDivElement>) => {
    const pinch = pinchRef.current;
    if (!pinch || event.touches.length !== 2) return;
    const first = event.touches[0];
    const second = event.touches[1];
    const dist = Math.hypot(
      first.clientX - second.clientX,
      first.clientY - second.clientY,
    );
    if (dist <= 0) return;
    setZoom(pinchRange(pinch.range, pinch.center, pinch.startDist / dist));
  };

  const onTouchEnd = (event: TouchEvent<HTMLDivElement>) => {
    if (event.touches.length < 2) pinchRef.current = null;
  };

  return (
    <>
      <div
        className="chart-wrap uplot-wrap"
        ref={setWrapEl}
        data-zoom={zoom ? `${zoom.t0.toFixed(0)}-${zoom.t1.toFixed(0)}` : "all"}
        role="img"
        aria-label="Time series chart. Drag to zoom, double-click to reset."
        onMouseDown={(event) => {
          if (event.button === 0) setSelecting(true);
        }}
        onMouseUp={() => setSelecting(false)}
        onMouseLeave={() => {
          setSelecting(false);
          setCursorIdx(null);
        }}
        onDoubleClick={() => setZoom(null)}
        onTouchStart={onTouchStart}
        onTouchMove={onTouchMove}
        onTouchEnd={onTouchEnd}
        onTouchCancel={onTouchEnd}
      >
        {xFull && yRange && (
          <div
            ref={setMountEl}
            className="uplot-mount"
            style={{ width: size.w, height: size.h }}
          />
        )}
        {bbox && plot && (
          <div className="uplot-overlays" aria-hidden="true">
            {markers
              .filter((marker) => inView(marker.value))
              .map((marker, markerIndex) => (
                <div key={`${marker.value}-${markerIndex}`}>
                  <div
                    className="uplot-marker"
                    style={{
                      left: bbox.left + plot.valToPos(marker.value, "x"),
                      top: bbox.top,
                      height: bbox.height,
                    }}
                  />
                  <span
                    className="uplot-marker-label"
                    style={{
                      left: bbox.left + plot.valToPos(marker.value, "x") + 4,
                      top: bbox.top + 12 + (markerIndex % 2) * 14,
                    }}
                  >
                    {marker.label}
                  </span>
                </div>
              ))}
            {endpoints
              .filter((point) => inView(point.t))
              .map((point) => (
                <div
                  key={`end-${point.key}`}
                  className="uplot-dot"
                  style={{
                    left: bbox.left + plot.valToPos(point.t, "x"),
                    top: bbox.top + plot.valToPos(point.v, "y"),
                    background: point.color,
                  }}
                />
              ))}
            {hoverRows.map((row) => (
              <div
                key={row.key}
                className="uplot-dot uplot-hover-dot"
                style={{
                  left: bbox.left + plot.valToPos(row.time, "x"),
                  top: bbox.top + plot.valToPos(row.value, "y"),
                  borderColor: row.color,
                }}
              />
            ))}
            {hoverRows.length > 0 && (
              <div
                className="uplot-vline"
                style={{
                  left: hoverX,
                  top: bbox.top,
                  height: bbox.height,
                }}
              />
            )}
          </div>
        )}
        {hoverRows.length > 0 && (
          <div className="chart-tooltip" style={{ left: tooltipLeft, top: 8 }}>
            <strong>{formatTick(hoverRows[0].time)}</strong>
            <table>
              <tbody>
                {[...hoverRows]
                  .sort((a, b) => b.value - a.value)
                  .map((row) => (
                    <tr key={row.key}>
                      <td>
                        <i style={{ background: row.color }} />
                        {row.label}
                      </td>
                      <td>{formatValue(row.value)}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      {!hideFooter && (
        <div className="chart-foot">
          <span className="chart-presets" role="group" aria-label="Time range">
            {PRESETS.map((preset) => {
              const active = isPresetActive(preset.points);
              return (
                <button
                  key={preset.label}
                  type="button"
                  className={`chart-foot-action${active ? " active" : ""}`}
                  aria-pressed={active}
                  onClick={() => {
                    if (preset.points === null) setZoom(null);
                    else {
                      const range = presetRange(preset.points);
                      if (range) setZoom(range);
                    }
                  }}
                >
                  {preset.label}
                </button>
              );
            })}
          </span>
          {caption && <span>{caption}</span>}
        </div>
      )}
    </>
  );
}

export const PRESETS: { label: string; points: number | null }[] = [
  { label: "All", points: null },
  { label: "Last 5k", points: 5000 },
  { label: "Last 1k", points: 1000 },
];
