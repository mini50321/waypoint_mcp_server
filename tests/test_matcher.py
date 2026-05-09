from waypoint_mcp.models.iep import IEPData
from waypoint_mcp.models.lesson import LessonData
from waypoint_mcp.retrieval.matcher import (
    analyze_lesson_demands,
    compare_lesson_to_student_needs,
    get_relevant_iep_context,
)


def test_relevant_iep_context_separates_documented_supports_from_scaffolds() -> None:
    lesson = LessonData(
        sections=[
            {
                "section_id": "sec-001",
                "name": "During Reading",
                "section_type": "during_reading",
                "text": "Students read a grade-level passage, track central idea, and answer comprehension questions.",
                "demand_tags": ["reading", "comprehension", "central_idea"],
            }
        ],
        vocabulary=["community", "specific"],
    )
    iep = IEPData(
        academic_needs=["reading comprehension", "vocabulary support"],
        goals=["Given informational text, the student will identify central idea and supporting details."],
        accommodations=[
            "Accommodation: provide a graphic organizer for reading comprehension tasks.",
            "Accommodation: provide checklist and frequent brief supervised breaks.",
        ],
    )

    context = get_relevant_iep_context(
        section_name="During Reading",
        task_type="reading",
        lesson_data=lesson,
        iep_data=iep,
    )

    assert context["iep_documented_accommodations"]
    assert context["recommended_instructional_scaffolds"]
    assert any("graphic organizer" in item.lower() for item in context["iep_documented_accommodations"])
    assert "chunk the text" in context["recommended_instructional_scaffolds"]
    assert context["support_labeling"]["iep_documented_accommodations"].startswith("Only supports")


def test_compare_lesson_to_student_needs_maps_demands_to_supports() -> None:
    lesson = LessonData(
        objectives=["Students will write a response using text evidence."],
        sections=[
            {
                "section_id": "sec-001",
                "name": "Independent Practice",
                "section_type": "independent_practice",
                "text": "Students write a paragraph response with a claim and evidence from the text.",
                "demand_tags": ["writing", "claim_evidence_reasoning"],
            }
        ],
    )
    iep = IEPData(
        academic_needs=["written expression"],
        goals=["The student will write a paragraph using claim and evidence."],
        accommodations=[
            "Accommodation: provide a graphic organizer and checklist for written responses.",
            "Accommodation: provide extended time for assessment and writing tasks.",
        ],
    )

    demands = analyze_lesson_demands(lesson)
    comparison = compare_lesson_to_student_needs(demands, iep)

    assert comparison["matches"]
    writing_match = next(
        match for match in comparison["matches"] if "sentence starters" in match["modification_direction"]
    )
    assert "Independent Practice" in writing_match["lesson_demand"]
    assert "written expression" in writing_match["student_need"]
    assert "graphic organizer" in writing_match["iep_support"].lower()
