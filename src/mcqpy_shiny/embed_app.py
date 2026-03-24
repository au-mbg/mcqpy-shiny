"""Browser-safe Py-Shiny app for Shinylive embeds."""

from __future__ import annotations

import base64
import json
from urllib.parse import urljoin

from shiny import App

try:
    from .shared_core import create_quiz_app
except ImportError:  # pragma: no cover - generated Shinylive snippet imports top-level files
    from shared_core import create_quiz_app

def _decode_quiz_token(token: str) -> str:
    prefix = "mcqpy:"
    if not token.startswith(prefix):
        raise ValueError("Token must start with 'mcqpy:'.")

    payload = token[len(prefix) :]
    padding = "=" * (-len(payload) % 4)
    return base64.urlsafe_b64decode(payload + padding).decode("utf-8")


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
    bundle = json.loads(raw)
    return _resolve_question_images(bundle, source)


def _answers_to_onehot(answer, n_choices: int) -> list[int]:
    onehot = [0] * n_choices
    if answer is None:
        return onehot

    selected = list(answer) if isinstance(answer, (list, tuple)) else [answer]
    for item in selected:
        if isinstance(item, int):
            index = item
        else:
            normalized = str(item).strip().upper()
            index = ord(normalized[0]) - 65

        if 0 <= index < n_choices:
            onehot[index] = 1
    return onehot


def grade_web_quiz(bundle: dict, answers: dict) -> dict:
    question_results = []
    for question in bundle.get("questions", []):
        selected_onehot = _answers_to_onehot(
            answers.get(question["qid"]), len(question["choices"])
        )
        correct = selected_onehot == question["correct_onehot"]
        points = question["point_value"] if correct else 0
        question_results.append(
            {
                "qid": question["qid"],
                "slug": question["slug"],
                "selected_onehot": selected_onehot,
                "correct": correct,
                "points": points,
                "max_points": question["point_value"],
            }
        )

    return {
        "points": sum(item["points"] for item in question_results),
        "max_points": sum(item["max_points"] for item in question_results),
        "question_results": question_results,
    }


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
        decode_token=_decode_quiz_token,
        grade_bundle=grade_web_quiz,
        missing_bundle_message="Load a quiz bundle to begin.",
        fixed_url=fixed_url,
        fixed_token=fixed_token,
        allow_manual_load=allow_manual_load,
        title=title,
        card_width=card_width,
    )
