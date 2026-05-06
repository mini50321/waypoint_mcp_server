from __future__ import annotations

import re

from waypoint_mcp.models.lesson import LessonData
from waypoint_mcp.parsers.chunker import chunk_pages
from waypoint_mcp.parsers.classifier import LESSON_CATEGORIES, classify_text_with_confidence
from waypoint_mcp.parsers.taxonomy import infer_lesson_demand_tags, normalize_lesson_section_type


def _collect_bullet_lines(text: str) -> list[str]:
    lines = [line.strip("-*0123456789. ").strip() for line in text.splitlines()]
    return [line for line in lines if line and len(line) > 2]


def _dedupe_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.lower().strip()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item.strip())
    return result


def _extract_value_after_colon(line: str) -> str | None:
    if ":" not in line:
        return None
    _, value = line.split(":", 1)
    cleaned = value.strip()
    return cleaned or None


def _split_terms(text: str) -> list[str]:
    parts = [part.strip(" .;") for part in re.split(r"[,;/]", text)]
    return [part for part in parts if part and len(part) > 1]


def _extract_sections(full_text: str) -> list[dict[str, object]]:
    heading_patterns: list[tuple[str, str]] = [
        (r"\b(opening|introduction|intro)\b", "Opening"),
        (r"\b(during reading|guided practice)\b", "During Reading"),
        (r"\b(independent practice|independent work)\b", "Independent Practice"),
        (r"\b(discussion|student-led discussion|share out)\b", "Discussion"),
        (r"\b(assessment|exit ticket|quiz)\b", "Assessment"),
    ]

    sections: list[dict[str, str]] = []
    current_name: str | None = None
    current_lines: list[str] = []

    for raw_line in full_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        matched_name: str | None = None
        for pattern, normalized_name in heading_patterns:
            if re.search(pattern, line, flags=re.IGNORECASE):
                matched_name = normalized_name
                break

        if matched_name:
            if current_name and current_lines:
                section_text = " ".join(current_lines).strip()
                sections.append(
                    {
                        "name": current_name,
                        "section_type": normalize_lesson_section_type(current_name),
                        "demand_tags": infer_lesson_demand_tags(section_text, current_name),
                        "text": section_text,
                    }
                )
            current_name = matched_name
            current_lines = []
            continue

        if current_name:
            current_lines.append(line)

    if current_name and current_lines:
        section_text = " ".join(current_lines).strip()
        sections.append(
            {
                "name": current_name,
                "section_type": normalize_lesson_section_type(current_name),
                "demand_tags": infer_lesson_demand_tags(section_text, current_name),
                "text": section_text,
            }
        )

    return sections


