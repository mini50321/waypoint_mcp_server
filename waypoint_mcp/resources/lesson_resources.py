from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from waypoint_mcp.models.lesson import LessonData


def register_lesson_resources(mcp: FastMCP, lesson_data: LessonData) -> None:
    @mcp.resource("lesson://overview")
    def lesson_overview() -> dict[str, object]:
        return {
            "lesson_id": lesson_data.lesson_id,
            "title": lesson_data.title,
            "grade": lesson_data.grade,
            "subject": lesson_data.subject,
            "unit": lesson_data.unit,
            "objective": lesson_data.objective or lesson_data.objectives,
            "essential_question": lesson_data.essential_question,
            "skill_focus": lesson_data.skill_focus,
            "parser_confidence": lesson_data.parser_confidence,
        }

    @mcp.resource("lesson://sections")
    def lesson_sections() -> list[dict[str, object]]:
        return lesson_data.sections

    @mcp.resource("lesson://vocabulary")
    def lesson_vocabulary() -> list[str]:
        return lesson_data.vocabulary

    @mcp.resource("lesson://assessment")
    def lesson_assessment() -> list[str]:
        return lesson_data.assessments

    @mcp.resource("lesson://demands")
    def lesson_demands() -> list[dict[str, object]]:
        return lesson_data.lesson_demands
