from __future__ import annotations

from pathlib import Path
from typing import TypedDict

import fitz


class PageText(TypedDict):
    page: int
    text: str


def _is_pdf_document(path: Path) -> bool:
    if path.suffix.lower() == ".pdf":
        return True
    with path.open("rb") as stream:
        header = stream.read(5)
    return header == b"%PDF-"


def _extract_pdf_text(path: Path) -> list[PageText]:
    pages: list[PageText] = []
    with fitz.open(path) as doc:
        for page_index, page in enumerate(doc, start=1):
            pages.append({"page": page_index, "text": page.get_text("text").strip()})
    return pages


def _extract_text_file(path: Path) -> list[PageText]:
    try:
        raw_text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raw_text = path.read_text(encoding="latin-1")

    raw_text = raw_text.strip()
    if not raw_text:
        return [{"page": 1, "text": ""}]

    # Support simple page delimiters if present in exported text.
    if "\f" in raw_text:
        sections = [section.strip() for section in raw_text.split("\f")]
    else:
        sections = [raw_text]

    return [{"page": idx, "text": section} for idx, section in enumerate(sections, start=1)]


def extract_pdf_text(path: str | Path) -> list[PageText]:
    document_path = Path(path)
    if not document_path.exists():
        raise FileNotFoundError(f"Document not found: {document_path}")

    if _is_pdf_document(document_path):
        pages = _extract_pdf_text(document_path)
    else:
        pages = _extract_text_file(document_path)

    if not pages:
        raise ValueError(f"No content extracted from document: {document_path}")
    return pages
