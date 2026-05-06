from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from waypoint_mcp.models.context import ParsedProjectContext
from waypoint_mcp.models.iep import IEPData
from waypoint_mcp.models.lesson import LessonData
from waypoint_mcp.retrieval.matcher import analyze_lesson_demands, compare_lesson_to_student_needs


def _detect_format(path: str | Path) -> str:
    file_path = Path(path)
    if file_path.suffix.lower() == ".pdf":
        return "pdf"
    try:
        with file_path.open("rb") as stream:
            if stream.read(5) == b"%PDF-":
                return "pdf"
    except FileNotFoundError:
        return "unknown"
    return "text"


def _build_parser_warnings(lesson_data: LessonData, iep_data: IEPData) -> dict[str, Any]:
    missing_fields: list[str] = []
    if not lesson_data.title:
        missing_fields.append("lesson.title")
    if not lesson_data.sections:
        missing_fields.append("lesson.sections")
    if not iep_data.accommodations:
        missing_fields.append("iep.accommodations")
    if not iep_data.goals:
        missing_fields.append("iep.goals")

    all_chunks = lesson_data.raw_chunks + iep_data.raw_chunks
    low_confidence_chunks = [
        {
            "source": chunk.get("source"),
            "page": chunk.get("page"),
            "category": chunk.get("category"),
            "confidence": chunk.get("confidence", 0.0),
        }
        for chunk in all_chunks
        if float(chunk.get("confidence", 0.0)) < 0.45
    ][:20]

    unknown_chunks_count = sum(1 for chunk in all_chunks if str(chunk.get("category", "other")) == "other")
    pii_count = int(iep_data.privacy_redactions.get("count", 0)) if iep_data.privacy_redactions else 0
    redaction_ratio = float(iep_data.privacy_redactions.get("redaction_ratio", 0.0)) if iep_data.privacy_redactions else 0.0

    extraction_issues: list[str] = []
    if not lesson_data.raw_chunks:
        extraction_issues.append("No lesson chunks extracted.")
    if not iep_data.raw_chunks:
        extraction_issues.append("No IEP chunks extracted.")

    recommended_review: list[str] = []
    if missing_fields:
        recommended_review.append("Review document headings and parser taxonomy mappings.")
    if low_confidence_chunks:
        recommended_review.append("Inspect low-confidence chunks before final classroom output.")
    if redaction_ratio > 0.2:
        recommended_review.append("Redaction ratio is high; review field-based redaction patterns.")

    return {
        "missing_fields": missing_fields,
        "low_confidence_chunks": low_confidence_chunks,
        "unknown_chunks_count": unknown_chunks_count,
        "pii_redacted_count": pii_count,
        "pii_redaction_details": iep_data.privacy_redactions,
        "over_redaction_risk": redaction_ratio > 0.2,
        "extraction_issues": extraction_issues,
        "recommended_review": recommended_review,
    }


def build_parsed_project_context(
    lesson_data: LessonData,
    iep_data: IEPData,
    lesson_path: str,
    iep_path: str,
    lesson_pages: list[dict[str, Any]],
    iep_pages: list[dict[str, Any]],
) -> ParsedProjectContext:
    demands = analyze_lesson_demands(lesson_data)
    matches = compare_lesson_to_student_needs(demands, iep_data).get("matches", [])
    source_summary = {
        "lesson_source": {
            "path": str(lesson_path),
            "detected_format": _detect_format(lesson_path),
            "page_count": len(lesson_pages),
            "extract_status": "ok" if lesson_pages else "failed",
        },
        "iep_source": {
            "path": str(iep_path),
            "detected_format": _detect_format(iep_path),
            "page_count": len(iep_pages),
            "extract_status": "ok" if iep_pages else "failed",
        },
        "parse_timestamp": datetime.now(timezone.utc).isoformat(),
    }
    parser_warnings = _build_parser_warnings(lesson_data, iep_data)
    return ParsedProjectContext(
        source_summary=source_summary,
        lesson=lesson_data,
        iep=iep_data,
        matches=matches,
        parser_warnings=parser_warnings,
    )
