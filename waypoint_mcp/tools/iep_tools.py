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


def _safe_iep_lines(items: list[str], max_items: int, blocked_terms: list[str] | None = None) -> list[str]:
    forbidden_markers = ("student name", "school:", "district:", "student id", "id:")
    blocked = tuple(term.lower() for term in (blocked_terms or []))
    filtered: list[str] = []
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
        filtered.append(_neutralize_pronouns(sanitized))
    return filtered[:max_items]


def register_iep_tools(mcp: FastMCP, iep_data: IEPData) -> None:
    @mcp.tool()
    def get_student_profile() -> dict[str, object]:
        """Return student strengths, present levels, goals, and accommodations."""
        max_items = 25
        blocked_terms = list(iep_data.privacy_redactions.get("blocked_terms", []))
        return {
            "student_alias": iep_data.student_alias,
            "official_enrolled_grade": iep_data.official_enrolled_grade or iep_data.grade,
            "grade": iep_data.grade,
            "academic_performance_levels": iep_data.academic_performance_levels[:max_items],
            "disability_category": iep_data.disability_category,
            "strengths": _safe_iep_lines(iep_data.strengths, max_items, blocked_terms),
            "interests": _safe_iep_lines(iep_data.interests, max_items, blocked_terms),
            "present_levels": _safe_iep_lines(iep_data.present_levels, max_items, blocked_terms),
            "academic_needs": _safe_iep_lines(iep_data.academic_needs, max_items, blocked_terms),
            "functional_needs": _safe_iep_lines(iep_data.functional_needs, max_items, blocked_terms),
            "goals": _safe_iep_lines(iep_data.goals, max_items, blocked_terms),
            "accommodations": _safe_iep_lines(iep_data.accommodations, max_items, blocked_terms),
            "key_accommodations": _safe_iep_lines(iep_data.accommodations, max_items, blocked_terms),
            "modifications": _safe_iep_lines(iep_data.modifications, max_items, blocked_terms),
            "assessment_supports": _safe_iep_lines(iep_data.assessment_supports, max_items, blocked_terms),
            "behavior_supports": _safe_iep_lines(iep_data.behavior_supports, max_items, blocked_terms),
            "self_regulation_supports": _safe_iep_lines(iep_data.self_regulation_supports, max_items, blocked_terms),
            "assistive_technology": _safe_iep_lines(iep_data.assistive_technology, max_items, blocked_terms),
            "service_notes": _safe_iep_lines(iep_data.service_notes, max_items, blocked_terms),
            "privacy_redactions": iep_data.privacy_redactions,
            "parser_confidence": iep_data.parser_confidence,
        }
