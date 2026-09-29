import { formatSigma, formatValue } from "../api";
import type { StatBlock } from "../api";

export function DriftBadge({ drift }: { drift: number | null }) {  if (drift === null || !Number.isFinite(drift)) {
    return (
      <span className="drift drift-flat" title="Too few points or no spread">
        —
      </span>
    );
  }
  const magnitude = Math.abs(drift);
  const tone =
    magnitude < 0.5 ? "drift-steady"
    : magnitude < 2 ? "drift-mild"
    : "drift-strong";
  const arrow = drift > 0.05 ? "▲" : drift < -0.05 ? "▼" : "●";
  return (
    <span className={`drift ${tone}`} title={`Half-vs-half shift: ${formatSigma(drift)}`}>
      {arrow} {formatSigma(drift)}
    </span>
  );
}
/**
 * Compact MSER truncation and correlated error estimates under the chart.
 */
export function AnalysisLine({ stats }: { stats: StatBlock }) {
  const analysis = stats.analysis;
  if (!analysis) return null;
  const items: [string, string][] = [];
  if (analysis.discarded_fraction != null) {
    items.push(["MSER cut", `${Math.round(analysis.discarded_fraction * 100)}%`]);
  }
  if (analysis.correlation_time != null) {
    items.push(["τ", `${Math.round(analysis.correlation_time)} steps`]);
  }
  if (analysis.n_effective != null) {
    items.push(["N_eff", Math.round(analysis.n_effective).toLocaleString()]);
  }
  if (!items.length) return null;
  return (
    <p className="stat-line analysis-line" aria-label="Truncation and correlation estimates" title="MSER estimates an initial cut; the statistics above use all samples. This is not a convergence verdict.">
      {items.map(([label, value], index) => (
        <span key={label}>
          {index > 0 && <i aria-hidden="true">·</i>}
          {label} <strong>{value}</strong>
        </span>
      ))}
    </p>
  );
}

export function StatLine({ stats, unit }: { stats: StatBlock; unit: string }) {  const latestVsMean =
    stats.latest !== null && stats.mean !== null && stats.std
      ? (stats.latest - stats.mean) / stats.std
      : null;
  const sem = stats.analysis?.sem;
  const meanValue =
    sem !== undefined && sem !== null && Number.isFinite(sem) && sem !== 0
      ? `${formatValue(stats.mean)} ± ${Number(sem.toPrecision(2)).toString()}`
      : formatValue(stats.mean);
  const items: [string, string][] = [
    ["Latest", formatValue(stats.latest)],
    ["Mean (all)", meanValue],
    ["Median", formatValue(stats.median)],
    ["σ", formatValue(stats.std)],
    ["Min", formatValue(stats.min)],
    ["Max", formatValue(stats.max)],
    ["vs mean", formatSigma(latestVsMean)],
  ];
  return (
    <p className="stat-line" aria-label={`Statistics in ${unit || "unknown unit"}`}>
      {items.map(([label, value], index) => (
        <span key={label}>
          {index > 0 && <i aria-hidden="true">·</i>}
          {label} <strong>{value}</strong>
        </span>
      ))}
    </p>
  );
}
