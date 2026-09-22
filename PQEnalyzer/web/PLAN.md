# PQEnalyzer Web — implementation plan (LOCAL-ONLY preview)

Standing constraints: nothing is committed or pushed; all work stays in the
working tree (`PQEnalyzer/web/`, `PQEnalyzer/tests/web/`,
`PQSetup/.../pq-design` fixes). The `web` CLI mode, `flat_mono.py`, and the
`@molarverse/pq-design` file: dependency are preview scaffolding, not product.

## Where we are (verified)

- FastAPI backend (`PQEnalyzer/web/{app,api}.py`) reusing readers, energy_access,
  plots.features, statistics. Endpoints: meta/status/refresh/parameters/series/
  overlays/histogram/summary/summaries/export.csv. 274 pytest green.
- React+TS frontend (`PQEnalyzer/web/frontend/src/`): dashboard (sparklines +
  mini-hists, drift badges, sort), focused series (brush zoom, presets, hover
  table, legend values, MSER marker, overlays), focused histogram (guides, KDE),
  palette, URL hash state, auto-refresh polling. `tsc` gated in `npm run build`.
- Shared stats: O(n) running average, block SEM/g/τ (Flyvbjerg–Petersen/Geyer),
  batched MSER — used by web, available to desktop/TUI later.
- Live behavior proven against replayed growing files; 500k rows + 8
  concurrent clients measured (overlays 0.44s, summaries 0.03s cached).
- Open PQ finding (NOT this project): `examples/h2o_mm` guff.dat (144.538)
  vs binary (144.49796…); rescaled runs explode. Separate opencode session
  investigates; brief at `/tmp/opencode/pq-investigation-brief.md`.

## Research briefs (2026-09-21, subagents)

- **uPlot**: fits (8×4k pts trivial, ~48KB/21KB gzip, zero-dep). No official
  React wrapper — roll ~60-line ref/effect wrapper (Grafana/SigNoz pattern).
  Theming via JS opts (font strings, grid strokes, pxAlign); custom HTML
  tooltip + legend via setCursor/setLegend plugin (~30-80 lines); endpoint
  dots need a small points/filter hack. Legend latest-values + click-toggle
  custom. Zoom presets via setScale; brush native; dbl-click reset.
  Verdict: adopt for the TIME chart only; keep hand-rolled SVG histogram
  (uPlot bars add little).
