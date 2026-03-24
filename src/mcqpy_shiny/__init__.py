"""Py-Shiny app factory for mcqpy web bundles."""

from __future__ import annotations

from typing import Any


def create_app(*args: Any, **kwargs: Any):
    from .app import create_app as _create_app

    return _create_app(*args, **kwargs)


def __getattr__(name: str):
    if name == "app":
        from .app import app as _app

        return _app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["app", "create_app"]
