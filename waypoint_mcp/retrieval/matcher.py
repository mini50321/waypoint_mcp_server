from __future__ import annotations

from typing import Any

from waypoint_mcp.models.iep import IEPData
from waypoint_mcp.models.lesson import LessonData
from waypoint_mcp.parsers.taxonomy import infer_bridge_support_tags, infer_lesson_demand_tags


def infer_task_type(section_text: str) -> list[str]:
    text = section_text.lower()
    task_types: list[str] = []
    if any(word in text for word in ["read", "text", "passage", "comprehension"]):
        task_types.append("reading")
    if any(word in text for word in ["write", "response", "paragraph", "claim", "evidence"]):
        task_types.append("writing")
    if any(word in text for word in ["discuss", "partner", "share", "talk"]):
        task_types.append("discussion")
    if any(word in text for word in ["quiz", "assessment", "exit ticket", "test"]):
        task_types.append("assessment")
    if any(word in text for word in ["focus", "attention", "behavior", "regulation"]):
        task_types.append("attention")
    return task_types or ["general"]


def analyze_lesson_demands(lesson_data: LessonData) -> dict[str, list[dict[str, Any]]]:
    sections: list[dict[str, Any]] = []
    objective_hint = lesson_data.objectives[0] if lesson_data.objectives else ""
    for section in lesson_data.sections:
        section_text = str(section.get("text", ""))
        name = str(section.get("name", "Section"))
        tasks = infer_task_type(section_text)
        demand_tags = list(dict.fromkeys(section.get("demand_tags", []) or infer_lesson_demand_tags(section_text, name)))
        difficulty_tags = [tag for tag in demand_tags if tag in {"attention", "working_memory", "text_tracking", "comprehension"}]
        demands: list[str] = []

        if "opening" in name.lower() or "intro" in name.lower():
            demands.extend(
                [
                    "activate prior knowledge about lesson topic",
                    "understand lesson objective before reading",
                ]
            )
        if "reading" in name.lower():
            demands.extend(
                [
                    "read grade-level text in chunks",
                    "identify central idea and supporting details",
                    "answer comprehension questions",
                    "interpret vocabulary in context",
                ]
            )
        if "independent" in name.lower() or "practice" in name.lower():
            demands.extend(
                [
                    "write a response using text evidence",
                    "organize claim and supporting evidence",
                    "complete task independently with stamina",
                ]
            )
        if "discussion" in name.lower():
            demands.extend(
                [
                    "prepare an idea before speaking",
                    "listen and respond to peers during discussion",
                ]
            )
        if "assessment" in name.lower() or "exit ticket" in name.lower():
            demands.extend(
                [
                    "demonstrate understanding in limited time",
                    "complete comprehension or short-response check",
                ]
            )

        for task in tasks:
            if task == "reading":
                demands.append("track meaning across paragraphs while reading")
            elif task == "writing":
                demands.append("compose clear written responses with sentence-level accuracy")
            elif task == "discussion":
                demands.append("express understanding orally using academic language")
            elif task == "assessment":
                demands.append("show mastery in assessment format")
            elif task == "attention":
                demands.append("sustain focus and self-regulate through multi-step tasks")

        if objective_hint:
            demands.append(f"align work to objective: {objective_hint}")
        if lesson_data.vocabulary:
            demands.append(f"use lesson vocabulary: {', '.join(lesson_data.vocabulary[:6])}")
        demands = list(dict.fromkeys(demands))
        sections.append(
            {
                "section_id": section.get("section_id"),
                "name": name,
                "section_type": section.get("section_type", "unknown"),
                "original_task": section.get("original_task", section_text[:220]),
                "student_actions": section.get("student_actions", demand_tags),
                "task_types": tasks,
                "demand_tags": demand_tags,
                "difficulty_tags": difficulty_tags,
                "demands": demands,
                "confidence": section.get("confidence", lesson_data.parser_confidence),
                "provenance": section.get("provenance", []),
            }
        )
    lesson_data.lesson_demands = sections
    return {"sections": sections}


