# PQEnalyzer

Inspect simulation output on the desktop or in your browser.

**Desktop (Tkinter) is the default.** The `web` command starts the browser interface.

| Interface | Command |
| --- | --- |
| [Desktop — default](getting-started.md#desktop-default) | `pqenalyzer simulation.en` |
| [Browser](getting-started.md#browser) | `pqenalyzer web simulation.en` |

```{figure} assets/screenshots/desktop.png
:width: 320px
:alt: Default Tkinter window with parameter, statistics, refresh and plot controls

Desktop controls. Plot, Histogram and Live Monitor open separate windows.
```

![Browser temperature series with its mean and the Analysis controls open](assets/screenshots/series-analysis.png)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install PQEnalyzer
```

| Start here | Reference |
| --- | --- |
| [Use the GUI](getting-started.md) | [Charts and uncertainty](analysis.md) |
| [Open files](input.md) | [Formats, units and dataset order](input.md#dataset-conventions) |
| [Connect from a cluster or home VPN](remote-access.md) | [Development](development.md) |

```{toctree}
:hidden:

getting-started
input
analysis
remote-access
development
```
