import { describe, expect, it } from "vitest";
import { applySoftBounds, pinchRange } from "./scale";

describe("pinchRange", () => {
  it("zooms in around the anchor when fingers move apart", () => {
    // distance doubles -> span halves, anchor keeps its fraction (1/4).
    const range = pinchRange({ t0: 0, t1: 1000 }, 250, 0.5);
    expect(range.t0).toBeCloseTo(125);
    expect(range.t1).toBeCloseTo(625);
  });

  it("zooms out when fingers move together", () => {
    const range = pinchRange({ t0: 400, t1: 600 }, 500, 2);
    expect(range.t0).toBeCloseTo(300);
    expect(range.t1).toBeCloseTo(700);
  });

  it("rejects degenerate input", () => {
    const start = { t0: 0, t1: 100 };
    expect(pinchRange(start, 50, 0)).toBe(start);
    expect(pinchRange(start, 50, NaN)).toBe(start);
    expect(pinchRange({ t0: 5, t1: 5 }, 5, 2)).toEqual({ t0: 5, t1: 5 });
  });
});

describe("applySoftBounds", () => {
  it("expands the range to include finite bounds", () => {
    expect(applySoftBounds([0, 10], "-5", "20")).toEqual([-5, 20]);
  });

  it("never shrinks the data range", () => {
    expect(applySoftBounds([0, 10], "2", "8")).toEqual([0, 10]);
  });

  it("ignores empty and unparseable inputs", () => {
    expect(applySoftBounds([0, 10], "", "")).toEqual([0, 10]);
    expect(applySoftBounds([0, 10], "auto", "1e")).toEqual([0, 10]);
  });

  it("applies each side independently", () => {
    expect(applySoftBounds([0, 10], "", "20")).toEqual([0, 20]);
    expect(applySoftBounds([0, 10], "-5", "")).toEqual([-5, 10]);
  });
});
