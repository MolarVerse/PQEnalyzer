import { useEffect, useRef, useState } from "react";
import { fetchStatus } from "../api";

export type ConnectionState = "live" | "polling" | "offline";

const POLL_FALLBACK_MS = 5000;

/**
 * Live staleness pushes over SSE (/api/events), with a status-poll
 * fallback where EventSource is unavailable. The connection is `offline`
 * while the stream is down (proxy cut, server restart): data stays put,
 * the badge says so, and native SSE retry flips it back on reconnect.
 */
export function useLiveStatus(callbacks: {
  onStale: () => void;
  onReconnect: () => void;
}): ConnectionState {
  const [connection, setConnection] = useState<ConnectionState>(() =>
    typeof EventSource === "undefined" ? "polling" : "live",
  );
  const refs = useRef(callbacks);
  refs.current = callbacks;

  useEffect(() => {
    if (typeof EventSource === "undefined") {
      const interval = window.setInterval(async () => {
        try {
          const status = await fetchStatus();
          if (status.stale) refs.current.onStale();
        } catch {
          /* keep showing last good data */
        }
      }, POLL_FALLBACK_MS);
      return () => window.clearInterval(interval);
    }
    const source = new EventSource("/api/events");
    const onStaleEvent = () => refs.current.onStale();
    const onOpen = () => {
      setConnection("live");
      refs.current.onReconnect();
    };
    const onError = () => setConnection("offline");
    source.addEventListener("stale", onStaleEvent);
    source.addEventListener("open", onOpen);
    source.addEventListener("error", onError);
    return () => source.close();
  }, []);

  return connection;
}
