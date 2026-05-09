from waypoint_mcp.parsers.iep_parser import parse_iep


def test_parse_iep_redacts_private_student_information() -> None:
    pages = [
        {
            "page": 1,
            "text": """
Student Name: Maria Lopez
Student ID: ABC123456
School: Lincoln Middle School
DOB: 01/02/2012
Parent email: parent@example.com
Parent phone: 555-123-4567

Present Levels: The student is in Grade 7 and needs reading comprehension, vocabulary, and written expression support.
Reading level: Grade 3 based on classroom assessments.

Annual Goal: Given grade-level informational text, the student will identify the central idea and two supporting details.

Accommodations: Provide graphic organizer, checklist, repeated directions, and frequent brief supervised breaks.
Testing accommodation: Provide extended time and a reference sheet for assessments.
""",
        }
    ]

    iep = parse_iep(pages, student_alias="student-a")
    exposed_text = " ".join(
        iep.strengths
        + iep.present_levels
        + iep.goals
        + iep.accommodations
        + iep.assessment_supports
        + iep.behavior_supports
    ).lower()

    assert iep.student_alias == "student-a"
    assert "maria" not in exposed_text
    assert "lopez" not in exposed_text
    assert "lincoln" not in exposed_text
    assert "abc123456" not in exposed_text
    assert iep.privacy_redactions["name_redactions"] >= 1
    assert iep.privacy_redactions["id_redactions"] >= 1
    assert iep.privacy_redactions["school_redactions"] >= 1
    assert iep.privacy_redactions["contact_redactions"] >= 1


def test_parse_iep_separates_enrolled_grade_from_performance_levels() -> None:
    pages = [
        {
            "page": 1,
            "text": """
Student Name: Maria Lopez
Grade: 7

Present Levels: The student participates in seventh grade ELA with support for reading comprehension and written expression.
Reading level: Grade 3 on recent progress monitoring.
Vocabulary level: Grade 2 on classroom vocabulary measures.

Annual Goal: The student will answer comprehension questions using text evidence.
Accommodations: Use graphic organizers, sentence frames, and teacher check-ins.
""",
        }
    ]

    iep = parse_iep(pages, student_alias="student-a")
    performance_levels = {
        item["domain"]: item["reported_level"] for item in iep.academic_performance_levels
    }

    assert iep.official_enrolled_grade == "7"
    assert iep.grade == "7"
    assert performance_levels["reading_level"] == "3"
    assert performance_levels["vocabulary_level"] == "2"
