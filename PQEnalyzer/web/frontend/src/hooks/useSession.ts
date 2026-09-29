import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchMeta,
  fetchParameters,
  fetchStatus,
  fetchSummaries,
  postRefresh,
  type Meta,
  type Parameter,
  type SummaryEntry,
} from "../api";
import { useLiveStatus } from "./useLiveStatus";

/**
 * Session-level data: files, parameters, and dashboard summaries, kept
 * fresh by live staleness pushes (status poll only where SSE is
 * unavailable). Parameter-level data lives in useParameterData; the
 * generation counter tells callers when an auto-refresh reloaded the
 * session so they can reload the focused parameter too.
 */
export function useSession() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [parameters, setParameters] = useState<Parameter[]>([]);
  const [summaries, setSummaries] = useState<SummaryEntry[]>([]);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const [generation, setGeneration] = useState(0);
  const autoRefreshRef = useRef(autoRefresh);
  autoRefreshRef.current = autoRefresh;

  const loadSession = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [loadedMeta, loadedParams, loadedSummaries] = await Promise.all([
        fetchMeta(),
        fetchParameters(),
        fetchSummaries(),
      ]);
      setMeta(loadedMeta);
      setParameters(loadedParams);
      setSummaries(loadedSummaries);
      setUpdatedAt(new Date().toLocaleTimeString());
    } catch (error) {
      setError(error instanceof Error ? error.message : String(error));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadSession();
  }, [loadSession]);

  const refreshNow = useCallback(async () => {
    const fresh = await postRefresh();
    setMeta((current) =>
      current ? { ...current, files: fresh.files, stale: fresh.stale } : current,
    );
    await loadSession();
  }, [loadSession]);

  // Push-driven freshness: on a stale event (or a reconnect, which may
  // have missed pushes) sync file rows once, then auto-refresh when on.
  const syncFromStatus = useCallback(async () => {
    try {
      const status = await fetchStatus();
      setMeta((current) =>
        current ? { ...current, files: status.files, stale: status.stale } : current,
      );
      if (status.stale && autoRefreshRef.current) {
        await refreshNow();
        setGeneration((value) => value + 1);
      }
    } catch {
      /* transient failure: keep showing last good data */
    }
  }, [refreshNow]);

  const connection = useLiveStatus({
    onStale: () => void syncFromStatus(),
    onReconnect: () => void syncFromStatus(),
  });

  // Resuming auto-refresh must pick up staleness reported while paused
  // (pushes only fire on transitions, so no new event is coming).
  const stale = meta?.stale ?? false;
  useEffect(() => {
    if (autoRefresh && stale) void syncFromStatus();
  }, [autoRefresh, stale, syncFromStatus]);

  return {
    meta,
    parameters,
    summaries,
    autoRefresh,
    setAutoRefresh,
    loading,
    error,
    updatedAt,
    generation,
    connection,
    fileCount: meta?.files.length ?? 0,
    loadSession,
    refreshNow,
  };
}
