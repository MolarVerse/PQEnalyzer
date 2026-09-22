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
    time_unit: "ps",
    series: [
      {
        label: "md-01.en",
        rows: 5000,
        stride: 2,
        downsampled: true,
        min: 240,
        max: 360,
        time: [0, 2, 4],
        values: [300, 310, null],
      },
      {
        label: "md-02.en",
        rows: 5000,
        stride: 2,
        downsampled: true,
        min: 250,
        max: 350,
        // Shorter file: missing tail aligns as nulls.
        time: [0, 2],
        values: [295, 305],
      },
    ],
  };
}

describe("seriesTable", () => {
  it("aligns per-file [time, value] pairs with nulls for short files", () => {
    const table = seriesTable(seriesResponse());
    expect(table.totalPoints).toBe(3);
    expect(table.truncated).toBe(false);
    expect(table.body).toEqual([
      [
        [0, 300],
        [0, 295],
      ],
      [
        [2, 310],
        [2, 305],
      ],
      [
        [4, null],
        [null, null],
      ],
    ]);
    expect(table.files).toHaveLength(2);
    expect(table.timeUnit).toBe("ps");
  });

  it("caps long transports and reports truncation", () => {
    const long: SeriesResponse = {
      ...seriesResponse(),
      series: [
        {
          label: "long.en",
          rows: 100000,
          stride: 50,
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
      [10, 30, 50, null, null],
      [null, null, null, 20, 40],
      // First value wins on duplicate times; null times ignored.
      [11, 33, null, null, null],
    ]);
  });

  it("drops non-finite times and values", () => {
    const aligned = alignSeries([
      { time: [NaN, Infinity, 2], values: [1, 2, NaN] },
    ]);
    expect(aligned.x).toEqual([2]);
    expect(aligned.columns).toEqual([[null]]);
  });

  it("handles empty input", () => {
    expect(alignSeries([])).toEqual({ x: [], columns: [] });
  });
});

describe("histogramTable", () => {
  it("maps edges to bins with per-file counts", () => {
    const histogram: HistogramResponse = {
      parameter: "TEMPERATURE",
      unit: "K",
      label: "x",
      edges: [0, 1, 2, 3],
      series: [
        { label: "md-01.en", rows: 100, counts: [10, 70, 20] },
        { label: "md-02.en", rows: 80, counts: [5, 60] },
      ],
      guides: [],
      kde: [],
    };
    const table = histogramTable(histogram);
    expect(table.bins).toEqual([
      { lower: 0, upper: 1, counts: [10, 5] },
      { lower: 1, upper: 2, counts: [70, 60] },
      // Short counts arrays default to zero, never undefined.
      { lower: 2, upper: 3, counts: [20, 0] },
    ]);
  });
});
