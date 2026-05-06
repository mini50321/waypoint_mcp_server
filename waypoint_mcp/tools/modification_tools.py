from __future__ import annotations

import re

from mcp.server.fastmcp import FastMCP

from waypoint_mcp.models.context import ParsedProjectContext
from waypoint_mcp.models.iep import IEPData
from waypoint_mcp.models.lesson import LessonData
from waypoint_mcp.retrieval.matcher import (
    analyze_lesson_demands as analyze_lesson_demands_impl,
    compare_lesson_to_student_needs as compare_lesson_to_student_needs_impl,
    get_relevant_iep_context as get_relevant_iep_context_impl,
)


def _safe_iep_lines(items: list[str], max_items: int = 40, blocked_terms: list[str] | None = None) -> list[str]:
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
        sanitized = re.sub(r"\b[Ss]he\b", "the student", sanitized)
        sanitized = re.sub(r"\b[Hh]er\b", "the student's", sanitized)
        sanitized = re.sub(r"\b[Hh]ers\b", "the student's", sanitized)
        sanitized = re.sub(r"\b[Hh]im\b", "the student", sanitized)
        sanitized = re.sub(r"\b[Hh]is\b", "the student's", sanitized)
        sanitized = re.sub(r"\b[Hh]e\b", "the student", sanitized)
        safe.append(sanitized)
    return safe[:max_items]


def register_modification_tools(
    mcp: FastMCP,
    lesson_data: LessonData,
    iep_data: IEPData,
    parsed_context: ParsedProjectContext | None = None,
) -> None:
    @mcp.tool()
    def get_relevant_iep_context(section_name: str, task_type: str) -> dict[str, object]:
        """Return IEP supports relevant to a lesson section and task type."""
        return get_relevant_iep_context_impl(
            section_name=section_name,
            task_type=task_type,
            lesson_data=lesson_data,
            iep_data=iep_data,
        )

    @mcp.tool()
    def analyze_lesson_demands() -> dict[str, object]:
        """Analyze what each lesson section requires from the student."""
        return analyze_lesson_demands_impl(lesson_data)

    @mcp.tool()
    def compare_lesson_to_student_needs() -> dict[str, object]:
        """Connect lesson demands to IEP needs and supports."""
        demands = analyze_lesson_demands_impl(lesson_data)
        return compare_lesson_to_student_needs_impl(demands=demands, iep_data=iep_data)

    @mcp.tool()
    def get_teacher_output_template() -> dict[str, object]:
        """Return final response structure for teacher-facing output."""
        return {
            "sections": [
                "Student Support Summary",
                "Before the Lesson",
                "Opening",
                "During Reading",
                "Independent Practice",
                "Discussion",
                "Assessment",
                "Teacher Checklist",
            ],
            "required_fields_per_section": [
                "original task",
                "student barrier",
                "IEP-documented support",
                "recommended instructional scaffold",
                "teacher action",
                "student-facing scaffold",
            ],
            "support_labeling_policy": {
                "IEP-documented support": "Must come directly from parsed IEP accommodations/assessment/behavior support text.",
                "recommended instructional scaffold": "May be inferred by the system and should not be presented as IEP-mandated language.",
            },
            "privacy_language_policy": {
                "student_reference": "Use `student-a`, `the student`, or `they/them`.",
                "forbidden_inference": "Do not infer or use gendered pronouns (she/he/her/him/his).",
            },
        }

    @mcp.tool()
    def get_parser_warnings() -> dict[str, object]:
        """Return parser warnings, confidence issues, and redaction counts."""
        if not parsed_context:
            return {"warning": "parsed context not available"}
        return parsed_context.parser_warnings

    @mcp.tool()
    def get_parsed_project_context() -> dict[str, object]:
        """Return full normalized lesson/IEP context and match summary."""
        if not parsed_context:
            return {"warning": "parsed context not available"}
        blocked_terms = list(parsed_context.iep.privacy_redactions.get("blocked_terms", []))
        safe_lesson = {
            "lesson_id": parsed_context.lesson.lesson_id,
            "title": parsed_context.lesson.title,
            "grade": parsed_context.lesson.grade,
            "subject": parsed_context.lesson.subject,
            "unit": parsed_context.lesson.unit,
            "objective": parsed_context.lesson.objective or parsed_context.lesson.objectives,
            "essential_question": parsed_context.lesson.essential_question,
            "skill_focus": parsed_context.lesson.skill_focus,
            "text_or_materials": parsed_context.lesson.text_or_materials[:25],
            "vocabulary": parsed_context.lesson.vocabulary[:25],
            "sections": parsed_context.lesson.sections[:25],
            "assessments": parsed_context.lesson.assessments[:20],
            "global_demands": parsed_context.lesson.global_demands[:20],
            "parser_confidence": parsed_context.lesson.parser_confidence,
        }
        safe_iep = {
            "student_alias": parsed_context.iep.student_alias,
            "official_enrolled_grade": parsed_context.iep.official_enrolled_grade or parsed_context.iep.grade,
            "grade": parsed_context.iep.grade,
            "academic_performance_levels": parsed_context.iep.academic_performance_levels[:25],
            "disability_category": parsed_context.iep.disability_category,
            "strengths": _safe_iep_lines(parsed_context.iep.strengths, blocked_terms=blocked_terms),
            "interests": _safe_iep_lines(parsed_context.iep.interests, blocked_terms=blocked_terms),
            "present_levels": _safe_iep_lines(parsed_context.iep.present_levels, blocked_terms=blocked_terms),
            "academic_needs": _safe_iep_lines(parsed_context.iep.academic_needs, blocked_terms=blocked_terms),
            "functional_needs": _safe_iep_lines(parsed_context.iep.functional_needs, blocked_terms=blocked_terms),
            "goals": _safe_iep_lines(parsed_context.iep.goals, blocked_terms=blocked_terms),
            "accommodations": _safe_iep_lines(parsed_context.iep.accommodations, blocked_terms=blocked_terms),
            "modifications": _safe_iep_lines(parsed_context.iep.modifications, blocked_terms=blocked_terms),
            "assessment_supports": _safe_iep_lines(parsed_context.iep.assessment_supports, blocked_terms=blocked_terms),
            "behavior_supports": _safe_iep_lines(parsed_context.iep.behavior_supports, blocked_terms=blocked_terms),
            "self_regulation_supports": _safe_iep_lines(parsed_context.iep.self_regulation_supports, blocked_terms=blocked_terms),
            "assistive_technology": _safe_iep_lines(parsed_context.iep.assistive_technology, blocked_terms=blocked_terms),
            "service_notes": _safe_iep_lines(parsed_context.iep.service_notes, blocked_terms=blocked_terms),
            "privacy_redactions": parsed_context.iep.privacy_redactions,
            "parser_confidence": parsed_context.iep.parser_confidence,
        }
        return {
            "source_summary": parsed_context.source_summary,
            "lesson": safe_lesson,
            "iep": safe_iep,
            "matches": parsed_context.matches,
            "parser_warnings": parsed_context.parser_warnings,
        }
