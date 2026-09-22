export type Mode = "series" | "histogram";

export const MODE_LABEL: Record<Mode, string> = {
  series: "Series",
  histogram: "Histogram",
};

export const MODES: Mode[] = ["series", "histogram"];
