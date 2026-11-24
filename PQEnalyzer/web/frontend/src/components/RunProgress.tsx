import { appApi } from "../runEmbed";
import { useEffect, useState } from "react";

type Snapshot = {
  state: "running" | "completed" | "failed";
  stage: number;
  total: number;
  steps: number;
  target: number;
  eta_seconds?: number | null;
  elapsed_seconds?: number;
  steps_per_second?: number | null;
};

export function RunProgress({ autoRefresh }: { autoRefresh: boolean }) {
  const [details, setDetails] = useState(false);
  const [progress, setProgress] = useState<Snapshot | null>(null);
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;

    async function poll() {
      let repeat = autoRefresh;
      try {
        const response = await fetch(appApi("/api/run-progress"), { signal: controller.signal });
        if (!response.ok) throw new Error();
        const snapshot: Snapshot | null = await response.json();
        if (controller.signal.aborted) return;
        setProgress(snapshot);
        setUnavailable(false);
        repeat = autoRefresh && snapshot?.state === "running";
      } catch {
        if (!controller.signal.aborted) setUnavailable(true);
      } finally {
        if (!controller.signal.aborted && repeat) timer = setTimeout(poll, 1500);
      }
    }

    void poll();
    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [autoRefresh]);

  if (!progress) return unavailable ? <p className="simulation-progress" role="status">Run progress unavailable</p> : null;
  const label = unavailable ? "Run progress unavailable"
    : progress.state === "completed" ? "Simulation finished"
      : progress.state === "failed" ? "Simulation failed"
        : !autoRefresh ? "Progress paused"
          : progress.stage ? `Stage ${progress.stage} / ${progress.total}` : "Starting simulation";
  const duration = (seconds: number) => seconds < 60 ? `${seconds}s` : `${Math.round(seconds / 60)}m`;
  return <div className="simulation-progress">
    <div className="simulation-summary" role="status">
      <strong>{label}</strong>
      <span>{progress.steps.toLocaleString()} / {progress.target.toLocaleString()} steps
        {autoRefresh && !unavailable && progress.eta_seconds != null && ` · ~${duration(progress.eta_seconds)} left`}
      </span>
    </div>
    <button type="button" className="simulation-details" aria-expanded={details}
      aria-controls="simulation-timing" onClick={() => setDetails(!details)}>Details</button>
    <div id="simulation-timing" className="simulation-timing" hidden={!details}>
      {progress.elapsed_seconds != null && <div>Elapsed: {duration(progress.elapsed_seconds)}</div>}
      {progress.steps_per_second != null && <div>Recent speed: {Math.round(progress.steps_per_second).toLocaleString()} steps/s</div>}
      <div>{(progress.target - progress.steps).toLocaleString()} steps remaining</div>
    </div>
  </div>;
}
