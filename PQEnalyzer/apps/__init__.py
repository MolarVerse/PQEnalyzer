"""
Application frontends for PQEnalyzer.
"""

__all__ = ["App"]


def __getattr__(name):
    if name == "App":
        from .app import App

        return App

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
