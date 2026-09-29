import { describe, expect, it } from "vitest";
import { guideX, niceTicks } from "./charts";

describe("niceTicks", () => {
  // Ticks sit on round steps inside the domain (matplotlib convention);
  // the axis itself already pads past the data.
  it("lays round steps across the domain", () => {
    const ticks = niceTicks(241.17, 360.2, 5);
    expect(ticks.length).toBeGreaterThanOrEqual(2);
    expect(ticks.length).toBeLessThanOrEqual(7);
    for (let i = 1; i < ticks.length; i += 1) {
      expect(ticks[i]).toBeGreaterThan(ticks[i - 1]);
    }
    const step = ticks[1] - ticks[0];
    expect(ticks[0]).toBeLessThanOrEqual(241.17 + step);
    expect(ticks[ticks.length - 1]).toBeGreaterThanOrEqual(360.2 - step);
  });

  it("collapses degenerate domains to a point", () => {
    expect(niceTicks(5, 5, 5)).toEqual([5]);
  });

  it("handles negative domains", () => {
    const ticks = niceTicks(-12955, 11515, 5);
    expect(ticks.length).toBeGreaterThanOrEqual(2);
    const step = ticks[1] - ticks[0];
    expect(ticks[0]).toBeLessThanOrEqual(-12955 + step);
    expect(ticks[ticks.length - 1]).toBeGreaterThanOrEqual(11515 - step);
  });
});

describe("guideX", () => {
  const edges = [0, 10, 20, 30];

  it("maps values linearly onto pixels", () => {
    expect(guideX(0, edges, 120)).toBe(1);
    expect(guideX(15, edges, 120)).toBe(60);
    expect(guideX(30, edges, 120)).toBe(119);
  });

  it("clamps out-of-range values inside the frame", () => {
    expect(guideX(-50, edges, 120)).toBe(1);
    expect(guideX(999, edges, 120)).toBe(119);
  });

  it("parks non-finite values and degenerate edges at zero", () => {
    expect(guideX(NaN, edges, 120)).toBe(0);
    expect(guideX(5, [7, 7], 120)).toBe(0);
  });
});
