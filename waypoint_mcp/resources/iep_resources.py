from __future__ import annotations

import re

from mcp.server.fastmcp import FastMCP

from waypoint_mcp.models.iep import IEPData


def _neutralize_pronouns(text: str) -> str:
    neutralized = re.sub(r"\b[Ss]he\b", "the student", text)
    neutralized = re.sub(r"\b[Hh]er\b", "the student's", neutralized)
    neutralized = re.sub(r"\b[Hh]ers\b", "the student's", neutralized)
    neutralized = re.sub(r"\b[Hh]im\b", "the student", neutralized)
    neutralized = re.sub(r"\b[Hh]is\b", "the student's", neutralized)
    neutralized = re.sub(r"\b[Hh]e\b", "the student", neutralized)
    return neutralized


def _safe_lines(items: list[str], max_items: int = 40, blocked_terms: list[str] | None = None) -> list[str]:
    forbidden_markers = ("student name", "school:", "district:", "student id", "id:")
    blocked = tuple(term.lower() for term in (blocked_terms or []))
    safe: list[str] = []
    for item in items:
        lowered = item.lower()
        if any(marker in lowered for marker in forbidden_markers):
            continue
        if blocked and any(term in lowered for term in blocked):
            continue
        sanitized = re.sub(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b", "[redacted-student-name]", item)
        sanitized = re.sub(r"\b[A-Z0-9]{6,}\b", "[redacted-id]", sanitized)
        if any(token in sanitized.lower() for token in ("school", "district", "campus")) and ":" in sanitized:
            sanitized = sanitized.split(":", 1)[0] + ": [redacted-school]"
        safe.append(_neutralize_pronouns(sanitized))
    return safe[:max_items]


def register_iep_resources(mcp: FastMCP, iep_data: IEPData) -> None:
    blocked_terms = list(iep_data.privacy_redactions.get("blocked_terms", []))

    @mcp.resource("iep://student-summary")
    def student_summary() -> dict[str, object]:
        return {
            "student_alias": iep_data.student_alias,
            "official_enrolled_grade": iep_data.official_enrolled_grade or iep_data.grade,
            "grade": iep_data.grade,
            "academic_performance_levels": iep_data.academic_performance_levels[:20],
            "strengths": _safe_lines(iep_data.strengths, blocked_terms=blocked_terms),
            "academic_needs": _safe_lines(iep_data.academic_needs, blocked_terms=blocked_terms),
            "functional_needs": _safe_lines(iep_data.functional_needs, blocked_terms=blocked_terms),
            "privacy_redactions": iep_data.privacy_redactions,
            "parser_confidence": iep_data.parser_confidence,
        }

    @mcp.resource("iep://present-levels")
    def iep_present_levels() -> list[str]:
        return _safe_lines(iep_data.present_levels, blocked_terms=blocked_terms)

    @mcp.resource("iep://goals")
    def iep_goals() -> list[str]:
        return _safe_lines(iep_data.goals, blocked_terms=blocked_terms)

    @mcp.resource("iep://accommodations")
    def iep_accommodations() -> list[str]:
        return _safe_lines(iep_data.accommodations, blocked_terms=blocked_terms)

    @mcp.resource("iep://behavior-supports")
    def iep_behavior_supports() -> list[str]:
        return _safe_lines(iep_data.behavior_supports, blocked_terms=blocked_terms)

    @mcp.resource("iep://assessment-supports")
    def iep_assessment_supports() -> list[str]:
        return _safe_lines(iep_data.assessment_supports, blocked_terms=blocked_terms)
