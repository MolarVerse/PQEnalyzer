import { describe, expect, it } from "vitest";
import {
  alignSeries,
  DATA_TABLE_ROW_CAP,
  histogramTable,
  seriesTable,
} from "./tables";
import type { HistogramResponse, SeriesResponse } from "./api";

function seriesResponse(): SeriesResponse {
  return {
    parameter: "TEMPERATURE",
    unit: "K",
    label: "x",
    time_label: "Sample",
    time_unit: "",
    source_count: 2,
    series: [
      {
        label: "All data",
        rows: 10000,
        downsampled: true,
        min: 240,
        max: 360,
        time: [1, 2, 3],
        values: [300, 310, null],
      },
    ],
  };
}

describe("seriesTable", () => {
  it("shows combined chart points and the sample axis", () => {
    const table = seriesTable(seriesResponse());
    expect(table.totalPoints).toBe(3);
    expect(table.truncated).toBe(false);
    expect(table.body).toEqual([
      [1, 300],
      [2, 310],
      [3, null],
    ]);
    expect(table.axisLabel).toBe("Sample");
    expect(table.timeUnit).toBe("");
  });

  it("caps long transports and reports truncation", () => {
    const long: SeriesResponse = {
      ...seriesResponse(),
      series: [
        {
          label: "long.en",
          rows: 100000,
          downsampled: true,
          min: 0,
          max: 1,
          time: Array.from({ length: DATA_TABLE_ROW_CAP + 500 }, (_, i) => i),
          values: Array.from({ length: DATA_TABLE_ROW_CAP + 500 }, () => 1),
        },
      ],
    };
    const table = seriesTable(long);
    expect(table.totalPoints).toBe(DATA_TABLE_ROW_CAP + 500);
    expect(table.shown).toBe(DATA_TABLE_ROW_CAP);
    expect(table.truncated).toBe(true);
    expect(table.body).toHaveLength(DATA_TABLE_ROW_CAP);
  });

  it("handles empty series", () => {
    const table = seriesTable({ ...seriesResponse(), series: [] });
    expect(table.totalPoints).toBe(0);
    expect(table.body).toEqual([]);
    expect(table.truncated).toBe(false);
  });
});

describe("alignSeries", () => {
  it("unions heterogeneous time grids with null gaps", () => {
    const aligned = alignSeries([
      { time: [1, 3, 5], values: [10, 30, 50] },
      { time: [5001, 5003], values: [20, 40] },
      { time: [1, null, 3], values: [11, 99, 33] },
    ]);
    expect(aligned.x).toEqual([1, 3, 5, 5001, 5003]);
    expect(aligned.columns).toEqual([
      [10, 30, 50, undefined, undefined],
      [undefined, undefined, undefined, 20, 40],
      // First value wins on duplicate times; null times ignored.
      [11, 33, undefined, undefined, undefined],
    ]);
  });

  it("drops non-finite times and values", () => {
    const aligned = alignSeries([
      { time: [NaN, Infinity, 2], values: [1, 2, NaN] },
    ]);
    expect(aligned.x).toEqual([2]);
    expect(aligned.columns).toEqual([[null]]);
  });

  it("keeps explicit missing values distinct from other series' times", () => {
    const aligned = alignSeries([
      { time: [1, 2, 3], values: [4, null, 6] },
      { time: [1.5, 2.5], values: [7, 8] },
    ]);
    expect(aligned.columns).toEqual([
      [4, undefined, null, undefined, 6],
      [undefined, 7, undefined, 8, undefined],
    ]);
  });

  it("handles empty input", () => {
    expect(alignSeries([])).toEqual({ x: [], columns: [] });
  });
});

describe("histogramTable", () => {
  it("maps edges to bins with combined counts", () => {
    const histogram: HistogramResponse = {
      parameter: "TEMPERATURE",
      unit: "K",
      label: "x",
      edges: [0, 1, 2, 3],
      series: [
        { label: "All data", rows: 180, counts: [15, 130, 35] },
      ],
      guides: [],
      kde: [],
    };
    const table = histogramTable(histogram);
    expect(table.bins).toEqual([
      { lower: 0, upper: 1, counts: [15] },
      { lower: 1, upper: 2, counts: [130] },
      { lower: 2, upper: 3, counts: [35] },
    ]);
  });
});
