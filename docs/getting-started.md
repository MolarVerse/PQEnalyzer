# Use the GUI

| Interface | Command |
| --- | --- |
| [Desktop (Tkinter) — default](#desktop-default) | `pqenalyzer simulation.en` |
| [Browser](#browser) | `pqenalyzer web simulation.en` |

## Desktop (default)

```bash
pqenalyzer simulation.en
```

`pqenalyzer gui simulation.en` is equivalent. A local graphical display is required.

```{figure} assets/screenshots/desktop.png
:width: 360px
:alt: Tkinter temperature selector, statistics, time-series overlays and plot buttons

Choose Parameter, select any overlays, then open a plot window.
```

| Control | Action |
| --- | --- |
| **Parameter** | Choose the quantity to plot |
| **Plot** / **Histogram** | Open a separate time-series or distribution window |
| **Statistics** / **Time-series overlays** | Choose guides before plotting, or click an existing plot to edit it |
| **Live Monitor** | Open the grid; double-click a panel to focus it; `f` fits the grid |
| **Auto-Refresh** | Reread the last input file and update open plots |
| **Plot Size** | Scale plot text; drag a plot window's edge to resize it |

Desktop raw series and KDEs keep files separate; statistic overlays pool the
files. **Difference (1 − 2)** subtracts file 2 from file 1 at matching time or
step values, with exactly two files and no interpolation.

## Browser

```bash
pqenalyzer web simulation.en
```

### 1. Choose a quantity

Click a dashboard tile, or search with `Ctrl+K` (`Cmd+K` on macOS).

![Dashboard with one tile per observable and units beside each name](assets/screenshots/dashboard.png)

### 2. Inspect the series

Hover for values. Drag to zoom; double-click to reset.
Open **Analysis** to select a mean, average or autocorrelation.

![Temperature series and the Analysis panel with reference, trend and correlation choices](assets/screenshots/series-analysis.png)

**Mean (all)** includes every finite value. Its `±` is the estimated standard error.
**Autocorrelation** shows the sequence correlated with itself, against lag in samples.
The MSER cut is a proposed transient boundary; summaries still use all data.
[Method definitions](analysis.md).

### 3. Inspect the distribution

Choose **Histogram**. **Options** controls bins, reference lines and KDE.

![Temperature histogram with bin and density options open](assets/screenshots/histogram.png)

| Control | Action |
| --- | --- |
| **All** / `Esc` | Return to the dashboard; first `Esc` leaves an active input or panel |
| **Series** / **Histogram**, or `1` / `2` | Change chart type |
| **Analysis** / **Options**, or `o` | Show chart controls |
| Left/Right arrows, `Home`, `End` | Inspect a focused chart without a mouse |
| Watching indicator | Pause or resume file updates |
| Download icon (Series) | Save the chart as PNG |
| `?` | Show all shortcuts |

## Install and open

Python 3.10+. In a new environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install PQEnalyzer
```

Keep `simulation.info` beside `simulation.en`. Browser mode opens
<http://127.0.0.1:8766>. In the browser, multiple files form one dataset in command-line order:

```bash
pqenalyzer web md-01.en md-02.en
```

No file conversion is needed.

## Server startup

```bash
pqenalyzer web --no-open simulation.en
```

Once the server is ready:

```text
PQEnalyzer  Web
Data   5,000 rows / 1 file
Open   http://127.0.0.1:8766
Stop   Ctrl+C
```

Open the printed URL; `--no-open` skips opening a browser automatically.
Keep the terminal running. Press `Ctrl+C` to stop the server.
The heading and URL use the PQ accent in a terminal. `NO_COLOR=1` disables
color; redirected output and `TERM=dumb` are plain.
Use `--port 8767` for a different port. On a cluster or home VPN, use the
[SSH / VPN guide](remote-access.md).
