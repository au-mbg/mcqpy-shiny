"""Browser-safe Py-Shiny app for Shinylive embeds."""

from __future__ import annotations

from urllib.parse import urljoin

from shiny import App

try:
    from .runtime_bundle import decode_quiz_token, grade_web_quiz, load_bundle_json
    from .shared_core import create_quiz_app
except ImportError:  # pragma: no cover - generated Shinylive snippet imports top-level files
    from runtime_bundle import decode_quiz_token, grade_web_quiz, load_bundle_json
    from shared_core import create_quiz_app


def _resolve_question_images(bundle: dict, source: str) -> dict:
    updated_questions = []
    for question in bundle.get("questions", []):
        updated = dict(question)
        updated["images"] = [
            image if image.startswith(("http://", "https://", "data:")) else urljoin(source, image)
            for image in question.get("images", [])
        ]
        updated_questions.append(updated)

    updated_bundle = dict(bundle)
    updated_bundle["questions"] = updated_questions
    return updated_bundle


async def _fetch_text(url: str) -> str:
    try:
        from pyodide.http import pyfetch  # type: ignore
    except ImportError:  # pragma: no cover
        from urllib.request import urlopen

        with urlopen(url) as response:  # noqa: S310
            return response.read().decode("utf-8")

    response = await pyfetch(url)
    if not response.ok:
        raise ValueError(f"Failed to load quiz bundle from {url}")
    return await response.string()


async def load_bundle(source: str) -> dict:
    raw = await _fetch_text(source)
    bundle = load_bundle_json(raw)
    return _resolve_question_images(bundle, source)


def create_app(
    *,
    fixed_url: str | None = None,
    fixed_token: str | None = None,
    allow_manual_load: bool = True,
    title: str = "MCQPy Quiz",
    card_width: str = "900px",
) -> App:
    return create_quiz_app(
        load_bundle=load_bundle,
        decode_token=decode_quiz_token,
        grade_bundle=grade_web_quiz,
        missing_bundle_message="Load a quiz bundle to begin.",
        fixed_url=fixed_url,
        fixed_token=fixed_token,
        allow_manual_load=allow_manual_load,
        title=title,
        card_width=card_width,
    )
