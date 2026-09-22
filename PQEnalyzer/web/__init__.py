"""
Web front end for PQEnalyzer (LOCAL-ONLY preview, not committed upstream).

``python -m PQEnalyzer web`` / ``pqenalyzer web`` serves a browser version of
the desktop GUI: parameter list, time-series chart with the shared overlay
math, histogram, sparkline dashboard, and CSV export. Styling follows the
``@molarverse/pq-design`` flat-mono language; data comes from the same
readers, ``energy_access`` helpers, and ``plots.features`` evaluators as the
desktop and terminal front ends, so numbers match everywhere.
"""

__all__ = ["create_app", "serve"]


def __getattr__(name):
    if name in __all__:
        from .app import create_app, serve

        return {"create_app": create_app, "serve": serve}[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
