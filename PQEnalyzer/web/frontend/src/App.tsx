import { AppHeader, AutoRefreshButton, HeaderStatus, HelpButton, HelpPanels, type HelpPage, SearchTrigger, useHealthProbe } from "@molarverse/pq-design";
/* PQEnalyzer Web shell. */

import {
  CommandPalette,
  type Command,
} from "@molarverse/pq-design";
import { useEffect, useMemo, useState } from "react";
import { RotateCcw } from "lucide-react";
import {
  formatUnit,
  type OverlayFlags,
} from "./api";
import { AnalysisPicker, HistogramBlock, NO_OVERLAYS, OVERLAY_DEFS, toggleOverlay } from "./components/RailBlocks";
import { ModeSeg } from "./components/Chrome";
import { MODES, MODE_LABEL } from "./mode";
import { useFocus } from "./hooks/useFocus";
import { useParameterData } from "./hooks/useParameterData";
import { useSession } from "./hooks/useSession";
import { DashboardView, type SortMode } from "./views/DashboardView";
import { HistogramView } from "./views/HistogramView";
import { SeriesView } from "./views/SeriesView";
import {
  browserStorage,
  loadSettings,
  saveSettings,
} from "./settings";
function isAnalysisHealth(value: unknown): value is { files: { rows: number; stale: boolean }[]; stale: boolean } {
  return Boolean(value && typeof value === "object" && "files" in value && Array.isArray(value.files)
    && "stale" in value && typeof value.stale === "boolean");
}

