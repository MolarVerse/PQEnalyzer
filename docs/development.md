# Development

## Build and check

From a repository checkout:

```bash
python -m pip install -e ".[test,docs]"
python -m pytest -m "not benchmark and not e2e"
python -m sphinx -W --keep-going -b html docs docs/_build/html
```

The frontend uses Node.js 24. Rebuild the bundled assets after a source change:

```bash
cd PQEnalyzer/web/frontend
npm ci
npm test
npm run build
```

Commit `PQEnalyzer/web/static` with frontend changes. CI checks that the
bundle matches its source and the installed PQDesign package.
For browser and desktop smoke tests, install Chromium first:

```bash
python -m playwright install chromium
python -m pytest -m e2e
```

On headless Linux, desktop tests require Xvfb; CI uses
`xvfb-run -a python -m pytest -m e2e`.

## Source ownership

| Layer | Location | Responsibility |
| --- | --- | --- |
| Parsing | `PQAnalysis`; `PQEnalyzer/readers` | Read output and validate compatible units |
| Dataset access | `PQEnalyzer/energy_access.py` | Resolve parameters and concatenate selected files |
| Methods | `PQEnalyzer/statistics`, `PQEnalyzer/plots` | Numeric calculations and plot conventions |
| Web server | `PQEnalyzer/web` | Shape JSON, watch files, and serve the bundled interface |
| Browser | `PQEnalyzer/web/frontend` | Interaction and chart rendering |
| Terminal adapter | `PQEnalyzer/_terminal.py` | App labels, dataset summaries and lifecycle events |

Extend PQAnalysis parsing and reuse the method layer before adding another
reader or calculation. Scientific changes need a reproducible input and a
check against an independent calculation; interface changes need a browser
check of the affected interaction.

`PQEnalyzer/_design_terminal.py` is vendored byte for byte from PQDesign's
`python/pq_terminal.py`. CI and release builds compare it with the released
package. PQDesign owns renderer branch coverage; this repository tests the
PQEnalyzer adapter, values and application lifecycle.

## Reproduce the figure

From the repository root, using the installed package and included example data:

```bash
python docs/examples/plot_analysis.py
```

This regenerates `docs/_static/temperature-analysis.svg` from the two energy
files and their `.info` files. It uses the same dataset and statistic APIs as
the web application. The example files illustrate the methods; apparent
stability does not validate a scientific simulation.

The manual uses [PQDesign](https://molarverse.github.io/PQDesign/) tokens and
its shared Furo stylesheet. Local copies and provenance are in `docs/_static`;
builds do not require a neighbouring checkout.
