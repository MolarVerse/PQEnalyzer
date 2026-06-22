<img src="https://raw.githubusercontent.com/MolarVerse/PQEnalyzer/main/PQEnalyzer/icons/icon.png" width="200">

[![CI](https://github.com/MolarVerse/PQEnalyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/MolarVerse/PQEnalyzer/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/MolarVerse/PQEnalyzer/graph/badge.svg?token=GMLrCKFfPA)](https://codecov.io/gh/MolarVerse/PQEnalyzer)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# PQEnalyzer
Energy and parameter analyzer for PQ molecular dynamics trajectories.

## Installation
    
Install with pip:

```bash
pip install PQEnalyzer
```

## Usage

Open the GUI by passing one or more supported input files. GUI mode is the
default, so the `gui` subcommand is optional:

```bash
pqenalyzer examples/md-02.en
```

Use the terminal dashboard when you want to monitor a simulation from the
terminal:

```bash
pqenalyzer tui examples/md-02.en
```

PQEnalyzer detects PQ energy files, QMCFC energy files, and PQ box files
automatically. Energy files are detected from the matching `.info` sidecar file.
Box files are detected by the conventional `.box` suffix:

```bash
pqenalyzer pq_output.en
pqenalyzer qmcfc_output.en
pqenalyzer examples/box-01.box
```

The input format can still be forced when needed. These examples open the GUI
because GUI mode is the default:

```bash
pqenalyzer --pq pq_output.en
pqenalyzer --qmcfc qmcfc_output.en
pqenalyzer --box box_output.data
```

Use the explicit `gui` subcommand only when you prefer that spelling:

```bash
pqenalyzer gui pq_output.en
```

Multiple input files can be plotted together when they expose the same
parameters and units:

```bash
pqenalyzer md-01.en md-02.en md-03.en
```

### GUI

The GUI provides focused time-series plots, histograms, and a `Live Monitor`
dashboard. `Plot` opens a selected parameter as a time series, `Histogram` opens
the selected parameter as a distribution, and `Live Monitor` opens a raw
overview with one panel per parameter.

`Auto-Refresh` is enabled by default. It watches the loaded input files and
refreshes open plots when new simulation output is written. Disable it to pause
file watching. Plot controls apply to the selected focused plot, so different
plot windows can use different statistics and overlays at the same time.

Available statistics and overlays are:

- `Mean`
- `Median`
- `Cumulative Average`
- `Self-Correlation Mean`
- `Difference (1 - 2)`
- `Running Average`

Double-click a `Live Monitor` panel to open a focused plot for that parameter.
When `Difference (1 - 2)` is enabled, PQEnalyzer compares the first file against
the second file and hides the raw data by default so the difference is easier to
read.

### TUI

The `tui` mode opens a full-screen terminal dashboard with file status,
per-parameter latest/mean/median/min/max values, compact trends, file-change
watching, and focused terminal charts.

Use `up`/`k` and `down`/`j` to select a parameter, `enter` to open its chart,
`esc` to return to the dashboard, `q` to quit, `r` to refresh manually, and `w`
to pause or resume watching.

Focused charts use the same shared plot features as the GUI: `m` toggles mean,
`n` toggles median, `c` toggles cumulative average, `s` toggles
self-correlation mean, `x` toggles difference, and `a` toggles running average.

## Input Files

PQEnalyzer reads energy output through
[`PQAnalysis`](https://github.com/MolarVerse/PQAnalysis). Each `.en` file is
expected to have its matching `.info` sidecar file next to it. The `.info` file
is also used for automatic PQ versus QMCFC energy-file detection.

PQEnalyzer also reads PQ box files through `PQAnalysis`. Box files are expected
to contain `step x y z alpha beta gamma` columns. The plotted parameters are
`BOX-X`, `BOX-Y`, `BOX-Z`, `ALPHA`, `BETA`, `GAMMA`, and `BOX-VOLUME`.

When multiple files are supplied, their parsed parameter mappings and units must
match. Files with different columns or incompatible units are rejected before
plotting.

Difference plots require exactly two loaded files. Values are calculated as
`file 1 - file 2` on shared simulation-time values. PQEnalyzer does not
interpolate, extrapolate, or concatenate difference data.

## Development

Install the package with test dependencies:

```bash
pip install -e ".[test]"
```

Run the default test suite:

```bash
python -m pytest -q
```

Benchmark tests require `pytest-benchmark`. If it is not installed, benchmark
tests are skipped by default.
