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

Open the GUI by passing one or more supported input files. PQEnalyzer detects
PQ energy, QMCFC energy, and box files automatically:

```bash
pqenalyzer pq_output.en
```

Plot in the terminal instead of opening the GUI:

```bash
pqenalyzer --no-gui pq_output.en
```

Plot one parameter in terminal mode without prompts:

```bash
pqenalyzer --no-gui --plot TEMPERATURE pq_output.en
```

Print the detected files, row counts, and available parameters:

```bash
pqenalyzer --no-gui --summary pq_output.en
```

Plot the difference between two aligned example files without prompts:

```bash
pqenalyzer --no-gui --plot TEMPERATURE --diff examples/diff-run-a.en examples/diff-run-b.en
```

Read QMCFC output:

```bash
pqenalyzer --qmcfc pq_output.en
```

Force PQ energy parsing:

```bash
pqenalyzer --pq pq_output.en
```

Plot PQ box parameters from a `.box` file:

```bash
pqenalyzer examples/box-01.box
```

Use `--box` when a box file does not use the conventional `.box` suffix.

## Shell Completion

PQEnalyzer uses `argcomplete` for shell completion and can print installable
completion scripts.

Package managers can install the generated scripts into their shell completion
directories so users get completion after installing the package.

Enable bash completion for the current shell session:

```bash
eval "$(pqenalyzer completion bash)"
```

Enable zsh completion for the current shell session:

```bash
eval "$(pqenalyzer completion zsh)"
```

Install fish completion persistently:

```bash
mkdir -p ~/.config/fish/completions
pqenalyzer completion fish > ~/.config/fish/completions/pqenalyzer.fish
```

To enable automatic argcomplete discovery for installed Python CLIs, run this
once and restart the shell:

```bash
activate-global-python-argcomplete --user -y
```

After completion is active, `--plot` completes common PQ and box parameters.
When input files are already present on the command line, it completes the
parameters detected from those files.

Multiple input files can be plotted together when they expose the same
parameters and units:

```bash
pqenalyzer md-01.en md-02.en md-03.en
```

For two aligned runs, the GUI and terminal mode can plot a pointwise difference
as the first input file minus the second input file.

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
