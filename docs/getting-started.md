# Getting started

## Install

Python 3.10 or newer is required. The web interface works on a server without
a graphical display.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install PQEnalyzer
pqenalyzer web /path/to/simulation.en
```

Keep `/path/to/simulation.info` beside the energy file. The browser opens
at <http://127.0.0.1:8766>. Choose another port with `--port 8767` if needed.
Use `--no-open` on a server and follow [Remote access](remote-access.md).

## Inspect

1. Select a parameter on the dashboard, or search with `Ctrl+K` (`Cmd+K` on macOS).
2. Check the quantity, unit, axis, and range. Hover or focus the chart to
   inspect values; drag to zoom and double-click to reset.
3. Switch to Histogram to inspect the distribution. Open Analysis in Series
   to choose a reference, an average, or autocorrelation.
4. Interpret the estimates using [Analysis](analysis.md). Review sampling
   and the physical model before drawing a scientific conclusion.

Files are watched for changes. Pausing keeps the current data visible;
resuming or refreshing reloads changed files. The connection indicator shows
`offline` if the server cannot be reached. Save chart images as PNG;
the source data remains in its original format.

| Key | Action |
| --- | --- |
| `Ctrl+K` / `Cmd+K` | Search parameters and chart modes |
| `1` / `2` | Series / Histogram |
| `m` / `n` | Mean / median |
| `c` / `a` / `s` | Cumulative / running average / autocorrelation |
| `o` | Open analysis or histogram options |
| Left/Right arrows, `Home`, `End` | Inspect values in a focused chart |
| `?` / `Esc` | Shortcut help / close the current panel |

## Several files

Supply continuation files in acquisition order:

```bash
pqenalyzer web md-01.en md-02.en
```

Every browser chart and analysis uses the concatenated sequence. File
boundaries do not restart averages or autocorrelation. See
[dataset conventions](input.md#dataset-conventions) before combining runs.

## Desktop interface

```bash
pqenalyzer gui /path/to/simulation.en
```

Omitting `gui` also opens this interface. `Plot`, `Histogram`, and
`Live Monitor` open separate windows; double-click a monitor panel to focus
it. Auto-refresh watches the loaded files and uses polling if native watching
is unavailable. Resize windows to refit plots; `f` fits the monitor grid.

Desktop Difference requires exactly two files and computes file 1 minus
file 2 at matching time or step values. It does not interpolate or extrapolate.
Desktop settings are stored locally; `PQENALYZER_CONFIG_DIR` overrides
the settings directory.