def parse_lesson(pages: list[dict[str, object]]) -> LessonData:
    chunks = chunk_pages("lesson", pages)
    lesson = LessonData()
    full_text = "\n".join(str(page.get("text", "")) for page in pages if page.get("text"))
    all_lines = _collect_bullet_lines(full_text)

    for chunk in chunks:
        category, confidence = classify_text_with_confidence(chunk.text, LESSON_CATEGORIES)
        chunk.category = category
        chunk.normalized_category = category
        chunk.confidence = confidence
        chunk.demand_tags = infer_lesson_demand_tags(chunk.text, chunk.heading or "")
        chunk_id = f"lesson-{chunk.page:03d}-{len(lesson.raw_chunks)+1:03d}"
        lesson.provenance.append(
            {
                "chunk_id": chunk_id,
                "source": "lesson",
                "page": chunk.page,
                "heading": chunk.heading,
                "confidence": confidence,
                "category": category,
            }
        )
        lesson.raw_chunks.append(chunk.to_dict())

        lines = _collect_bullet_lines(chunk.text)

        if category == "overview":
            if not lesson.title:
                lesson.title = chunk.heading or (lines[0] if lines else None)
            if not lesson.grade:
                for line in lines:
                    if "grade" in line.lower() or re.search(r"\bgrade\s*\d+\b", line, flags=re.IGNORECASE):
                        lesson.grade = _extract_value_after_colon(line) or line
                        break
            if not lesson.subject:
                for line in lines:
                    if "subject" in line.lower() or "ela" in line.lower() or "math" in line.lower():
                        lesson.subject = _extract_value_after_colon(line) or line
                        break
            if not lesson.unit:
                for line in lines:
                    if "unit" in line.lower():
                        lesson.unit = _extract_value_after_colon(line) or line
                        break
        elif category == "objectives":
            lesson.objectives.extend(lines)
        elif category == "standards":
            lesson.standards.extend(lines)
        elif category == "materials":
            lesson.materials.extend(lines)
            lesson.text_or_materials.extend(lines)
        elif category == "vocabulary":
            for line in lines:
                value = _extract_value_after_colon(line) if "vocabulary" in line.lower() else line
                lesson.vocabulary.extend(_split_terms(value or line))
        elif category == "lesson_section":
            section_name = chunk.heading or "Section"
            lesson.sections.append(
                {
                    "section_id": f"sec-{len(lesson.sections)+1:03d}",
                    "name": section_name,
                    "section_type": normalize_lesson_section_type(section_name),
                    "demand_tags": infer_lesson_demand_tags(chunk.text, section_name),
                    "text": chunk.text,
                    "original_task": lines[0] if lines else chunk.text[:180],
                    "student_actions": infer_lesson_demand_tags(chunk.text, section_name),
                    "questions_or_prompts": [line for line in lines if "?" in line],
                    "confidence": confidence,
                    "provenance": [{"source": "lesson", "page": chunk.page}],
                }
            )
        elif category == "assessment":
            lesson.assessments.extend(lines)

        lesson.questions.extend([line for line in lines if "?" in line or "question" in line.lower()])

    if not lesson.title and all_lines:
        lesson.title = all_lines[0]

    if not lesson.grade:
        for line in all_lines:
            match = re.search(r"\bgrade\s*(\d+)\b", line, flags=re.IGNORECASE)
            if match:
                lesson.grade = match.group(1)
                break

    if not lesson.subject:
        for line in all_lines:
            if any(subject in line.lower() for subject in ("ela", "english", "math", "science", "social studies")):
                lesson.subject = line
                break

    if not lesson.vocabulary:
        for idx, line in enumerate(all_lines):
            if "vocabulary" not in line.lower() and "key term" not in line.lower():
                continue
            extracted = _extract_value_after_colon(line)
            if extracted:
                lesson.vocabulary.extend(_split_terms(extracted))
            elif idx + 1 < len(all_lines):
                lesson.vocabulary.extend(_split_terms(all_lines[idx + 1]))

    if not lesson.assessments:
        lesson.assessments = [
            line
            for line in all_lines
            if any(keyword in line.lower() for keyword in ("assessment", "exit ticket", "quiz", "short response"))
        ][:8]

    section_candidates = _extract_sections(full_text)
    if section_candidates:
        for idx, section in enumerate(section_candidates, start=1):
            section.setdefault("section_id", f"sec-{idx:03d}")
            section.setdefault("original_task", section.get("text", "")[:220])
            section.setdefault("student_actions", section.get("demand_tags", []))
            section.setdefault("questions_or_prompts", [])
            section.setdefault("confidence", 0.75)
            section.setdefault("provenance", [{"source": "lesson"}])
        lesson.sections = section_candidates

    if not lesson.sections:
        fallback_text = " ".join(page["text"] for page in pages if page.get("text"))
        lesson.sections = [
            {
                "section_id": "sec-001",
                "name": "Lesson",
                "section_type": "unknown",
                "demand_tags": infer_lesson_demand_tags(fallback_text, "Lesson"),
                "text": fallback_text,
                "original_task": fallback_text[:220],
                "student_actions": infer_lesson_demand_tags(fallback_text, "Lesson"),
                "questions_or_prompts": [],
                "confidence": 0.45,
                "provenance": [{"source": "lesson"}],
            }
        ]

    lesson.objectives = _dedupe_keep_order(lesson.objectives)
    lesson.objective = list(lesson.objectives)
    lesson.standards = _dedupe_keep_order(lesson.standards)
    lesson.materials = _dedupe_keep_order(lesson.materials)
    lesson.text_or_materials = _dedupe_keep_order(lesson.text_or_materials + lesson.materials)
    lesson.vocabulary = _dedupe_keep_order(lesson.vocabulary)
    lesson.questions = _dedupe_keep_order(lesson.questions)
    lesson.assessments = _dedupe_keep_order(lesson.assessments)
    lesson.skill_focus = lesson.objectives[0] if lesson.objectives else lesson.skill_focus
    essential_questions = [line for line in all_lines if "essential question" in line.lower() or line.strip().endswith("?")]
    if essential_questions:
        lesson.essential_question = essential_questions[0]
    all_confidences = [float(chunk.get("confidence", 0.0)) for chunk in lesson.raw_chunks]
    lesson.parser_confidence = round(sum(all_confidences) / len(all_confidences), 3) if all_confidences else 0.0
    lesson.global_demands = _dedupe_keep_order(
        [tag for section in lesson.sections for tag in section.get("demand_tags", [])]
    )

    return lesson
