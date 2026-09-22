/*
 * PQEnalyzer Web shell (LOCAL-ONLY preview).
 * Display mode (series|histogram) is shared; focus (parameter|null) picks
 * the dashboard overview or one focused chart. A control only ever changes
 * what is below it.
 */

import {
  CommandPalette,
  Modal,
  type Command,
} from "@molarverse/pq-design";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  formatUnit,
  type OverlayFlags,
} from "./api";
import { AnalysisBlock, HistogramBlock, OVERLAY_DEFS, OverlaysBlock, YAxisBlock, type SoftBounds } from "./components/RailBlocks";
import { ShortcutHelp } from "./components/ShortcutHelp";
import { ModeSeg } from "./components/Chrome";
import { MODES, MODE_LABEL } from "./mode";
import { useFocus } from "./hooks/useFocus";
import { useParameterData } from "./hooks/useParameterData";
import { useSession } from "./hooks/useSession";
import { DashboardView, type SortMode } from "./views/DashboardView";
import { HistogramView } from "./views/HistogramView";
import { SeriesView } from "./views/SeriesView";



const EMPTY_FLAGS: OverlayFlags = {
  mean: false,
  median: false,
  cummulative_average: false,
  self_correlation_mean: false,
  difference: false,
  running_average: false,
};
/** Track a CSS media query so rail blocks render in exactly one place. */
function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(
    () => window.matchMedia(query).matches,
  );
  useEffect(() => {
    const list = window.matchMedia(query);
    const onChange = () => setMatches(list.matches);
    list.addEventListener("change", onChange);
    return () => list.removeEventListener("change", onChange);
  }, [query]);
  return matches;
}

/**
 * The scientific headline under the chart: equilibration verdict plus the
 * correlated error diagnostics. Details live in the tools panel.
 */


