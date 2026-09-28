import { describe, expect, it } from "vitest";
import { NO_OVERLAYS, toggleOverlay } from "./RailBlocks";

describe("analysis choices", () => {
  it("keeps difference exclusive and restores ordinary choices on the next selection", () => {
    const trend = toggleOverlay(NO_OVERLAYS, "running_average");
    expect(trend.running_average).toBe(true);

    const difference = toggleOverlay(trend, "difference");
    expect(difference).toEqual({ ...NO_OVERLAYS, difference: true });

    const reference = toggleOverlay(difference, "mean");
    expect(reference).toEqual({ ...NO_OVERLAYS, mean: true });
  });
});
