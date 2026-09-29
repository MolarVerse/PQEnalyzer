import { describe, expect, it } from "vitest";
import { alignSeries } from "./chartData";

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
