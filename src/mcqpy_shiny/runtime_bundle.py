"""Runtime-safe quiz bundle helpers used by mcqpy-shiny.

NOTE ABOUT DUPLICATION
This file intentionally duplicates a small browser-safe subset of logic that also
exists in `mcqpy.web`. The duplication is temporary and exists so `mcqpy-shiny`
can run in Shinylive/Pyodide without pulling in the full `mcqpy` dependency tree.

If/when this is cleaned up, the intended refactor is to extract these shared
bundle/token/grading helpers into a tiny dedicated package used by both
`mcqpy` and `mcqpy-shiny`.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return list(value)


def _as_dict(value: Any) -> dict[Any, Any]:
    if value is None:
        return {}
    return dict(value)


def normalize_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    metadata = _as_dict(bundle.get("metadata"))
    questions = []
    for question in bundle.get("questions", []):
        code_blocks = []
        for block in question.get("code_blocks", []):
            code_blocks.append(
                {
                    "code": block.get("code", ""),
                    "language": block.get("language"),
                }
            )

        questions.append(
            {
                "qid": question["qid"],
                "slug": question["slug"],
                "text": question["text"],
                "choices": list(question["choices"]),
                "question_type": question["question_type"],
                "point_value": int(question["point_value"]),
                "correct_onehot": [int(item) for item in question["correct_onehot"]],
                "images": _as_list(question.get("images")),
                "image_captions": _as_dict(question.get("image_captions")),
                "code_blocks": code_blocks,
                "has_explanation": bool(question.get("has_explanation", False)),
            }
        )

    return {
        "schema_version": bundle.get("schema_version", "1.0"),
        "metadata": {
            "title": metadata.get("title", ""),
            "description": metadata.get("description"),
            "source": metadata.get("source"),
        },
        "questions": questions,
    }


def load_bundle_json(raw: str) -> dict[str, Any]:
    return normalize_bundle(json.loads(raw))


def load_bundle_file(path: str | Path) -> dict[str, Any]:
    return load_bundle_json(Path(path).read_text(encoding="utf-8"))


def encode_quiz_token(url: str) -> str:
    payload = base64.urlsafe_b64encode(url.encode("utf-8")).decode("ascii").rstrip("=")
    return f"mcqpy:{payload}"


def decode_quiz_token(token: str) -> str:
    prefix = "mcqpy:"
    if not token.startswith(prefix):
        raise ValueError("Token must start with 'mcqpy:'.")

    payload = token[len(prefix) :]
    padding = "=" * (-len(payload) % 4)
    return base64.urlsafe_b64decode(payload + padding).decode("utf-8")


def _answers_to_onehot(
    answer: str | int | list[str] | list[int] | tuple[str, ...] | tuple[int, ...] | None,
    n_choices: int,
) -> list[int]:
    onehot = [0] * n_choices
    if answer is None:
        return onehot

    selected = list(answer) if isinstance(answer, (list, tuple)) else [answer]
    for item in selected:
        if isinstance(item, int):
            index = item
        else:
            normalized = str(item).strip().upper()
            if not normalized:
                continue
            index = ord(normalized[0]) - 65

        if 0 <= index < n_choices:
            onehot[index] = 1
    return onehot


def grade_web_quiz(bundle: dict[str, Any], answers: dict[str, Any]) -> dict[str, Any]:
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
