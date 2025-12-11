"""OCR helper to turn exam images into JSON questions/answers.

Usage:
    python ocr_to_json.py images_dir --output questions.json

Dependencies:
- Pillow
- pytesseract (requires the Tesseract OCR engine installed and available on PATH)
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Iterable, List, Tuple

from PIL import Image
import pytesseract
from pytesseract import TesseractNotFoundError

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif"}


def collect_image_paths(inputs: Iterable[str]) -> List[Path]:
    paths: List[Path] = []
    for raw in inputs:
        path = Path(raw)
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            paths.append(path)
        elif path.is_dir():
            for image_path in sorted(path.rglob("*")):
                if image_path.suffix.lower() in IMAGE_EXTENSIONS:
                    paths.append(image_path)
        else:
            for image_path in sorted(Path().glob(raw)):
                if image_path.suffix.lower() in IMAGE_EXTENSIONS:
                    paths.append(image_path)
    return paths


def split_question_answer(text: str) -> Tuple[str, str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "", ""

    lower_lines = [line.lower() for line in lines]
    answer_markers = ("answer:", "ans:", "a:")

    for idx, lower_line in enumerate(lower_lines):
        for marker in answer_markers:
            if lower_line.startswith(marker):
                answer_first_line = lines[idx][len(marker):].strip()
                answer_parts = []
                if answer_first_line:
                    answer_parts.append(answer_first_line)
                answer_parts.extend(lines[idx + 1 :])
                question_text = " ".join(lines[:idx]).strip()
                return question_text, " ".join(answer_parts).strip()

    if len(lines) > 1:
        question_line = lines[0]
        for marker in ("question:", "q:", "q."):
            if question_line.lower().startswith(marker):
                trimmed = question_line[len(marker) :].strip()
                question_line = trimmed or question_line
                break
        return question_line, " ".join(lines[1:]).strip()

    return lines[0], ""


def run_ocr(image_path: Path, language: str) -> str:
    with Image.open(image_path) as img:
        grayscale_image = img.convert("L")
    try:
        return pytesseract.image_to_string(grayscale_image, lang=language)
    except TesseractNotFoundError as exc:  # pragma: no cover - depends on host
        raise SystemExit(
            "Tesseract OCR is not installed or not on PATH. Install it from "
            "https://tesseract-ocr.github.io/tessdoc/Installation.html"
        ) from exc


def ensure_tesseract_available() -> None:
    """Fail fast with a friendly message when the Tesseract binary is missing."""

    if shutil.which("tesseract"):
        return

    raise SystemExit(
        "Tesseract OCR binary not found on PATH. Install it and try again. "
        "See https://tesseract-ocr.github.io/tessdoc/Installation.html for instructions."
    )


def build_questions(image_paths: Iterable[Path], language: str) -> List[dict]:
    questions = []
    for image_path in image_paths:
        text = run_ocr(image_path, language)
        question, answer = split_question_answer(text)
        questions.append({"question": question, "answer": answer})
    return questions


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract OCR text from images into JSON questions/answers.")
    parser.add_argument(
        "inputs",
        nargs="+",
        help="Image files, directories, or glob patterns to process (e.g. '*.jpeg').",
    )
    parser.add_argument(
        "--lang",
        default="eng",
        help="Language code for Tesseract OCR (default: eng).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output JSON file. Prints to stdout when omitted.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Indentation level for JSON output (default: 2).",
    )

    args = parser.parse_args()

    ensure_tesseract_available()

    image_paths = collect_image_paths(args.inputs)
    if not image_paths:
        raise SystemExit("No matching image files found.")

    questions = build_questions(image_paths, args.lang)
    payload = {"questions": questions}
    serialized = json.dumps(payload, indent=args.indent, ensure_ascii=False)

    if args.output:
        args.output.write_text(serialized, encoding="utf-8")
    else:
        print(serialized)


if __name__ == "__main__":
    main()
