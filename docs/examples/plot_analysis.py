"""Regenerate the manual figure from the repository's energy examples."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from PQEnalyzer.energy_access import concatenate_series
from PQEnalyzer.readers import create_reader
from PQEnalyzer.statistics import Statistic


ROOT = Path(__file__).resolve().parents[2]
TOKENS = json.loads((ROOT / "PQEnalyzer/design/tokens.json").read_text())
COLOUR = TOKENS["color"]
plt.rcParams.update({
    "font.family": "DejaVu Sans Mono",
    "font.size": 10,
    "text.color": COLOUR["ink"],
    "axes.labelcolor": COLOUR["ink"],
    "axes.edgecolor": COLOUR["border-strong"],
    "xtick.color": COLOUR["ink-soft"],
    "ytick.color": COLOUR["ink-soft"],
    "svg.hashsalt": "pqenalyzer-temperature-analysis",
})

reader = create_reader([str(ROOT / "examples" / name)
                        for name in ("md-01.en", "md-02.en")])
series = concatenate_series(reader.energies, "TEMPERATURE")
time, values = series.time, series.values
if not (np.isfinite(time).all() and (np.diff(time) > 0).all()):
    time = np.arange(1, values.size + 1)
    xlabel = "Sample"
else:
    xlabel = f"Simulation time ({reader.energies[0].simulation_time_unit})"
cumulative_time, cumulative = Statistic.cumulative_average_values(time, values)
window_time, running = Statistic.running_average_values(time, values, 500)
lags, correlation = Statistic.autocorrelation_values(values, max_lag=500)

figure, axes = plt.subplots(3, 1, figsize=(9, 9), layout="constrained")
axes[0].plot(time, values, color=COLOUR["border-strong"], linewidth=0.5,
             label="Observations", rasterized=True)
axes[0].plot(cumulative_time, cumulative, color=COLOUR["accent"],
             label="Cumulative mean")
axes[0].plot(window_time, running, color=TOKENS["code"]["file"],
             label="Running mean (w = 500)")
axes[0].set(xlabel=xlabel, ylabel=f"Temperature ({series.unit})", title="Series")
axes[0].legend(fontsize=9, frameon=False, ncol=3, loc="lower right")
finite = values[np.isfinite(values)]
axes[1].hist(finite, bins="auto", color=COLOUR["accent"], linewidth=0.5,
             edgecolor=COLOUR["surface"])
axes[1].set(xlabel=f"Temperature ({series.unit})", ylabel="Count", title="Histogram")
axes[2].plot(lags, correlation, color=COLOUR["accent"])
axes[2].axhline(0, color=COLOUR["border-strong"], linewidth=0.75)
axes[2].set(xlabel="Lag (samples)", ylabel="Normalized correlation", title="Autocorrelation")
for axis in axes:
    axis.spines[["top", "right"]].set_visible(False)
    axis.grid(axis="y", color=COLOUR["border"], linewidth=0.5)
    axis.set_axisbelow(True)
output = ROOT / "docs/_static/temperature-analysis.svg"
figure.savefig(output, metadata={"Date": None})
output.write_text("\n".join(line.rstrip() for line in output.read_text().splitlines()) + "\n")
plt.close(figure)
