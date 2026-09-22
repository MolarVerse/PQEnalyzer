import { describe, expect, it } from "vitest";
import { sortRuns } from "./RunsTable";
import type { StatBlock } from "../api";

function block(label: string, patch: Partial<StatBlock> = {}): StatBlock {
  return {
    label,
    rows: 100,
    latest: null,
    mean: null,
    median: null,
    std: null,
    min: null,
    max: null,
    drift: null,
    ...patch,
  };
}

describe("sortRuns", () => {
  it("sorts labels alphabetically both ways", () => {
    const rows = [block("md-02.en"), block("md-01.en")];
    expect(sortRuns(rows, "label", 1).map((r) => r.label)).toEqual([
      "md-01.en",
      "md-02.en",
    ]);
    expect(sortRuns(rows, "label", -1).map((r) => r.label)).toEqual([
      "md-02.en",
      "md-01.en",
    ]);
  });

  it("sorts numbers numerically with nulls sinking", () => {
    const rows = [
      block("a", { mean: 5 }),
      block("b", { mean: null }),
      block("c", { mean: -2 }),
    ];
    expect(sortRuns(rows, "mean", 1).map((r) => r.label)).toEqual([
      "c",
      "a",
      "b",
    ]);
    expect(sortRuns(rows, "mean", -1).map((r) => r.label)).toEqual([
      "a",
      "c",
      "b",
    ]);
  });

  it("does not mutate the input", () => {
    const rows = [block("b"), block("a")];
    sortRuns(rows, "label", 1);
    expect(rows.map((r) => r.label)).toEqual(["b", "a"]);
  });
});
