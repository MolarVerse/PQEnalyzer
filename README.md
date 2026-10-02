<img src="https://raw.githubusercontent.com/MolarVerse/PQEnalyzer/main/PQEnalyzer/icons/icon.png" alt="PQEnalyzer logo" width="200">

[![CI](https://github.com/MolarVerse/PQEnalyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/MolarVerse/PQEnalyzer/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/MolarVerse/PQEnalyzer/graph/badge.svg?token=GMLrCKFfPA)](https://codecov.io/gh/MolarVerse/PQEnalyzer)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# PQEnalyzer

Plot and monitor PQ energy, box, and optimizer output in a browser or
desktop interface.

## Install

```bash
pip install PQEnalyzer
```

## Quick Start

The desktop GUI remains the default:

```bash
pqenalyzer /path/to/simulation.en
```

Use the browser dashboard explicitly:

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

## Web

```bash
pqenalyzer web FILE [FILE ...] [--port 8766] [--no-open]
```

This starts a local-only server (loopback, default `127.0.0.1:8766`) and
opens the dashboard in your browser. Nothing leaves your machine; use
`--port` when the default is taken and `--no-open` to print the address
without opening a browser.

### Cluster access over SSH

Keep the server on the cluster loopback interface and forward it through SSH.
On a directly reachable login node, start PQEnalyzer there:

```bash
pqenalyzer web --no-open --port 8766 /path/to/simulation.en
```

Then open the tunnel from your desktop:

```bash
ssh -N -L 8766:127.0.0.1:8766 user@login.cluster
```

Open `http://127.0.0.1:8766` locally. If the analysis runs on an allocated
compute node behind a login node, start PQEnalyzer on that compute node and
use the login node as a jump host:

```bash
ssh -N -J user@login.cluster \
  -L 8766:127.0.0.1:8766 user@compute-node
```

Keep the PQEnalyzer process inside the allocation for as long as the tunnel is
needed. The server intentionally rejects non-loopback hosts; SSH provides the
authenticated, encrypted path without exposing an unauthenticated HTTP server
to the cluster network or VPN.

What you see:

- **Dashboard** — one card per parameter with a sparkline and the latest
  value. Click a card (or press
  `Ctrl+K` and type a name) to inspect it.
- **Series / Histogram** — press `1` / `2` to switch the chart language.
  Drag to zoom, double-click to reset, hover or tap for values. Focus a chart
  and use arrow keys to inspect values; `Home` / `End` jump to the edges.
  Files are read in input order as one dataset, with one series and one
  distribution.
- **Analysis** — open `Analysis` above the chart to choose a reference,
  a trend, or autocorrelation. The mean is shown initially. Cumulative and
  running averages continue across file boundaries; the running window
  defaults to about 5% of all samples. Autocorrelation correlates this same
  sequence with itself and switches the chart to lag in steps. Analysis
  choices and dashboard sort persist per browser. Correlation pairs can cross
  file boundaries; use continuous segments of the same run for this analysis.
- **Axis** — physical time is used when it increases throughout the combined
  sequence. If it restarts or overlaps between files, charts use a one-based
  sample index so every observation remains visible.
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

Hover or focus the series or histogram to inspect values and bin counts. The source
files stay in their original format; the chart can be saved as a PNG. An MSER
marker shows an estimated initial cut on eligible time series. The mean,
uncertainty, and other summary statistics still use all samples. The `±`
value is the standard error of the mean (SEM), adjusted for autocorrelation.
Estimates that overflow floating-point arithmetic are shown as unavailable.
The cut is not a verdict that the simulation has converged.

Parameters split into **observables** (energy, temperature, pressure,
density, …) and **diagnostics** (`LOOPTIME`, atom counts, and any other
zero-variance series). Diagnostics stay fully viewable, but they get no
drift measurements or MSER cuts, and sort after observables:
loop time tracks compute cost per step, not the simulated system, so a
step change there vetoes the segment — it never proves equilibration.

## Desktop GUI

Run `pqenalyzer gui FILE [FILE ...]` to use the desktop interface.

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

PQEnalyzer remembers the plot size, window dimensions, selected parameter,
auto-refresh state, and plot settings. Set `PQENALYZER_CONFIG_DIR` to override
the platform settings directory. Desktop and web use the same flat mono design
tokens.

## Plot Features

Web uses one ordered dataset for every chart and analysis:

| Feature | Time series | Histogram | Key |
| --- | --- | --- | --- |
| Mean | yes | yes | `m` |
| Median | yes | yes | `n` |
| Cumulative Average | yes | no | `c` |
| Running Average | yes | no | `a` |
| Autocorrelation | separate lag view | no | `s` |

Web autocorrelation is mean-centered and normalized to 1 at lag zero,
calculated on all selected files as one sequence.

## Multiple Files

```bash
pqenalyzer md-01.en md-02.en md-03.en
```

In the web view, common parameters from the files form one ordered dataset. A
parameter found in only some files uses those files in input order. Shared
parameters must use the same unit.

In the desktop GUI, Difference plotting requires exactly two files and calculates
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
then update the archive URL and lockfile together. Copy that package's
`tokens.json` to `PQEnalyzer/design/tokens.json`; CI checks they match.
Desktop colors derive from this packaged snapshot. Keep chart and
dashboard layout in PQEnalyzer.

Run the end-to-end suite separately:

```bash
python -m playwright install chromium
python -m pytest -m e2e
```

The browser test checks parameter selection, keyboard chart inspection,
autocorrelation, histogram bins, PNG download, and stale-file refresh.
CI rebuilds the frontend and checks that `PQEnalyzer/web/static` matches the
source. A release tag must point to the current `main` commit; the tag job
repeats the tests, builds the distribution, and installs the wheel before
publishing it.
