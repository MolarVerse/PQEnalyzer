<img src="https://raw.githubusercontent.com/MolarVerse/PQEnalyzer/main/PQEnalyzer/icons/icon.png" alt="PQEnalyzer logo" width="200">

[![CI](https://github.com/MolarVerse/PQEnalyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/MolarVerse/PQEnalyzer/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/MolarVerse/PQEnalyzer/graph/badge.svg?token=GMLrCKFfPA)](https://codecov.io/gh/MolarVerse/PQEnalyzer)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# PQEnalyzer

Plot and monitor PQ energy, box, and optimizer output in a desktop,
terminal, or browser interface.

## Install

```bash
pip install PQEnalyzer
```

## Quick Start

The GUI is the default:

```bash
pqenalyzer /path/to/simulation.en
```

Use the terminal interface with the `tui` subcommand:

```bash
pqenalyzer tui /path/to/simulation.en
```

Use the browser interface with the `web` subcommand:

```bash
pqenalyzer web /path/to/simulation.en
```

PQEnalyzer detects the input format automatically. Use a format flag only when
detection is ambiguous:

```bash
pqenalyzer --pq pq-output.en
pqenalyzer --qmcfc qmcfc-output.en
pqenalyzer --box box-output.data
pqenalyzer --opt optimization.data
```

`pqenalyzer gui FILE` is equivalent to `pqenalyzer FILE`.

## Input

| Output | Conventional file | Detection |
| --- | --- | --- |
| PQ energy | `.en` with matching `.info` | `.info` layout |
| QMCFC energy | `.en` with matching `.info` | `.info` layout |
| PQ box | `.box` | suffix or file contents |
| PQ optimizer | `.opt` | suffix |

Energy, box, and optimizer parsing is provided by
[`PQAnalysis`](https://github.com/MolarVerse/PQAnalysis).

Energy files need a matching `.info` file in the same directory. PQ `.info`
rows containing a single parameter column are supported.

Box files contain `step x y z alpha beta gamma`. PQEnalyzer plots `BOX-X`,
`BOX-Y`, `BOX-Z`, `ALPHA`, `BETA`, `GAMMA`, and `BOX-VOLUME`.

Optimizer plots use the optimization step as the x-axis. They include energy
changes, forces, convergence states, and limits. A convergence state of `-1`
means not converged, `0` means disabled, and `1` means converged. The first row
is PQ's initialization snapshot. Final completion status remains in the PQ log.

## GUI

| Control | Result |
| --- | --- |
| `Plot` | Open a time-series plot for the selected parameter |
| `Histogram` | Open its distribution |
| `Live Monitor` | Open one time-series panel per parameter |
| `Auto-Refresh` | Watch loaded files and update open plots |

Double-click a Live Monitor panel to open its focused plot. Plot settings belong
to that focused window, so each window can use different overlays.

Auto-refresh starts with the GUI. If native file watching is unavailable,
PQEnalyzer uses polling and shows `(polling)` in the status line.

Plot windows refit when resized. The Live Monitor also redistributes its grid;
press `f` to fit it to the current screen. Use `Plot Size` in the sidebar, `+`
and `-` in a plot window, or `Ctrl+0` / `Command+0` to restore `100%`.

PQEnalyzer remembers the theme, plot size, window dimensions, selected
parameter, auto-refresh state, and plot settings. Set
`PQENALYZER_CONFIG_DIR` to override the platform settings directory.

## TUI

```bash
pqenalyzer tui FILE [FILE ...]
```

| Key | Action |
| --- | --- |
| `Up` / `k`, `Down` / `j` | Select a parameter |
| `Enter` | Open the selected chart |
| `Esc` | Return to the dashboard |
| `r` | Refresh |
| `w` | Pause or resume file watching |
| `q` | Quit |

## Web

```bash
pqenalyzer web FILE [FILE ...] [--port 8766] [--no-open]
```

This starts a local-only server (loopback, default `127.0.0.1:8766`) and
opens the dashboard in your browser. Nothing leaves your machine; use
`--port` when the default is taken and `--no-open` to print the address
without opening a browser.

What you see:

- **Dashboard** — one card per parameter with a sparkline, the latest
  value, and drift/equilibration glyphs. Click a card (or press
  `Ctrl+K` and type a name) to inspect it.
- **Series / Histogram** — press `1` / `2` to switch the chart language.
  Drag to zoom, double-click to reset, hover for values. Files are read in
  input order as one dataset, with one series and one distribution.
- **Analysis** — open `Analysis` above the chart to choose a reference,
  a trend, or autocorrelation. The mean is shown initially. Cumulative and
  running averages continue across file boundaries; the running window
  defaults to about 5% of all samples. Autocorrelation correlates this same
  sequence with itself and switches the chart to lag in steps. Analysis
  choices and dashboard sort persist per browser.
- **Axis** — physical time is used when it increases throughout the combined
  sequence. If it restarts or overlaps between files, charts use a one-based
  sample index so every observation remains visible. The CSV includes that
  sample index, original time, and source file.
- **Live updates** — the header badge reads `watching` while files are
  watched, `stale` when they changed on disk (refresh or resume watching
  to reload), `paused` when watching is off, and `offline` if the
  connection drops. Data stays on screen throughout.

| Key | Action |
| --- | --- |
| `Ctrl+K` | Search parameters and modes |
| `1` / `2` | Series / histogram mode |
| `m`, `n`, `c`, `s`, `a` | Mean, median, cumulative average, autocorrelation, running average |
| `o` | Analysis or histogram options |
| `?` | This shortcut list |
| `Esc` | Close panel, then back to the dashboard |

`Data` shows the transported points as a table, and `PNG` / `CSV` download
the chart and the full-resolution data. PNG exports the chart currently shown. The
equilibration marker appears on eligible time series.

Parameters split into **observables** (energy, temperature, pressure,
density, …) and **diagnostics** (`LOOPTIME`, atom counts, and any other
zero-variance series). Diagnostics stay fully viewable, but they get no
drift badges, no equilibration verdicts, and sort after observables:
loop time tracks compute cost per step, not the simulated system, so a
step change there vetoes the segment — it never proves equilibration.

## Plot Features

The GUI and TUI offer these plot features. Web uses the shared series and
plot math for its time overlays. Its `s` shortcut shows normalized
autocorrelation by lag instead of Self-Correlation Mean:

| Feature | Time series | Histogram | TUI key |
| --- | --- | --- | --- |
| Mean | yes | yes | `m` |
| Median | yes | yes | `n` |
| Cumulative Average | yes | no | `c` |
| Self-Correlation Mean | yes | no | `s` |
| Difference (1 - 2) | yes | no | `x` |
| Running Average | yes | no | `a` |

Self-Correlation Mean in the GUI/TUI stays on the data's original scale; it
is not normalized. The web autocorrelation is mean-centered and normalized
to 1 at lag zero, calculated on all selected files as one sequence.

## Multiple Files

```bash
pqenalyzer md-01.en md-02.en md-03.en
```

In the web view, common parameters from the files form one ordered dataset. A
parameter found in only some files uses those files in input order. Shared
parameters must use the same unit.

In the GUI and TUI, Difference plotting requires exactly two files and calculates
`file 1 - file 2`. Points are matched by simulation time, simulation step, or
optimization step. PQEnalyzer does not interpolate, extrapolate, or concatenate
difference data. Raw series are hidden when Difference is enabled.

## Development

```bash
pip install -e ".[test]"
python -m pytest -m "not benchmark and not e2e"
```

For the web frontend, use Node.js 24 and build the bundled files served by
`pqenalyzer web`:

```bash
cd PQEnalyzer/web/frontend
npm ci
npm test
npm run build
```

Commit the generated files in `PQEnalyzer/web/static` when the frontend
changes. The frontend installs the shared flat mono controls from a versioned
[PQDesign release](https://github.com/MolarVerse/PQDesign/releases);
no adjacent PQSetup checkout is needed. To update the shared design, follow
the [design package guide](https://github.com/MolarVerse/PQDesign#readme),
then update the archive URL and lockfile together. Keep chart and dashboard
layout in PQEnalyzer.

Run the end-to-end suite separately:

```bash
python -m pytest -m e2e
```
