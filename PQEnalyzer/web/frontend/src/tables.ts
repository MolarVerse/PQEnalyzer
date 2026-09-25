import type { HistogramResponse, SeriesResponse } from "./api";

/**
 * Pure builders for the data-table modal (transported, i.e. downsampled,
 * points — the same values the charts draw). Full resolution stays in the
 * CSV export; tables are capped so the dialog stays usable.
 */
export const DATA_TABLE_ROW_CAP = 2000;

export interface SeriesTableData {
  timeUnit: string;
  files: { label: string; rows: number; stride: number; downsampled: boolean }[];
  /** Transported points (longest file); shown rows are capped. */
  totalPoints: number;
  shown: number;
  truncated: boolean;
  /**
   * One row per transported index; per file a [time, value] pair (null when
   * the file has no point there — strides may differ between files).
   */
  body: (number | null)[][][];
}

export function seriesTable(series: SeriesResponse): SeriesTableData {
  const totalPoints = series.series.reduce(
    (longest, item) => Math.max(longest, item.time.length),
    0,
  );
  const shown = Math.min(totalPoints, DATA_TABLE_ROW_CAP);
  const body: (number | null)[][][] = [];
  for (let i = 0; i < shown; i += 1) {
    body.push(
      series.series.map((item) => [item.time[i] ?? null, item.values[i] ?? null]),
    );
  }
  return {
    timeUnit: series.time_unit,
    files: series.series.map((item) => ({
      label: item.label,
      rows: item.rows,
      stride: item.stride,
      downsampled: item.downsampled,
    })),
    totalPoints,
    shown,
    truncated: totalPoints > shown,
    body,
  };
}

export interface AlignedSeries {
  /** Union of finite times across datasets, ascending. */
  x: number[];
  /** One column per dataset, aligned to x (null = no point there). */
  columns: (number | null)[][];
}

/**
 * Align heterogeneous time grids onto one union x axis for canvas plotting.
 * Exact (no resampling): each dataset keeps its own values, nulls elsewhere
 * render as honest gaps. First value wins on duplicate times.
 */
export function alignSeries(
  datasets: { time: (number | null)[]; values: (number | null)[] }[],
): AlignedSeries {
  const perDataset = datasets.map((dataset) => {
    const map = new Map<number, number | null>();
    const count = Math.min(dataset.time.length, dataset.values.length);
    for (let i = 0; i < count; i += 1) {
      const t = dataset.time[i];
      if (typeof t !== "number" || !Number.isFinite(t)) continue;
      if (!map.has(t)) map.set(t, dataset.values[i] ?? null);
    }
    return map;
  });
  const x = [...new Set(perDataset.flatMap((map) => [...map.keys()]))].sort(
    (a, b) => a - b,
  );
  const columns = perDataset.map((map) =>
    x.map((t) => {
      const v = map.get(t);
      return typeof v === "number" && Number.isFinite(v) ? v : null;
    }),
  );
  return { x, columns };
}

export interface HistogramTableData {
  files: { label: string; rows: number }[];
  bins: { lower: number; upper: number; counts: number[] }[];
}

export function histogramTable(histogram: HistogramResponse): HistogramTableData {
  const bins = histogram.edges.slice(0, -1).map((lower, index) => ({
    lower,
    upper: histogram.edges[index + 1],
    counts: histogram.series.map((item) => item.counts[index] ?? 0),
  }));
  return {
    files: histogram.series.map((item) => ({ label: item.label, rows: item.rows })),
    bins,
  };
}
