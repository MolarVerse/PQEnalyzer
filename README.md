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

Open the GUI by passing one or more PQ `.en` energy files:

```bash
pqenalyzer pq_output.en
```

Plot in the terminal instead of opening the GUI:

```bash
pqenalyzer --no-gui pq_output.en
```

Read QMCFC output:

```bash
pqenalyzer --qmcfc pq_output.en
```

Multiple input files can be plotted together when they expose the same energy
parameters and units:

```bash
pqenalyzer md-01.en md-02.en md-03.en
```

## Input Files

PQEnalyzer reads energy output through
[`PQAnalysis`](https://github.com/MolarVerse/PQAnalysis). Each `.en` file is
expected to have its matching `.info` sidecar file next to it.

When multiple files are supplied, their parsed parameter mappings and units must
match. Files with different columns or incompatible units are rejected before
plotting.

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
