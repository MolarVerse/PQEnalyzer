# Input

Parsing uses [PQAnalysis](https://github.com/MolarVerse/PQAnalysis).
Formats are detected automatically; specify a flag when detection is ambiguous.

| Output | Files | Explicit selection | Independent axis |
| --- | --- | --- | --- |
| PQ energy | `.en` and matching `.info` | `--pq` | Simulation time, with its recorded unit |
| QMCFC energy | `.en` and matching `.info` | `--qmcfc` | Simulation time or step |
| PQ cell | `.box`; rows `step x y z alpha beta gamma` | `--box` | Simulation step |
| PQ optimizer | `.opt` | `--opt` | Optimization step |

```bash
pqenalyzer web --pq simulation.en
pqenalyzer web --box simulation.box
pqenalyzer web --opt optimization.opt
```

Energy metadata supplies labels and units. Single-column PQ metadata rows
are supported. Box parameters include lengths, angles, and `BOX-VOLUME`.
Optimizer parameters include energy changes, forces, convergence states,
and limits. State `-1` means not converged, `0` disabled, and `1` converged;
the first optimizer row is the initialization snapshot. Check the PQ log
for final completion status.

## Dataset conventions

- Files are read in command-line order. A selected parameter uses only files
  containing that parameter, in that order.
- Shared parameter labels must have identical units. A mismatch is rejected;
  units are not converted.
- Finite, strictly increasing time across the complete sequence is used as
  the chart axis. A restart, overlap, or invalid time switches the axis to
  samples `1, 2, …, N`; observations retain their order.
- Continuation segments should represent the same sampling process.
  Autocorrelation pairs cross file boundaries. Analyze independent replicas
  or changed ensembles in separate sessions when interpreting correlation
  and uncertainty.

Charts may reduce the displayed point count while preserving endpoints,
bucket extrema, and representative missing-value gaps. Statistics and histogram counts use
the full finite data. Missing values appear as gaps; the different analysis
rules are listed in [Analysis](analysis.md#unavailable-estimates).

For reproducible results, retain input files and metadata, file order,
software versions, sampling interval, selected parameter, and any chosen
window or histogram settings.
