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
  Drag to zoom, double-click to reset, hover for values. `Split` shows
  one panel per file with a shared zoom.
- **Overlays lead** — the strip under the legend toggles derived curves
  with live values (or picks a preset: Reference, Spread, Trend,
  Equilibrate, Correlate). The combined mean is on from the first paint;
  raw series recede while any overlay is active. Your overlay defaults,
  soft bounds, and dashboard sort persist per browser.
- **Live updates** — the header badge reads `watching` while files are
  watched, `stale` when they changed on disk (refresh or resume watching
  to reload), `paused` when watching is off, and `offline` if the
  connection drops. Data stays on screen throughout.

| Key | Action |
| --- | --- |
| `Ctrl+K` | Search parameters and modes |
| `1` / `2` | Series / histogram mode |
| `m`, `n`, `c`, `s`, `a` | Mean, median, cumulative/self-correlation/running average overlays |
| `x` | Difference of two files |
| `o` | Overlay and analysis options |
| `?` | This shortcut list |
| `Esc` | Close panel, then back to the dashboard |

`Data` shows the transported points as a table, `Runs` the sortable
per-file stats, and `PNG` / `CSV` download the chart and the
full-resolution data. Soft y-axis bounds in the options panel widen the
axis without clipping data.

Parameters split into **observables** (energy, temperature, pressure,
density, …) and **diagnostics** (`LOOPTIME`, atom counts, and any other
zero-variance series). Diagnostics stay fully viewable, but they get no
drift badges, no equilibration verdicts, and sort after observables:
loop time tracks compute cost per step, not the simulated system, so a
step change there vetoes the segment — it never proves equilibration.

## Plot Features

The GUI, TUI, and web interface use the same plot features (the web keys
match the TUI keys):

| Feature | Time series | Histogram | TUI key |
| --- | --- | --- | --- |
| Mean | yes | yes | `m` |
| Median | yes | yes | `n` |
| Cumulative Average | yes | no | `c` |
| Self-Correlation Mean | yes | no | `s` |
| Difference (1 - 2) | yes | no | `x` |
| Running Average | yes | no | `a` |

Self-Correlation Mean stays on the data's original scale; it is not normalized.

## Multiple Files

```bash
pqenalyzer md-01.en md-02.en md-03.en
```

Common parameters are plotted together. A parameter found in only some files
is plotted from those files. Shared parameters must use the same unit.

Difference plotting requires exactly two files and calculates
`file 1 - file 2`. Points are matched by simulation time, simulation step, or
optimization step. PQEnalyzer does not interpolate, extrapolate, or concatenate
difference data. Raw series are hidden when Difference is enabled.

## Development

```bash
pip install -e ".[test]"
python -m pytest -m "not benchmark and not e2e"
```

Run the end-to-end suite separately:

```bash
python -m pytest -m e2e
```
