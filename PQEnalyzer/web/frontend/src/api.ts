/*
 * Typed client for the PQEnalyzer web API (LOCAL-ONLY preview).
 * All math stays server-side; the browser only renders.
 */

export interface FileStatus {
  label: string;
  path: string;
  rows: number;
  stale: boolean;
}

export interface Meta {
  reader: string;
  time_label: string;
  files: FileStatus[];
  stale: boolean;
}

export interface Parameter {
  name: string;
  unit: string;
  label: string;
  files: number;
  rows: number;
}

export interface SeriesItem {
  label: string;
  rows: number;
  stride: number;
  downsampled: boolean;
  min: number | null;
  max: number | null;
  time: (number | null)[];
  values: (number | null)[];
}

export interface SeriesResponse {
  parameter: string;
  unit: string;
  label: string;
  time_unit: string;
  series: SeriesItem[];
}

export interface OverlayItem {
  key: string;
  label: string;
  time: (number | null)[];
  values: (number | null)[];
}

export interface OverlayFlags {
  mean: boolean;
  median: boolean;
  cummulative_average: boolean;
  self_correlation_mean: boolean;
  difference: boolean;
  running_average: boolean;
}

export interface AnalysisBlock {
  sem: number | null;
  inefficiency: number | null;
  correlation_time: number | null;
  n_effective: number | null;
  equil_index: number | null;
  equil_time: number | null;
  discarded_fraction: number | null;
  equilibrated: boolean | null;
}

export interface StatBlock {
  label: string;
  rows: number;
  latest: number | null;
  mean: number | null;
  median: number | null;
  std: number | null;
  min: number | null;
  max: number | null;
  /** Second-half vs first-half mean shift, in standard deviations. */
  drift: number | null;
  /** Present on the focused summary; absent on dashboard entries. */
  analysis?: AnalysisBlock;
}

export interface SummaryResponse {
  parameter: string;
  unit: string;
  label: string;
  files: StatBlock[];
  combined: StatBlock;
}

export interface SummaryEntry {
  name: string;
  unit: string;
  label: string;
  files: StatBlock[];
  combined: StatBlock;
  spark: (number | null)[];
  hist: { edges: number[]; counts: number[] } | null;
}

export interface KdeCurve {
  label: string;
  x: number[];
  y: number[];
}

export interface HistogramResponse {
  parameter: string;
  unit: string;
  label: string;
  edges: number[];
  series: { label: string; rows: number; counts: number[] }[];
  guides: { label: string; value: number }[];
  kde: KdeCurve[];
}

async function get<T>(path: string): Promise<T> {
  // Live-monitoring data must never come from the HTTP cache.
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(
      typeof detail?.detail === "string"
        ? detail.detail
        : `Request failed (${response.status})`,
    );
  }
  return response.json() as Promise<T>;
}

export interface StatusResponse {
  files: FileStatus[];
  stale: boolean;
}

export const fetchMeta = () => get<Meta>("/api/meta");
export const fetchStatus = () => get<StatusResponse>("/api/status");
export const fetchParameters = () =>
  get<{ parameters: Parameter[] }>("/api/parameters").then((r) => r.parameters);
export const fetchSeries = (parameter: string) =>
  get<SeriesResponse>(`/api/series?parameter=${encodeURIComponent(parameter)}`);
export const fetchSummary = (parameter: string) =>
  get<SummaryResponse>(`/api/summary?parameter=${encodeURIComponent(parameter)}`);
export const fetchSummaries = () =>
  get<{ summaries: SummaryEntry[] }>("/api/summaries").then((r) => r.summaries);
export const fetchHistogram = (parameter: string, bins: number) =>
  get<HistogramResponse>(
    `/api/histogram?parameter=${encodeURIComponent(parameter)}&bins=${bins}`,
  );

export function fetchOverlays(
  parameter: string,
  flags: OverlayFlags,
  windowSize: string,
): Promise<{ overlays: OverlayItem[] }> {
  const query = new URLSearchParams({ parameter });
  (Object.keys(flags) as (keyof OverlayFlags)[]).forEach((key) => {
    if (flags[key]) query.set(key, "true");
  });
  if (windowSize.trim()) query.set("window_size", windowSize.trim());
  return get(`/api/overlays?${query.toString()}`);
}

export async function postRefresh(): Promise<StatusResponse> {
  const response = await fetch("/api/refresh", {
    method: "POST",
    cache: "no-store",
  });
  if (!response.ok) throw new Error(`Refresh failed (${response.status})`);
  return response.json() as Promise<StatusResponse>;
}

/** Compact value formatting without hiding scale (mirrors the TUI). */
export function formatValue(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "n/a";
  }
  const magnitude = Math.abs(value);
  if (magnitude !== 0 && (magnitude < 1e-3 || magnitude >= 1e5)) {
    return value.toExponential(2);
  }
  return Number(value.toPrecision(5)).toString();
}

/** Shorter variant for axis ticks. */
export function formatTick(value: number): string {
  if (!Number.isFinite(value)) return "";
  const magnitude = Math.abs(value);
  if (magnitude !== 0 && (magnitude < 1e-3 || magnitude >= 1e5)) {
    return value.toExponential(1);
  }
  return Number(value.toPrecision(4)).toString();
}

const SUPERSCRIPT_DIGITS: Record<string, string> = {
  "0": "⁰",
  "1": "¹",
  "2": "²",
  "3": "³",
  "4": "⁴",
  "5": "⁵",
  "6": "⁶",
  "7": "⁷",
  "8": "⁸",
  "9": "⁹",
  "-": "⁻",
};

/** Compact sigma formatting with an explicit sign (+1.2σ, −0.3σ, —). */
export function formatSigma(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "—";
  }
  const sign = value < 0 ? "−" : "+";
  return `${sign}${Math.abs(value).toPrecision(2)}σ`;
}

/**
 * Render simulation units properly: A^3 becomes Å³, g/cm^3 becomes g/cm³,
 * amuA/fs becomes amu·Å/fs, and the dimensionless "-" marker becomes empty
 * (callers fall back to "n/a" or omit the unit).
 */
export function formatUnit(unit: string | null | undefined): string {
  if (!unit || unit === "-") return "";
  // Bare A before a slash, caret, or end-of-string is the ångström unit
  // (A^3, amuA/fs). No word boundary: amuA has none before the A.
  const angstrom = unit.replace(/A(?=[/^]|$)/g, "Å");
  const superscripted = angstrom.replace(
    /\^(-?\d+)/g,
    (match) =>
      [...match.slice(1)].map((digit) => SUPERSCRIPT_DIGITS[digit] ?? digit).join(""),
  );
  return superscripted.replace("amuÅ", "amu·Å");
}
