# <img src="docs/_static/pq-logo.png" alt="PQ logo" width="48"> PQEnalyzer

Inspect simulation output in your browser: time series, distributions and autocorrelation.

![Temperature series with the Analysis controls open](docs/assets/screenshots/series-analysis.png)

## Open your data

Python 3.10+. Keep each energy file's matching `.info` beside it.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install PQEnalyzer
pqenalyzer web simulation.en
```

| Do | Use |
| --- | --- |
| Choose a quantity | Dashboard tile or `Ctrl/Cmd+K` |
| Inspect or analyze | Hover the chart; open **Analysis** |
| See the distribution | **Histogram** or `2` |

Multiple files form **one dataset in command-line order**, across every chart and analysis.
Read the original files directly; no conversion is needed.

[Visual guide](https://molarverse.github.io/PQEnalyzer/getting-started.html) ·
[Methods](https://molarverse.github.io/PQEnalyzer/analysis.html) ·
[Cluster / home VPN](https://molarverse.github.io/PQEnalyzer/remote-access.html)

For a desktop window: `pqenalyzer gui simulation.en`.
Parsing uses [PQAnalysis](https://github.com/MolarVerse/PQAnalysis).
