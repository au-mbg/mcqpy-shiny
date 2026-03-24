"""Bundle loading helpers for local and static-hosted quizzes."""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import urlopen

from mcqpy.web import WebQuizBundle


def _is_remote_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def _path_to_data_url(path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(path.name)
    if mime_type is None:
        mime_type = "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _resolve_question_images(bundle: WebQuizBundle, source: str) -> WebQuizBundle:
    updated_questions = []
    for question in bundle.questions:
        updated_questions.append(
            question.model_copy(
                update={
                    "images": [
                        image if _is_remote_url(image) else urljoin(source, image)
                        for image in question.images
                    ]
                }
            )
        )
    return bundle.model_copy(update={"questions": updated_questions})


def _resolve_local_question_images(bundle: WebQuizBundle, bundle_dir: Path) -> WebQuizBundle:
    updated_questions = []
    for question in bundle.questions:
        images = []
        for image in question.images:
            image_path = Path(image)
            if image_path.is_absolute():
                resolved = image_path
            else:
                resolved = (bundle_dir / image_path).resolve()

            images.append(_path_to_data_url(resolved))

        updated_questions.append(question.model_copy(update={"images": images}))

    return bundle.model_copy(update={"questions": updated_questions})


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


def load_bundle_from_path(path: str | Path) -> WebQuizBundle:
    bundle_path = Path(path).resolve()
    bundle = WebQuizBundle.load_from_file(bundle_path)
    return _resolve_local_question_images(bundle, bundle_path.parent)


async def load_bundle_from_url(url: str) -> WebQuizBundle:
    raw = await _fetch_text(url)
    bundle = WebQuizBundle.model_validate_json(raw)
    return _resolve_question_images(bundle, url)


async def load_bundle(source: str) -> WebQuizBundle:
    if _is_remote_url(source):
        return await load_bundle_from_url(source)
    return load_bundle_from_path(source)
