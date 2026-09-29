import { describe, expect, it } from "vitest";
import { NO_OVERLAYS, toggleOverlay } from "./RailBlocks";

describe("analysis choices", () => {
  it("uses autocorrelation as one chart mode", () => {
    const trend = toggleOverlay(NO_OVERLAYS, "running_average");
    const correlation = toggleOverlay(trend, "autocorrelation");
    expect(correlation).toEqual({ ...NO_OVERLAYS, autocorrelation: true });
    expect(toggleOverlay(correlation, "mean")).toEqual({ ...NO_OVERLAYS, mean: true });
    expect(toggleOverlay(correlation, "autocorrelation")).toEqual(NO_OVERLAYS);
  });

  it("allows references and trends together on the combined series", () => {
    const mean = toggleOverlay(NO_OVERLAYS, "mean");
    expect(toggleOverlay(mean, "running_average")).toEqual({
      ...NO_OVERLAYS, mean: true, running_average: true,
    });
  });
});
