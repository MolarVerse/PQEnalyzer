# PQEnalyzer

PQEnalyzer reads simulation output where it is stored and presents one
ordered dataset in a browser. Inspect observables, distributions, and
correlation before deciding whether a run needs more sampling.

| Task | Guide |
| --- | --- |
| Open the first dataset | [Getting started](getting-started.md) |
| Check formats, units, and file order | [Input](input.md) |
| Interpret charts and uncertainty | [Analysis](analysis.md) |
| Work on a server from your desktop | [SSH and VPN](remote-access.md) |
| Build the interface or reproduce figures | [Development](development.md) |

```{figure} _static/temperature-analysis.svg
:alt: One temperature sequence as a series with averages, a count histogram, and normalized autocorrelation by lag.

Three views of the 10,000 temperature observations in the repository's
`examples/md-01.en` and `examples/md-02.en`, in that order. Definitions are in
[Analysis](analysis.md); the generating command is in
[Development](development.md#reproduce-the-figure).
```

```{toctree}
:hidden:

getting-started
input
analysis
remote-access
development
```
