"""Browser interface over simulation readers and shared statistical methods."""

__all__ = ["create_app", "serve"]


def __getattr__(name):
    if name in __all__:
        from .app import create_app, serve

        return {"create_app": create_app, "serve": serve}[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
