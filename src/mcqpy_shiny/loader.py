"""Bundle loading helpers for local and static-hosted quizzes."""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import urlopen

try:
    from .runtime_bundle import load_bundle_file, load_bundle_json
except ImportError:  # pragma: no cover - direct `shiny run path/to/app.py`
    from runtime_bundle import load_bundle_file, load_bundle_json


def _is_remote_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def _path_to_data_url(path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(path.name)
    if mime_type is None:
        mime_type = "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _resolve_question_images(bundle: dict, source: str) -> dict:
    updated_questions = []
    for question in bundle["questions"]:
        updated = dict(question)
        updated["images"] = [
            image if _is_remote_url(image) else urljoin(source, image)
            for image in question.get("images", [])
        ]
        updated_questions.append(updated)
    updated_bundle = dict(bundle)
    updated_bundle["questions"] = updated_questions
    return updated_bundle


def _resolve_local_question_images(bundle: dict, bundle_dir: Path) -> dict:
    updated_questions = []
    for question in bundle["questions"]:
        images = []
        for image in question.get("images", []):
            image_path = Path(image)
            if image_path.is_absolute():
                resolved = image_path
            else:
                resolved = (bundle_dir / image_path).resolve()

            images.append(_path_to_data_url(resolved))

        updated = dict(question)
        updated["images"] = images
        updated_questions.append(updated)

    updated_bundle = dict(bundle)
    updated_bundle["questions"] = updated_questions
    return updated_bundle


async def _fetch_text(url: str) -> str:
    try:
        from pyodide.http import pyfetch  # type: ignore
    except ImportError:
        with urlopen(url) as response:  # noqa: S310
            return response.read().decode("utf-8")

    response = await pyfetch(url)
    if not response.ok:
        raise ValueError(f"Failed to load quiz bundle from {url}")
    return await response.string()


def load_bundle_from_path(path: str | Path) -> dict:
    bundle_path = Path(path).resolve()
    bundle = load_bundle_file(bundle_path)
    return _resolve_local_question_images(bundle, bundle_path.parent)


async def load_bundle_from_url(url: str) -> dict:
    raw = await _fetch_text(url)
    bundle = load_bundle_json(raw)
    return _resolve_question_images(bundle, url)


async def load_bundle(source: str) -> dict:
    if _is_remote_url(source):
        return await load_bundle_from_url(source)
    return load_bundle_from_path(source)
