import { describe, expect, it } from "vitest";
import { formatSigma, formatTick, formatUnit, formatValue } from "./api";

describe("formatValue", () => {
  it("formats compactly without hiding scale", () => {
    expect(formatValue(null)).toBe("n/a");
    expect(formatValue(Number.NaN)).toBe("n/a");
    expect(formatValue(310.74)).toBe("310.74");
    expect(formatValue(0.000012)).toBe("1.20e-5");
    expect(formatValue(186045.84503)).toBe("1.86e+5");
  });
});

describe("formatTick", () => {
  it("keeps axis labels short", () => {
    expect(formatTick(9999)).toBe("9999");
    expect(formatTick(0.000012)).toBe("1.2e-5");
  });
});

describe("formatSigma", () => {
  it("signs drift in sigma units", () => {
    expect(formatSigma(null)).toBe("—");
    expect(formatSigma(1.234)).toBe("+1.2σ");
    expect(formatSigma(-0.567)).toBe("−0.57σ");
  });
});

describe("formatUnit", () => {
  it("renders physics units properly", () => {
    expect(formatUnit("A^3")).toBe("Å³");
    expect(formatUnit("g/cm^3")).toBe("g/cm³");
    expect(formatUnit("amuA/fs")).toBe("amu·Å/fs");
    expect(formatUnit("kcal/mol")).toBe("kcal/mol");
    expect(formatUnit("-")).toBe("");
    expect(formatUnit("")).toBe("");
    expect(formatUnit(null)).toBe("");
  });
});