export default function App() {
  // Overlay defaults (combined mean) and dashboard sort persist per browser.
  const [stored] = useState(() => loadSettings(browserStorage()));
  const [flags, setFlags] = useState<OverlayFlags>(() => ({
    ...NO_OVERLAYS,
    ...stored.overlays,
  }));
  const [windowSize, setWindowSize] = useState("");
  const [bins, setBins] = useState("");
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [sortMode, setSortMode] = useState<SortMode>(
    stored.sortMode === "drift" ? "drift" : "name",
  );
  const [toolsOpen, setToolsOpen] = useState(false);
  const [showKde, setShowKde] = useState(false);
  const [helpPage, setHelpPage] = useState<HelpPage | null>(null);
  const searchShortcut = /Mac|iPhone|iPad/.test(navigator.platform) ? "⌘ K" : "Ctrl K";

  const health = useHealthProbe("/api/status", isAnalysisHealth);
  const session = useSession();
  const { focus, mode, selectMode, focusParameter } = useFocus(session.parameters, !session.loading);
  const paramData = useParameterData(focus, flags, windowSize, bins, mode, session.generation);

  useEffect(() => {
    setToolsOpen(false);
  }, [focus, mode]);

  // Persist analysis choices and dashboard sort.
  useEffect(() => {
    saveSettings(browserStorage(), {
      version: 1,
      overlays: flags,
      sortMode,
    });
  }, [flags, sortMode]);

  const error = session.error ?? paramData.error;
  const activeParam = session.parameters.find((param) => param.name === focus) ?? null;


  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.defaultPrevented || event.isComposing || helpPage !== null) return;
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
      if (event.key === "?") {
        setHelpPage("shortcuts");
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
        setFlags((current) => toggleOverlay(current, overlayKey));
        return;
      }
      const modeIndex = ["1", "2"].indexOf(event.key);
      if (modeIndex >= 0) selectMode(MODES[modeIndex]);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [focus, focusParameter, helpPage, paletteOpen, selectMode, toolsOpen]);

  /** Largest valid manual window in the combined sequence. */
  const maxWindow = useMemo(
    () =>
      paramData.series?.series.reduce(
        (longest, item) => Math.max(longest, item.rows),
        1,
      ) ?? 1,
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
        id: "help",
        label: "Help",
        group: "Help",
        run: () => setHelpPage("help"),
      },
      {
        id: "help-shortcuts",
        label: "Keyboard shortcuts",
        group: "Help",
        hint: "?",
        run: () => setHelpPage("shortcuts"),
      },
    ];
    return [...paramCommands, ...modeCommands, ...helpCommands];
  }, [session.parameters, focus, mode, focusParameter, selectMode]);



  const currentFiles = session.meta?.files.map(
    ({ label, path }) => path.split(/[\\/]/).at(-1) || label,
  );

  return (
    <div className={`web-shell${toolsOpen && focus !== null ? " tools-open" : ""}`}>
      <AppHeader
          className="web-header"
          name="PQEnalyzer"
          context={currentFiles?.[0]}
          files={currentFiles}
          actions={<HelpButton open={helpPage !== null} onClick={() => setHelpPage("help")} />}
          logo="/icon.png"
          search={<SearchTrigger
            label="Search…"
            accessibleName="Search parameters"
            shortcut={searchShortcut}
            open={paletteOpen}
            onOpen={() => setPaletteOpen(true)}
          />}
          status={<HeaderStatus
            checks={[
              { label: "Server connection", state: health.state },
              {
                label: "Simulation output",
                state: session.error || (session.meta && (!session.fileCount || session.meta.stale || health.data?.stale))
                  ? "fail" : session.meta ? "pass" : health.state === "fail" ? "skipped" : "pending",
                detail: session.error ? "The output files could not be loaded."
                  : session.meta?.stale || health.data?.stale ? "Files changed on disk; the displayed data is out of date." : undefined,
              },
              {
                label: "Analysis data",
                state: paramData.error ? "fail" : session.parameters.length ? "pass"
                  : session.loading ? "pending" : session.meta ? "fail" : "skipped",
                detail: paramData.error ? "The current analysis could not be loaded." : undefined,
              },
              {
                label: "Live updates",
                state: !session.autoRefresh ? "skipped" : session.connection === "offline" || health.state === "fail" ? "fail"
                  : health.state,
                detail: !session.autoRefresh ? "Paused by you." : session.connection === "polling" ? "Checking periodically." : undefined,
              },
            ]}
          />}
        />

      <div className="web-body">
        <div className="chart-toolbar pq-data-tools" role="group" aria-label="Chart controls">
          <ModeSeg mode={mode} onSelect={selectMode} />
          <AutoRefreshButton active={session.autoRefresh}
            onToggle={() => session.setAutoRefresh((value) => !value)} />
        </div>
        <main className={`web-main${focus === null ? "" : " focused"}`}>
          {session.loading && <p className="output-empty">Loading session…</p>}
          {error && (
            <p className="notice error" role="alert">
              <span>{error}</span>
              <button type="button" onClick={() => void session.loadSession()}>
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
              onRefresh={() => void session.refreshNow()}
              onBack={() => focusParameter(null)}
              seriesLoading={paramData.seriesLoading}
              series={paramData.series}
              overlays={paramData.overlays}
              overlaysLoading={paramData.overlaysLoading}
              flags={flags}
              timeLabel={session.meta?.time_label ?? "Simulation Time"}
              summary={paramData.summary}
              overlayError={paramData.overlayError}
              toolsOpen={toolsOpen}
              onToggleTools={() => setToolsOpen((open) => !open)}
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

          {!session.loading && !error && focus && paramData.summaryError && (
            <p className="notice error" role="alert">
              <span>Summary unavailable: {paramData.summaryError}</span>
            </p>
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
          aria-label={mode === "series" ? "Analysis options" : "Histogram options"}
        >
          <div className="tools-head">
            <strong>{mode === "series" ? "Analysis" : "Histogram"}</strong>
            <div className="tools-head-actions">
              {mode === "series" && Object.values(flags).some(Boolean) && (
                <button
                  type="button"
                  className="ghost-action"
                  aria-label="Clear analysis"
                  title="Clear analysis"
                  onClick={() => setFlags({ ...NO_OVERLAYS })}
                >
                  <RotateCcw size={14} aria-hidden="true" />
                </button>
              )}
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
          </div>
          {mode === "series" ? (
            <AnalysisPicker
              flags={flags}
              setFlags={setFlags}
              windowSize={windowSize}
              setWindowSize={setWindowSize}
              maxWindow={maxWindow}
            />
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
      <HelpPanels page={helpPage} onPage={setHelpPage} docs="https://molarverse.github.io/PQEnalyzer/"
        intro={<p>Search for a simulation parameter. Switch between Series and Histogram to inspect how it changes or how it is distributed.</p>}
        groups={[
          { title: "Workspace", items: [
            [searchShortcut, "Search parameters and modes"],
            ["1 / 2", "Series / histogram mode"],
            ["O", "Analysis / histogram options"],
            ["?", "Keyboard shortcuts"],
            ["Esc", "Close a panel or return to the dashboard"],
          ] },
          { title: "Plot overlays", items: OVERLAY_DEFS.map(({ shortcut, label }) => [shortcut, label]) },
        ]} />

    </div>
  );
}
