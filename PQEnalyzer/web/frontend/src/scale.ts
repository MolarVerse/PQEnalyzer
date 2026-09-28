/**
 * Pure scale math for chart pinch zoom. No DOM, no uPlot.
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
