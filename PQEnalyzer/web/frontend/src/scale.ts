/**
 * Pure scale math for the series chart: pinch-zoom ranges and soft
 * (expand-only, Grafana-style) y bounds. No DOM, no uPlot.
 */

export interface TimeRange {
  t0: number;
  t1: number;
}

/**
 * Zoom a time range around an anchor: ratio = startDistance / currentDistance
 * (> 1 with fingers apart zooms out, < 1 zooms in). The anchor keeps its
 * fractional position so the point under the fingers stays put.
 */
export function pinchRange(
  start: TimeRange,
  center: number,
  ratio: number,
): TimeRange {
  const span = start.t1 - start.t0;
  if (!(span > 0) || !Number.isFinite(ratio) || ratio <= 0) return start;
  const clamped = Math.min(Math.max(ratio, 1 / 64), 64);
  const newSpan = span * clamped;
  const fraction = (center - start.t0) / span;
  return {
    t0: center - newSpan * fraction,
    t1: center + newSpan * (1 - fraction),
  };
}

/**
 * Expand an axis range to include soft bounds. Unparseable or empty
 * inputs mean "auto" and never shrink the data range.
 */
export function applySoftBounds(
  range: [number, number],
  minRaw: string,
  maxRaw: string,
): [number, number] {
  let [v0, v1] = range;
  const softMin = Number.parseFloat(minRaw);
  const softMax = Number.parseFloat(maxRaw);
  if (Number.isFinite(softMin)) v0 = Math.min(v0, softMin);
  if (Number.isFinite(softMax)) v1 = Math.max(v1, softMax);
  if (!(v1 > v0)) return range;
  return [v0, v1];
}
