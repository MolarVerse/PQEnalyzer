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

Open the GUI by passing one or more supported input files to the `gui` mode.
PQEnalyzer detects PQ energy, QMCFC energy, and box files automatically:

```bash
pqenalyzer gui pq_output.en
```

Open the terminal interface for simulation monitoring:

```bash
pqenalyzer tui pq_output.en
```

Read QMCFC output:

```bash
pqenalyzer gui --qmcfc pq_output.en
```

Force PQ energy parsing:

```bash
pqenalyzer gui --pq pq_output.en
```

Plot PQ box parameters from a `.box` file:

```bash
pqenalyzer gui examples/box-01.box
```

Use `--box` when a box file does not use the conventional `.box` suffix.

Multiple input files can be plotted together when they expose the same
parameters and units:

```bash
pqenalyzer gui md-01.en md-02.en md-03.en
```

The `tui` mode opens a full-screen terminal dashboard with file status,
per-parameter latest/mean/min/max values, compact trends, file-change watching,
and focused terminal charts. Use `up`/`j` and `down`/`k` to select a parameter,
`enter` to open its chart, `esc` to return to the dashboard, `q` to quit, `r`
to refresh manually, and `w` to pause or resume watching. Focused charts include
statistics overlays: `m` toggles mean, `n` toggles median, `c` toggles
cumulative average, `s` toggles self-correlation mean, `x` toggles difference,
and `a` toggles running average.

In GUI mode, `Live Monitor` opens a raw overview with one panel per parameter.
`Auto-Refresh` watches the loaded file for changes and redraws open plots when
new simulation output is written. Disable `Auto-Refresh` to pause file
watching. Double-click a monitor panel to open a focused plot for that
parameter. Statistics and time-series overlay controls apply to the selected
focused plot, while the monitor stays raw for simulation monitoring.

## Input Files

PQEnalyzer reads energy output through
[`PQAnalysis`](https://github.com/MolarVerse/PQAnalysis). Each `.en` file is
expected to have its matching `.info` sidecar file next to it.

PQEnalyzer also reads PQ box files through `PQAnalysis`. Box files are expected
to contain `step x y z alpha beta gamma` columns. The plotted parameters are
`BOX-X`, `BOX-Y`, `BOX-Z`, `ALPHA`, `BETA`, `GAMMA`, and `BOX-VOLUME`.

When multiple files are supplied, their parsed parameter mappings and units must
match. Files with different columns or incompatible units are rejected before
plotting.

Difference plots additionally require both files to have the same
simulation-time axis.

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
