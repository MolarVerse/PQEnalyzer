import { describe, expect, it } from "vitest";
import { inspectIndex } from "./chartNavigation";

describe("keyboard chart inspection", () => {
  const present = [0, 2, 5];

  it("skips missing points and stops at the ends", () => {
    expect(inspectIndex(present, null, "ArrowRight")).toBe(0);
    expect(inspectIndex(present, 0, "ArrowRight")).toBe(2);
    expect(inspectIndex(present, 2, "ArrowRight")).toBe(5);
    expect(inspectIndex(present, 5, "ArrowRight")).toBe(5);
    expect(inspectIndex(present, 5, "ArrowLeft")).toBe(2);
    expect(inspectIndex(present, null, "ArrowLeft")).toBe(5);
  });

  it("supports first and last and an empty chart", () => {
    expect(inspectIndex(present, 2, "Home")).toBe(0);
    expect(inspectIndex(present, 2, "End")).toBe(5);
    expect(inspectIndex([], null, "ArrowRight")).toBeNull();
  });
});
