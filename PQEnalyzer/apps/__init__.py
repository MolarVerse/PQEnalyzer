"""
This module includes the App class that is used to run the application.
"""

__all__ = ["App", "TermApp"]


def __getattr__(name):
    if name == "App":
        from .app import App

        return App

    if name == "TermApp":
        from .termapp import TermApp

        return TermApp

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
