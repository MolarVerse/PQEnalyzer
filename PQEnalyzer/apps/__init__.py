"""
Application frontends for PQEnalyzer.
"""

__all__ = ["App", "TuiApp"]


def __getattr__(name):
    if name == "App":
        from .app import App

        return App

    if name == "TuiApp":
        from .tui import TuiApp

        return TuiApp

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