export default function App() {
  const [flags, setFlags] = useState<OverlayFlags>(EMPTY_FLAGS);
  const [windowSize, setWindowSize] = useState("1000");
  const [bins, setBins] = useState("48");
  const [yBounds, setYBounds] = useState<SoftBounds>({ min: "", max: "" });
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [sortMode, setSortMode] = useState<SortMode>("name");
  const [toolsOpen, setToolsOpen] = useState(false);
  const [showEquil, setShowEquil] = useState(true);
  const [showKde, setShowKde] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const narrow = useMediaQuery("(max-width: 1100px)");

  const session = useSession();
  const { focus, mode, selectMode, focusParameter } = useFocus(session.parameters, !session.loading);
  const paramData = useParameterData(focus, flags, windowSize, bins, mode);

  const reloadFocus = useCallback(() => {
    if (focus) void paramData.loadParameter(focus);
  }, [focus, paramData.loadParameter]);

  // Session auto-refresh bumps the generation: reload the focused parameter.
  useEffect(() => {
    if (session.generation > 0) reloadFocus();
  }, [session.generation, reloadFocus]);

  const refreshNow = useCallback(async () => {
    await session.refreshNow();
    reloadFocus();
  }, [session.refreshNow, reloadFocus]);

  const error = session.error ?? paramData.error;
  const activeParam = session.parameters.find((param) => param.name === focus) ?? null;


  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const mod = event.metaKey || event.ctrlKey;
      if (mod && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setPaletteOpen((open) => !open);
        return;
      }
      if (mod || event.altKey || paletteOpen) return;
      const target = event.target as HTMLElement | null;
      if (event.key === "Escape" && target?.tagName === "INPUT") {
        // Editing a tools-panel field: Esc leaves the field (shortcuts
        // resume) instead of typing nowhere.
        target.blur();
        return;
      }
      if (
        target &&
        (target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.tagName === "SELECT")
      ) {
        return;
      }
      if (event.key === "Escape" && helpOpen) {
        setHelpOpen(false);
        return;
      }
      if (event.key === "?") {
        setHelpOpen(true);
        return;
      }
      if (event.key === "Escape" && toolsOpen) {
        setToolsOpen(false);
        return;
      }
      if (event.key === "Escape" && focus !== null) {
        focusParameter(null);
        return;
      }
      if (event.key.toLowerCase() === "o") {
        setToolsOpen((open) => !open);
        return;
      }
      const overlayKey = OVERLAY_DEFS.find(
        (def) => def.shortcut === event.key.toLowerCase(),
      )?.key;
      if (overlayKey) {
        if (overlayKey === "difference" && session.fileCount !== 2) return;
        if (overlayKey !== "difference" && flags.difference) return;
        setFlags((current) => ({ ...current, [overlayKey]: !current[overlayKey] }));
        return;
      }
      const modeIndex = ["1", "2"].indexOf(event.key);
      if (modeIndex >= 0) selectMode(MODES[modeIndex]);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [session.fileCount, flags.difference, focus, focusParameter, helpOpen, paletteOpen, selectMode, toolsOpen]);

  /** Upper bound for the smoothing slider: the longest loaded file. */
  const maxWindow = useMemo(
    () =>
      paramData.series?.series.reduce(
        (longest, item) => Math.max(longest, item.rows),
        1000,
      ) ?? 1000,
    [paramData.series],
  );


  const paletteCommands: Command[] = useMemo(() => {
    const paramCommands: Command[] = session.parameters.map((param) => ({
      id: `param-${param.name}`,
      label: param.name,
      group: "Parameters",
      hint: formatUnit(param.unit) || `${param.rows.toLocaleString()} rows`,
      current: param.name === focus,
      featured: true,
      run: () => focusParameter(param.name),
    }));
    const modeCommands: Command[] = MODES.map((key) => ({
      id: `mode-${key}`,
      label: `${MODE_LABEL[key]} mode`,
      group: "Modes",
      current: mode === key,
      featured: true,
      run: () => selectMode(key),
    }));
    const helpCommands: Command[] = [
      {
        id: "help-shortcuts",
        label: "Keyboard shortcuts",
        group: "Help",
        hint: "?",
        run: () => setHelpOpen(true),
      },
    ];
    return [...paramCommands, ...modeCommands, ...helpCommands];
  }, [session.parameters, focus, mode, focusParameter, selectMode]);



  return (
    <div className="web-shell">
      <header className="web-header">
        <div className="brand">
          <img src="/icon.png" alt="" />
          <strong>PQEnalyzer Web</strong>
        </div>
        <div className="header-center">
          <button
            type="button"
            className="command-search"
            onClick={() => setPaletteOpen(true)}
          >
            <span>{focus ?? "Search parameters…"}</span>
            <kbd>Ctrl K</kbd>
          </button>
        </div>
        <div className="header-status">
          {!narrow && <ModeSeg mode={mode} onSelect={selectMode} />}
          <button
            type="button"
            className={`pq-tag ${session.connection === "offline" ? "pending" : session.meta?.stale ? "missing" : "ok"}`}
            title={
              session.connection === "offline"
                ? "Connection lost — retrying in the background; data stays put"
                : session.meta?.stale
                  ? "Files changed on disk — activate to refresh"
                  : session.autoRefresh
                    ? `Watching files${session.updatedAt ? ` · updated ${session.updatedAt}` : ""} — activate to pause`
                    : "Paused — activate to resume watching"
            }
            aria-pressed={session.autoRefresh}
            aria-label={
              session.connection === "offline"
                ? "Offline — retrying in the background"
                : session.autoRefresh ? "Pause auto-refresh" : "Resume auto-refresh"
            }
            onClick={() => session.setAutoRefresh((value) => !value)}
          >
            <span className="pq-tag-value">
              {session.connection === "offline"
                ? "offline"
                : session.meta?.stale ? "stale" : session.autoRefresh ? "watching" : "paused"}
            </span>
          </button>
        </div>
      </header>

      <div className="web-body">
        <main className={`web-main${focus === null ? " scroll" : ""}`}>
          {narrow && (
            <div className="narrow-views">
              <ModeSeg mode={mode} onSelect={selectMode} />
            </div>
          )}
          {session.loading && <p className="output-empty">Loading session…</p>}
          {error && (
            <p className="notice error" role="alert">
              <span>{error}</span>
              <button type="button" onClick={() => { void session.loadSession(); reloadFocus(); }}>
                Retry
              </button>
            </p>
          )}

          {!session.loading && !error && focus && mode === "series" && (
            <SeriesView
              focus={focus}
              unit={activeParam?.unit ?? ""}
              stale={session.meta?.stale ?? false}
              autoRefresh={session.autoRefresh}
              onRefresh={() => void refreshNow()}
              onBack={() => focusParameter(null)}
              seriesLoading={paramData.seriesLoading}
              series={paramData.series}
              overlays={paramData.overlays}
              flags={flags}
              timeLabel={session.meta?.time_label ?? "Simulation Time"}
              summary={paramData.summary}
              overlayError={paramData.overlayError}
              showEquil={showEquil}
              toolsOpen={toolsOpen}
              onToggleTools={() => setToolsOpen((open) => !open)}
              softBounds={yBounds}
            />
          )}

          {!session.loading && !error && focus && mode === "histogram" && (
            <HistogramView
              focus={focus!}
              unit={activeParam?.unit ?? ""}
              onBack={() => focusParameter(null)}
              toolsOpen={toolsOpen}
              onToggleTools={() => setToolsOpen((open) => !open)}
              histogram={paramData.histogram}
              showKde={showKde}
              flags={flags}
              summary={paramData.summary}
            />
          )}

          {!session.loading && !error && focus === null && (
            <DashboardView
              summaries={session.summaries}
              fileCount={session.fileCount}
              mode={mode}
              sortMode={sortMode}
              onSortMode={setSortMode}
              parameterNames={session.parameters.map((param) => param.name)}
              onInspect={focusParameter}
            />
          )}

          {!session.loading && !error && focus === null && session.parameters.length === 0 && (
            <p className="output-empty">No plottable parameters in these files.</p>
          )}
        </main>
      </div>

      {toolsOpen && focus !== null && (
        <section
          id="chart-tools"
          className="tools-panel"
          role="dialog"
          aria-label={mode === "series" ? "Overlay options" : "Histogram options"}
        >
          <div className="tools-head">
            <strong>{mode === "series" ? "Overlays" : "Histogram"}</strong>
            <button
              type="button"
              className="ghost-action"
              aria-label="Close options"
              title="Close (Esc)"
              onClick={() => setToolsOpen(false)}
            >
              <span aria-hidden="true">×</span>
            </button>
          </div>
          {mode === "series" ? (
            <>
              <OverlaysBlock
                flags={flags}
                setFlags={setFlags}
                fileCount={session.fileCount}
                windowSize={windowSize}
                setWindowSize={setWindowSize}
                maxWindow={maxWindow}
              />
              <YAxisBlock bounds={yBounds} setBounds={setYBounds} />
              <AnalysisBlock
                stats={paramData.summary?.combined ?? null}
                showMarker={showEquil}
                setShowMarker={setShowEquil}
              />
            </>
          ) : (
            <HistogramBlock
              flags={flags}
              setFlags={setFlags}
              bins={bins}
              setBins={setBins}
              showKde={showKde}
              setShowKde={setShowKde}
              kdeAvailable={(paramData.histogram?.kde.length ?? 0) > 0}
            />
          )}
        </section>
      )}

      <CommandPalette
        open={paletteOpen}
        commands={paletteCommands}
        groupOrder={["Parameters", "Modes", "Help"]}
        placeholder="Search parameters or modes…"
        onClose={() => setPaletteOpen(false)}
      />
      <Modal
        open={helpOpen}
        title="Keyboard shortcuts"
        subtitle="Every shortcut the shell offers"
        onClose={() => setHelpOpen(false)}
      >
        <ShortcutHelp />
      </Modal>
    </div>
  );
}
