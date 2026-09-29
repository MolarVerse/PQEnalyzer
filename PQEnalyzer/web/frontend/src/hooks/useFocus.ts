import { useCallback, useEffect, useRef, useState } from "react";
import { hashState, writeHash } from "../hash";
import { type Mode } from "../mode";

/**
 * Focus (inspected parameter, null = dashboard) + mode (series|histogram).
 * The URL hash is the source of truth so back/forward and shared links work.
 */
export function useFocus(parameters: { name: string }[], ready: boolean) {
  const [focus, setFocus] = useState<string | null>(null);
  const [mode, setMode] = useState<Mode>(() => hashState().mode ?? "series");
  const initialized = useRef(false);

  // No p in the hash means the dashboard overview: never auto-focus.
  // Waits for the session: initializing against the empty pre-load list
  // would drop a deep-linked parameter.
  useEffect(() => {
    if (initialized.current || !ready) return;
    initialized.current = true;
    const initial = hashState();
    if (initial.mode) setMode(initial.mode);
    const first = initial.parameter;
    setFocus(
      first && parameters.some((param) => param.name === first) ? first : null,
    );
  }, [parameters, ready]);

  useEffect(() => {
    const onHash = () => {
      const state = hashState();
      setFocus(state.parameter);
      if (state.mode) setMode(state.mode);
    };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const selectMode = useCallback((next: Mode) => {
    writeHash((params) => params.set("m", next));
    setMode(next);
  }, []);

  const focusParameter = useCallback(
    (name: string | null) => {
      setFocus(name);
      writeHash((params) => {
        if (name) params.set("p", name);
        else params.delete("p");
        if (!params.has("m")) params.set("m", mode);
      });
    },
    [mode],
  );

  return { focus, mode, selectMode, focusParameter };
}
