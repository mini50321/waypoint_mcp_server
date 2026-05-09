from waypoint_mcp.parsers.lesson_parser import parse_lesson
from waypoint_mcp.retrieval.matcher import analyze_lesson_demands


def test_parse_lesson_extracts_core_sections_and_demands() -> None:
    pages = [
        {
            "page": 1,
            "text": """
Lesson: What is community and why is it important?
Unit: Community and Belonging
Grade: 7
Subject: ELA
Objective: Students will identify the central idea and supporting details in an informational text.
Vocabulary: aspect, moral, narrative, specific

Opening
Students review the lesson objective, activate prior knowledge, and discuss what makes a community.

During Reading
Students read the informational text in chunks, track the central idea, annotate supporting details, and answer comprehension questions.

Independent Practice
Students answer multiple choice questions and write a paragraph response using claim and evidence from the text.

Discussion
Students discuss partner questions and share how the author's examples support the central idea.

Assessment
Students complete an exit ticket with comprehension questions and a short written response.
""",
        }
    ]

    lesson = parse_lesson(pages)
    section_names = [section["name"] for section in lesson.sections]

    assert section_names == [
        "Opening",
        "During Reading",
        "Independent Practice",
        "Discussion",
        "Assessment",
    ]
    assert {"reading", "writing", "discussion", "assessment"}.issubset(set(lesson.global_demands))
    assert {"aspect", "moral", "narrative", "specific"}.issubset(set(lesson.vocabulary))


def test_analyze_lesson_demands_returns_teacher_relevant_tasks() -> None:
    lesson = parse_lesson(
        [
            {
                "page": 1,
                "text": """
Lesson: Understanding Central Idea
Objective: Students will identify central idea and supporting evidence.
Vocabulary: central idea, evidence

During Reading
Students read the passage, annotate important evidence, and answer comprehension questions.

Independent Practice
Students write a paragraph explaining the central idea with evidence.
""",
            }
        ]
    )

    demands = analyze_lesson_demands(lesson)
    sections = {section["name"]: section for section in demands["sections"]}

    assert "track meaning across paragraphs while reading" in sections["During Reading"]["demands"]
    assert "compose clear written responses with sentence-level accuracy" in sections["Independent Practice"]["demands"]
    assert "reading" in sections["During Reading"]["task_types"]
    assert "writing" in sections["Independent Practice"]["task_types"]