def get_supports_for_task(task_type: str, iep_data: IEPData) -> dict[str, Any]:
    goal_keywords: dict[str, list[str]] = {
        "reading": ["read", "comprehension", "infer", "main idea", "central idea", "annotat"],
        "writing": ["write", "claim", "evidence", "analysis", "paragraph", "response"],
        "discussion": ["discuss", "oral", "conversation", "speak"],
        "assessment": ["assessment", "test", "quiz", "check"],
        "attention": ["attention", "self-regulation", "focus", "behavior"],
    }
    result: dict[str, Any] = {
        "relevant_needs": [],
        "relevant_goals": [],
        "relevant_accommodations": [],
        "iep_documented_accommodations": [],
        "recommended_instructional_scaffolds": [],
    }

    if task_type == "reading":
        result["relevant_needs"] += ["reading comprehension", "vocabulary support", "text tracking"]
        result["recommended_instructional_scaffolds"] += [
            "chunk the text",
            "pre-teach vocabulary",
            "use a graphic organizer",
            "check comprehension after each section",
        ]
    elif task_type == "writing":
        result["relevant_needs"] += ["written expression", "claim/evidence support", "writing stamina"]
        result["recommended_instructional_scaffolds"] += [
            "provide sentence starters",
            "use a paragraph frame",
            "use a claim-evidence reasoning organizer",
            "allow oral rehearsal",
            "provide a writing checklist",
        ]
    elif task_type == "discussion":
        result["recommended_instructional_scaffolds"] += [
            "give preparation time",
            "provide sentence frames",
            "allow partner rehearsal",
        ]
    elif task_type == "assessment":
        result["recommended_instructional_scaffolds"] += [
            "allow extra time",
            "provide checklist/reference sheet",
            "allow alternative response format",
        ]
    elif task_type == "attention":
        result["recommended_instructional_scaffolds"] += [
            "front-load instructions",
            "schedule short check-ins",
            "offer planned movement break",
        ]
    else:
        result["recommended_instructional_scaffolds"] += ["repeat directions", "offer visual checklist"]

    if iep_data.academic_needs:
        result["relevant_needs"].extend(iep_data.academic_needs)
    result["relevant_needs"] = list(dict.fromkeys(result["relevant_needs"]))
    result["relevant_goals"] = [
        goal
        for goal in iep_data.goals
        if any(keyword in goal.lower() for keyword in goal_keywords.get(task_type.lower(), []))
    ] or list(iep_data.goals[:20])

    lowered_task = task_type.lower()
    bridge_support_tags = infer_bridge_support_tags([lowered_task])
    bridge_keywords = {
        "chunking": ["chunk"],
        "graphic_organizer": ["organizer"],
        "sentence_starter": ["sentence starter", "frame"],
        "paragraph_frame": ["paragraph frame", "writing frame", "frame"],
        "extra_time": ["extra time", "extended time"],
        "repeated_directions": ["repeat directions", "directions"],
        "visual_support": ["visual"],
        "vocabulary_preview": ["vocabulary", "pre-teach"],
        "text_tracking_aid": ["tracking", "line reader"],
        "comprehension_check": ["comprehension check", "check for understanding"],
        "small_group": ["small group"],
        "one_to_one_checkin": ["1:1", "check-in"],
        "breaks": ["break"],
        "alternate_response": ["alternate response", "alternative response"],
        "oral_response": ["oral response", "verbal response"],
        "reduced_quantity": ["reduced", "shortened"],
    }
    accommodation_quality_keywords = [
        "accommodation",
        "organizer",
        "checklist",
        "extra time",
        "extended time",
        "break",
        "small group",
        "1:1",
        "check-in",
        "reference",
        "repeat directions",
        "visual",
        "sentence starter",
        "paragraph frame",
        "oral response",
        "alternate",
        "preferential seating",
        "front",
    ]

    source_accommodations = (
        list(iep_data.accommodations)
        + list(iep_data.assessment_supports)
        + list(iep_data.behavior_supports)
        + list(iep_data.modifications)
    )
    quality_accommodations = [
        item
        for item in source_accommodations
        if len(item.strip()) > 10 and any(keyword in item.lower() for keyword in accommodation_quality_keywords)
    ]
    if iep_data.accommodations:
        filtered_accommodations = [
            item
            for item in quality_accommodations
            if lowered_task in item.lower()
            or any(token in item.lower() for token in ["checklist", "graphic organizer", "extended time", "break"])
            or any(
                any(keyword in item.lower() for keyword in bridge_keywords.get(tag, [])) for tag in bridge_support_tags
            )
        ]
        result["relevant_accommodations"] = filtered_accommodations or quality_accommodations
        result["iep_documented_accommodations"] = result["relevant_accommodations"]
    result["recommended_instructional_scaffolds"] = list(dict.fromkeys(result["recommended_instructional_scaffolds"]))

    return result


def get_relevant_iep_context(
    section_name: str,
    task_type: str,
    lesson_data: LessonData,
    iep_data: IEPData,
) -> dict[str, Any]:
    if not task_type:
        section_text = next(
            (
                str(section.get("text", ""))
                for section in lesson_data.sections
                if str(section.get("name", "")).lower() == section_name.lower()
            ),
            "",
        )
        inferred = infer_task_type(section_text)
        task_type = inferred[0]

    supports = get_supports_for_task(task_type=task_type, iep_data=iep_data)
    lesson_section = next(
        (section for section in lesson_data.sections if str(section.get("name", "")).lower() == section_name.lower()),
        {"name": section_name, "text": ""},
    )
    demand_tags = list(dict.fromkeys(lesson_section.get("demand_tags", []) or infer_lesson_demand_tags(str(lesson_section.get("text", "")), section_name)))
    bridge_support_tags = infer_bridge_support_tags(demand_tags)
    return {
        "lesson_section": lesson_section.get("name", section_name),
        "task_type": task_type,
        "demand_tags": demand_tags,
        "bridge_support_tags": bridge_support_tags,
        "recommended_supports": supports.get("recommended_instructional_scaffolds", []),
        "support_labeling": {
            "iep_documented_accommodations": "Only supports explicitly parsed from IEP text.",
            "recommended_instructional_scaffolds": "System-recommended scaffolds inferred from lesson demands and student needs.",
        },
        **supports,
    }


def compare_lesson_to_student_needs(demands: dict[str, list[dict[str, Any]]], iep_data: IEPData) -> dict[str, Any]:
    matches: list[dict[str, str]] = []
    for section in demands.get("sections", []):
        section_name = str(section.get("name", "Section"))
        for task_type in section.get("task_types", ["general"]):
            supports = get_supports_for_task(task_type, iep_data)
            strongest_demand = "; ".join(section.get("demands", [])[:2]) or task_type
            matches.append(
                {
                    "lesson_demand": f"{section_name}: {strongest_demand}",
                    "student_need": ", ".join(supports["relevant_needs"]) or "general support",
                    "iep_support": ", ".join(supports["iep_documented_accommodations"]) or "teacher discretion",
                    "modification_direction": ", ".join(supports["recommended_instructional_scaffolds"]),
                }
            )
    return {"matches": matches}
