from __future__ import annotations

from pathlib import Path
from typing import Any

from waypoint_mcp.loaders.pdf_loader import extract_pdf_text


def load_iep_pages(path: str | Path) -> dict[str, Any]:
    pages = extract_pdf_text(path)
    return {"source": "iep", "pages": pages, "warnings": [], "errors": []}
