# MCP Tool Outputs

This file summarizes representative outputs from the Waypoint MCP server after loading the sample lesson and IEP. It shows that the server returns structured lesson context, privacy-safe student context, lesson-demand analysis, lesson-to-IEP matching, parser warnings, and a teacher-facing response template.

## `get_lesson_outline`

Returned a 7th-grade ELA lesson titled *"What is 'Community' and Why is It Important?"* from Unit 1: Community and Belonging. The lesson is built around a nonfiction text by Toby Lowe and is structured across 8 sections: Opening, two Discussions, three During Reading segments, and two Independent Practice tasks.

The lesson demands include reading comprehension, vocabulary, writing, claim/evidence reasoning, and discussion.

## `get_student_profile`

Returned a privacy-safe profile for `student-a`, a 7th-grade student reading at roughly a 2nd-3rd grade level across vocabulary, literature comprehension, and informational text comprehension.

Academic needs include reading comprehension, vocabulary support, written expression, and attention/self-regulation. IEP supports include frequent supervised breaks (DF3), graphic organizers/checklists, movement breaks, and frequent check-ins.

Privacy redactions were applied to protect the student's name, ID, school, and contact information. The parser reported 49 total redactions.

## `analyze_lesson_demands`

Returned section-level student demands for all 8 lesson sections. Key demands include:

- Activating prior knowledge before reading
- Tracking meaning across paragraphs
- Answering comprehension questions
- Composing written responses
- Organizing claim/evidence reasoning
- Sustaining stamina during independent work
- Participating in academic discussion

## `compare_lesson_to_student_needs`

Returned 24 matches between lesson demands and the student's IEP needs. Across sections, the consistent IEP-documented supports are frequent breaks, organizers/checklists, and movement breaks.

Recommended instructional modifications include:

- Chunking grade-level text
- Pre-teaching vocabulary
- Using graphic organizers
- Providing sentence frames
- Allowing partner rehearsal
- Offering extra time or alternate response formats for assessment tasks

## `get_parsed_project_context`

Confirmed that both source documents were successfully loaded and extracted:

- Lesson source: 8-page PDF
- IEP source: 36-page PDF

The parsed context includes normalized lesson data, normalized IEP data, lesson-to-student matches, source metadata, and parser warnings.

Reported parser confidence:

- Lesson: 0.394
- IEP: 0.359

## `get_parser_warnings`

Returned parser warnings and extraction confidence details. Several low-confidence chunks were flagged, especially across IEP pages classified as `other`. The lesson also had 4 low-confidence overview pages.

Privacy behavior:

- 49 PII items were redacted
- No over-redaction risk was reported

Recommended review:

- Inspect low-confidence chunks before relying on the final classroom output
- Cross-check specific accommodation language against the source IEP when parser confidence is low

## `get_teacher_output_template`

Returned the required structure for teacher-facing output:

- Student Support Summary
- Before the Lesson
- Opening
- During Reading
- Independent Practice
- Discussion
- Assessment
- Teacher Checklist

Each instructional section requires:

- Original task
- Student barrier
- IEP-documented support
- Recommended instructional scaffold
- Teacher action
- Student-facing scaffold

The template also requires privacy-safe and gender-neutral language, including `student-a`, `the student`, or `they/them`.

## Parameterized Tool Examples

The following tools require parameters and are useful for section-specific evidence:

```text
get_lesson_section(section_name="During Reading")
get_relevant_iep_context(section_name="During Reading", task_type="reading")
get_relevant_iep_context(section_name="Independent Practice", task_type="writing")
```

These calls demonstrate how Claude can retrieve targeted lesson sections and relevant IEP supports for a specific instructional task.
