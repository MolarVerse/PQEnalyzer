export interface AlignedSeries {
  /** Union of finite times across datasets, ascending. */
  x: number[];
  /** One column per dataset, aligned to x (null = no point there). */
  columns: (number | null | undefined)[][];
}

/**
 * Align heterogeneous time grids onto one union x axis for canvas plotting.
 * Exact (no resampling): undefined means a time belongs to another series,
 * while an explicit null is a real missing value in this series. uPlot joins
 * across undefined alignment slots and keeps nulls as visible gaps.
 * First value wins on duplicate times.
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
      if (!map.has(t)) return undefined;
      const v = map.get(t);
      return typeof v === "number" && Number.isFinite(v) ? v : null;
    }),
  );
  return { x, columns };
}
