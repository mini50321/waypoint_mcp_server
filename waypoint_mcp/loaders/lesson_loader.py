from __future__ import annotations

from pathlib import Path
from typing import Any

from waypoint_mcp.loaders.pdf_loader import extract_pdf_text


def load_lesson_pages(path: str | Path) -> dict[str, Any]:
    pages = extract_pdf_text(path)
    return {"source": "lesson", "pages": pages, "warnings": [], "errors": []}
