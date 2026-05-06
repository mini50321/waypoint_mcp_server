from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class DocumentChunk:
    source: str
    page: int
    heading: str | None
    text: str
    category: str | None = None
    normalized_category: str | None = None
    demand_tags: list[str] | None = None
    need_tags: list[str] | None = None
    support_tags: list[str] | None = None
    confidence: float = 0.0

    def to_dict(self) -> dict[str, str | int | None]:
        return asdict(self)


def _guess_heading(paragraph: str) -> str | None:
    first_line = paragraph.splitlines()[0].strip() if paragraph.strip() else ""
    if not first_line:
        return None
    if len(first_line) <= 80 and first_line.replace(" ", "").isupper():
        return first_line.title()
    if ":" in first_line and len(first_line) <= 80:
        return first_line.rstrip(":")
    return None


def chunk_pages(source: str, pages: list[dict[str, object]], min_chars: int = 120) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    for page in pages:
        page_number = int(page["page"])
        text = str(page.get("text", "")).strip()
        if not text:
            continue

        parts = [part.strip() for part in text.split("\n\n") if part.strip()]
        buffer = ""
        heading: str | None = None
        for part in parts:
            candidate_heading = _guess_heading(part)
            if candidate_heading and not heading:
                heading = candidate_heading

            if len(buffer) + len(part) < min_chars:
                buffer = f"{buffer}\n\n{part}".strip()
                continue

            chunk_text = f"{buffer}\n\n{part}".strip() if buffer else part
            chunks.append(
                DocumentChunk(
                    source=source,
                    page=page_number,
                    heading=heading,
                    text=chunk_text,
                )
            )
            buffer = ""
            heading = None

        if buffer:
            chunks.append(DocumentChunk(source=source, page=page_number, heading=heading, text=buffer))

    return chunks