- **SSE**: use native FastAPI `EventSourceResponse` (or sse-starlette 3.4.x):
  background thread mtime-watcher → `loop.call_soon_threadsafe` →
  per-client asyncio.Queue; heartbeat comments; EventSource client with
  `retry`, `Last-Event-ID`, and a poll fallback when EventSource is missing
  or the stream closes (no retry on HTTP 4xx/5xx). Single worker is fine
  (async-suspended handlers don't block). Verdict: ~20 lines server +
  ~10 client; do it after the chart migration.

## Phases (ship each independently; suite + screenshots per phase)

### Phase 0 — Test harness + pure-logic tests ✅ DONE
- `vitest` (+ `jsdom`) devDeps, `"test": "vitest run"` script.
- Tests: `hash.test.ts`, `charts.test.ts` (niceTicks/decimate/pathFor/
- nearestIndex), `api.test.ts` (formats). 20 green.
- Already paid off: caught a real `amuA/fs` unit-formatting bug.

### Phase 1 — Split App.tsx (no behavior change) ✅ DONE
- Extracted `views/SeriesView.tsx`, `views/HistogramView.tsx`,
  `views/DashboardView.tsx`, `hooks/useSession.ts` (meta/params/summaries/
  poll/refresh + generation counter), `hooks/useFocus.ts` (focus/mode/hash),
  `hooks/useParameterData.ts` (series/overlays/summary/histogram),
  `components/Stats.tsx`, `components/Chrome.tsx`, `components/RailBlocks.tsx`.
- App.tsx 798 → 338 lines. tsc + 20 vitest + 277 pytest + build green;
  dashboard/series/histogram screenshots identical, no console errors.
- Side fix: manual refresh now also reloads parameters/summaries
  (previously only meta + focused parameter).

### Phase 2 — Data-table view + shortcut help (a11y path) ✅ DONE
- `tables.ts` pure builders (`seriesTable` aligns per-file [time, value]
  pairs with nulls, caps at 2000 rows; `histogramTable` maps all bins) +
  `tables.test.ts` (4 tests: alignment, truncation, empty, short-counts).
- `components/DataTable.tsx` (`SeriesDataTable`, `HistogramDataTable`:
  sticky head, tabular numerals, null glyph) + "Data" ghost buttons in both
  title rows opening a `full` Modal with transported-count subtitle and a
  full-resolution CSV export link. `components/ShortcutHelp.tsx` lists every
  shortcut; `?` opens it, Esc closes (before tools/focus handling), also in
  the palette under a new "Help" group.
- Caught + fixed a real Phase-1 bug: `useFocus` initialized against the
  empty pre-load parameter list, dropping deep-linked `?p=` on fresh loads
  (now takes a `ready` flag; direct hash-URL load verified).
- Done: 24 vitest + 13 web pytest + tsc + build green; keyboard-only flow
  scripted (`?`→Esc keeps focus, Data→table→Esc, hist table 48 rows);
  screenshots, no console errors.

### Phase 3 — uPlot time-chart migration ✅ DONE
- `components/UPlotChart.tsx` (uPlot 1.6.32 canvas; React owns legend,
  tooltip, endpoint dots, MSER marker, presets as HTML overlays so the
  flat-mono language stays in one place) + `alignSeries` union-x builder in
  `tables.ts` (exact, nulls stay gaps; 3 tests). Deleted the SVG `TimeChart`,
  `decimate`, `pathFor`, `nearestIndex` and their tests; dropped the
  SVG-only CSS leftovers. Kept: legend w/ values + toggles, hover table,
  brush zoom, dblclick reset, presets, y-always-full-data, raw dimming.
- Two real bugs caught by the audit: (1) wrap padding fed back into canvas
  size → ResizeObserver recreate loop (fixed with a fixed-px mount);
  (2) a static-array x `range` snaps every `setScale` back to the creation
  domain — must be a function range (uPlot re-invokes it per setScale).
- Difference mode refuses on the demo files (disjoint time grids) —
  pre-existing backend behavior, unchanged.
- Done: tsc + 19 vitest + 277 pytest + build green; interaction audit
  (hover/brush/dblclick/presets/legend/overlays/marker/narrow) clean;
  histogram + dashboard screenshots identical, no console errors.

### Phase 4 — Live transport + state hardening ✅ DONE
- Backend `/api/events` (SSE: `retry: 2000` hint, `hello` with status,
  `stale` pushes, `: ping` heartbeats) + lazy daemon mtime watcher in
  `WebState` (0.5s scan, one push per fresh→stale transition, bounded
  per-client queues, unsubscribe on disconnect). `/api/status` stays the
  fallback, POST `/api/refresh` the manual path. 4 new `test_events.py`
  tests (hello/stale/heartbeat/single-push + unsubscribe).
- Frontend `useLiveStatus` (EventSource + 5s status-poll fallback where
  SSE is missing + offline flag) + 4 vitest tests with a stubbed
  EventSource (push/open/error/unmount/fallback). `useSession` dropped
  the 2.5s poll; badge gains `offline` (pending ◐ glyph, data stays put).
- Caught in verification: resuming auto-refresh no longer re-synced
  (pushes only fire on transitions) — added a resume-sync effect.
  Also repaired two selectors eaten by the Phase 3 CSS surgery
  (.chart-foot, .chart-tooltip) and re-verified the bundle.
- Done: tsc + 23 vitest + 281 pytest + build green. Live acceptance on
  the running server: touch→stale banner 0.82s paused, resume clears
  0.23s, watching auto-roundtrip; route-aborted stream → offline badge
  with intact chart → reconnect flips back; kill -9 → offline,
  restart → watching with data intact, no console errors.

### Phase 5 — Deferred product depth ✅ DONE (all six)
- **Split compare**: `Split` toggle (2+ files, disabled with an explanation
  in difference mode) renders one panel per file with latest/rows/stride
  heads, overlays repeated as reference, and lockstep zoom via controlled
  `zoom`/`onZoomChange` on `UPlotChart` plus one shared preset bar
  (`presetRangeFor`/`PRESETS` exported for reuse).
- **Runs table**: `Runs` modal with W&B-style sortable per-file stats
  (nulls sink, combined pinned, drift in σ) + `sortRuns` unit tests.
- **PNG export**: `PNG` button; `UPlotChart` exposes `exportPNG` (canvas
  data URL, axes included); split composites stacked panels into one file.
- **Pinch zoom**: two-finger handlers on the chart wrap (anchor keeps its
  fraction, hover suppressed mid-pinch) + `pinchRange` unit tests; verified
  over CDP touch events (span halved, anchored).
- **Y soft min/max**: `Y-axis` tools block (blank = auto), expand-only
  `applySoftBounds` + tests, plumbed App → SeriesView → uPlot; plus an
  Esc-in-input blur fix the new text fields exposed (shortcuts resume).
- **Mini guides**: dashboard histogram minis draw mean (solid) + median
  (dashed) via `guideX` + tests.
- Done: tsc + 36 vitest + 281 pytest + build green; audited split lockstep,
  PNG download (104 KB composite), runs sorting, pinch, soft bounds
  (0–400 axis), mini guides (22 lines), split+overlay dimming; no errors.

## Decisions log
- Downsampling stays server-side stride (honest, disclosed); min-max
  per-pixel happens client-side for rendering only.
- Overlay math stays server-side in `plots.features` (single source of truth).
- No `pyproject.toml` dependency changes in preview (fastapi/uvicorn/httpx
  assumed present locally; static/ built locally, untracked).
- `tokens.json` is the style source of truth; never restyle by overriding
  with self-referential `var()` (cycle bug documented 2026-09-19).
