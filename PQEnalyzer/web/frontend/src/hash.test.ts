import { describe, expect, it } from "vitest";
import { parseHash } from "./hash";

describe("parseHash", () => {
  it("reads mode and focus", () => {
    expect(parseHash("#m=histogram&p=PRESSURE")).toEqual({
      parameter: "PRESSURE",
      mode: "histogram",
    });
  });

  it("treats a bare hash as the dashboard overview", () => {
    expect(parseHash("")).toEqual({ parameter: null, mode: null });
    expect(parseHash("#")).toEqual({ parameter: null, mode: null });
  });

  it("keeps focus without a mode key (never drops parameters)", () => {
    // Regression: an early return once discarded the parameter here,
    // reverting every card click back to the dashboard.
    expect(parseHash("#p=TEMPERATURE")).toEqual({
      parameter: "TEMPERATURE",
      mode: null,
    });
  });

  it("migrates legacy v= links", () => {
    expect(parseHash("#v=histogram&p=X")).toEqual({
      parameter: "X",
      mode: "histogram",
    });
    expect(parseHash("#v=series")).toEqual({
      parameter: null,
      mode: "series",
    });
    expect(parseHash("#v=dashboard")).toEqual({
      parameter: null,
      mode: null,
    });
  });

  it("ignores unknown modes", () => {
    expect(parseHash("#m=pie&p=X")).toEqual({
      parameter: "X",
      mode: null,
    });
  });
});
