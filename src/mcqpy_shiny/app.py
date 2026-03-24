"""Py-Shiny app for taking mcqpy web quizzes."""

from __future__ import annotations

from shiny import App

from mcqpy.web import WebQuizBundle, decode_quiz_token, grade_web_quiz

try:
    from .loader import load_bundle
    from .shared_core import create_quiz_app
except ImportError:  # pragma: no cover - direct `shiny run path/to/app.py`
    from loader import load_bundle
    from shared_core import create_quiz_app


def _normalize_question(question) -> dict:
    return {
        "qid": question.qid,
        "slug": question.slug,
        "text": question.text,
        "choices": list(question.choices),
        "question_type": question.question_type,
        "point_value": question.point_value,
        "correct_onehot": list(question.correct_onehot),
        "images": list(question.images),
        "image_captions": dict(question.image_captions),
        "code_blocks": [block.model_dump() for block in question.code_blocks],
    }


def _normalize_bundle(bundle: WebQuizBundle) -> dict:
    return {
        "metadata": bundle.metadata.model_dump(),
        "questions": [_normalize_question(question) for question in bundle.questions],
    }


def _normalize_result(result) -> dict:
    return {
        "points": result.points,
        "max_points": result.max_points,
        "question_results": [
            {
                "qid": item.qid,
                "slug": item.slug,
                "selected_onehot": list(item.selected_onehot),
                "correct": item.correct,
                "points": item.points,
                "max_points": item.max_points,
            }
            for item in result.question_results
        ],
    }


async def _load_bundle(source: str) -> dict:
    return _normalize_bundle(await load_bundle(source))


def _grade_bundle(bundle: dict, answers: dict) -> dict:
    bundle_model = WebQuizBundle.model_validate(bundle)
    return _normalize_result(grade_web_quiz(bundle_model, answers))


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
