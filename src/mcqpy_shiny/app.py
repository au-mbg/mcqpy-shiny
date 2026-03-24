"""Py-Shiny app for taking mcqpy web quizzes."""

from __future__ import annotations

from shiny import App

try:
    from .loader import load_bundle
    from .runtime_bundle import decode_quiz_token, grade_web_quiz
    from .shared_core import create_quiz_app
except ImportError:  # pragma: no cover - direct `shiny run path/to/app.py`
    from loader import load_bundle
    from runtime_bundle import decode_quiz_token, grade_web_quiz
    from shared_core import create_quiz_app

async def _load_bundle(source: str) -> dict:
    return await load_bundle(source)


def _grade_bundle(bundle: dict, answers: dict) -> dict:
    return grade_web_quiz(bundle, answers)


def create_app(
    *,
    fixed_url: str | None = None,
    fixed_token: str | None = None,
    allow_manual_load: bool = True,
    title: str = "MCQPy Quiz",
    card_width: str = "900px",
) -> App:
    return create_quiz_app(
        load_bundle=_load_bundle,
        decode_token=decode_quiz_token,
        grade_bundle=_grade_bundle,
        missing_bundle_message="Load a quiz bundle to begin. Bundles are exported with `mcqpy export web`.",
        fixed_url=fixed_url,
        fixed_token=fixed_token,
        allow_manual_load=allow_manual_load,
        title=title,
        card_width=card_width,
    )


app = create_app()


def run_app() -> None:
    """Entry point for `mcqpy-shiny`."""

    from shiny import run_app

    run_app(app)
