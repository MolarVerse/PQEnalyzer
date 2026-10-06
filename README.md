# PQEnalyzer

Inspect PQ and QMCFC energy output, PQ cell data, and optimizer output in a
browser or desktop window. Parsing uses
[PQAnalysis](https://github.com/MolarVerse/PQAnalysis).

## Install and open

Python 3.10 or newer is required. The web interface is included.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install PQEnalyzer
pqenalyzer web /path/to/simulation.en
```

Keep the matching `.info` file beside each energy file. Select a parameter,
inspect its series, then switch to Histogram or choose an analysis. Hover or
focus the chart for values; no data conversion is needed.

| Input | Browser dataset |
| --- | --- |
| One file | Its observations and units |
| Several files | One sequence in command-line order; shared units must match |
| Restarted or overlapping time | One-based sample axis, retaining every observation |

Use `pqenalyzer gui FILE` for the desktop interface; `pqenalyzer FILE` also
opens the desktop interface.

## Manual

- [First analysis](https://molarverse.github.io/PQEnalyzer/getting-started.html)
- [Input, units, and dataset order](https://molarverse.github.io/PQEnalyzer/input.html)
- [Charts and statistical methods](https://molarverse.github.io/PQEnalyzer/analysis.html)
- [Cluster access through SSH and VPN, including from home](https://molarverse.github.io/PQEnalyzer/remote-access.html)
- [Development and reproducible figures](https://molarverse.github.io/PQEnalyzer/development.html)

The [manual](https://molarverse.github.io/PQEnalyzer/) defines the reported SEM,
autocorrelation, and MSER cut. These estimates support scientific review;
they do not establish convergence or sufficient sampling.
