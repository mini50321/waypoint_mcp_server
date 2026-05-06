from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from waypoint_mcp.models.lesson import LessonData


def register_lesson_tools(mcp: FastMCP, lesson_data: LessonData) -> None:
    @mcp.tool()
    def get_lesson_outline() -> dict[str, object]:
        """Return lesson objective, sections, activities, and assessment."""
        skill_focus = lesson_data.objectives[0] if lesson_data.objectives else None
        return {
            "title": lesson_data.title,
            "grade": lesson_data.grade,
            "subject": lesson_data.subject,
            "unit": lesson_data.unit,
            "essential_question": lesson_data.essential_question,
            "skill_focus": skill_focus,
            "objectives": lesson_data.objective or lesson_data.objectives,
            "vocabulary": lesson_data.vocabulary,
            "questions": lesson_data.questions,
            "sections": [section.get("name", "Section") for section in lesson_data.sections],
            "section_details": [
                {
                    "section_id": section.get("section_id"),
                    "name": section.get("name", "Section"),
                    "section_type": section.get("section_type", "unknown"),
                    "demand_tags": section.get("demand_tags", []),
                    "confidence": section.get("confidence", lesson_data.parser_confidence),
                }
                for section in lesson_data.sections
            ],
            "assessment": lesson_data.assessments,
            "parser_confidence": lesson_data.parser_confidence,
        }

    @mcp.tool()
    def get_lesson_section(section_name: str) -> dict[str, object]:
        """Return one lesson section by section name."""
        for section in lesson_data.sections:
            if str(section.get("name", "")).lower() == section_name.lower():
                return section
        return {"name": section_name, "text": "", "warning": "section not found"}
