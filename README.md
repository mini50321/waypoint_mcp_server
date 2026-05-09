# Waypoint MCP Server

Python MCP server that helps Claude adapt a lesson for a student with an IEP.

The server loads a lesson file and an IEP file, parses both into stable educational schemas, matches lesson demands to student needs/supports, and exposes focused MCP tools/resources so Claude can generate teacher-ready lesson modifications.

---

## What This Project Does

Teachers often need to translate a long IEP into practical changes for tomorrow's lesson. This MCP server acts as the structured context layer between raw documents and Claude.

It:

- Loads lesson and IEP files from `data/`
- Supports PDF and plain text inputs
- Extracts and chunks document text
- Normalizes unstable lesson/IEP formats into stable schemas
- Redacts private student information from Claude-facing outputs
- Separates official enrolled grade from academic performance levels
- Separates IEP-documented supports from recommended instructional scaffolds
- Matches lesson demands to student needs and accommodations
- Exposes MCP tools/resources for Claude to generate a teacher-ready support plan

---

## Project Layout

```txt
waypoint_mcp/
├── server.py
├── data/
│   ├── lesson        # or lesson.pdf
│   └── iep           # or iep.pdf
├── loaders/
│   └── document loading + PDF/text extraction
├── models/
│   └── stable lesson/IEP schemas
├── parsers/
│   └── chunking, classification, normalization, redaction
├── resources/
│   └── MCP read-only resources
├── retrieval/
│   └── lesson demand ↔ IEP support matching
└── tools/
    └── MCP tools Claude can call
```

---

## Quick Start

### 1. Install dependencies

```bash
py -m pip install -e .
```

### 2. Add source files

Place lesson and IEP files in `data/`.

Supported options:

```txt
data/
├── lesson
└── iep
```

or:

```txt
data/
├── lesson.pdf
└── iep.pdf
```

The loader detects PDFs by extension or `%PDF-` file signature. Non-PDF files are read as plain text.

### 3. Run the server manually

```bash
py -m waypoint_mcp.server
```

Expected startup behavior:

```txt
[WAYPOINT_MCP] STARTING
[WAYPOINT_MCP] VALIDATING_INPUTS
[WAYPOINT_MCP] LOADING_DOCUMENTS
[WAYPOINT_MCP] PARSING_DOCUMENTS
[WAYPOINT_MCP] REGISTERING_MCP
[WAYPOINT_MCP] READY
[WAYPOINT_MCP] WAITING_FOR_CLIENT
```

Logs are written to `stderr` so MCP `stdio` communication remains safe.

---

## Environment Variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `WAYPOINT_LESSON_PATH` | `data/lesson` | Path to the lesson file |
| `WAYPOINT_IEP_PATH` | `data/iep` | Path to the IEP file |
| `WAYPOINT_STUDENT_ALIAS` | `student-a` | Privacy-safe student alias |

Example:

```bash
set WAYPOINT_LESSON_PATH=data/lesson.pdf
set WAYPOINT_IEP_PATH=data/iep.pdf
set WAYPOINT_STUDENT_ALIAS=student-a
```

---

## Claude Desktop Setup

Add the server to your Claude Desktop config.

On Windows, edit:

```txt
%APPDATA%\Claude\claude_desktop_config.json
```

Example config:

```json
{
  "mcpServers": {
    "waypoint": {
      "command": "py",
      "args": [
        "-m",
        "waypoint_mcp.server"
      ],
      "cwd": "ABSOLUTE_PATH_TO_PROJECT_ROOT",
      "env": {
        "WAYPOINT_LESSON_PATH": "ABSOLUTE_PATH_TO_PROJECT_ROOT\\data\\lesson",
        "WAYPOINT_IEP_PATH": "ABSOLUTE_PATH_TO_PROJECT_ROOT\\data\\iep",
        "WAYPOINT_STUDENT_ALIAS": "student-a"
      }
    }
  }
}
```

After saving the config, fully quit and reopen Claude Desktop.

Test the connection by asking Claude:

```txt
Use the Waypoint MCP server. What tools are available?
```

---

## Available MCP Tools

### `get_lesson_outline`

Returns the normalized lesson summary, including title, unit, subject, sections, vocabulary, assessments, and key instructional demands.

### `get_lesson_section`

Returns one lesson section by name.

### `analyze_lesson_demands`

Identifies what each lesson section requires from the student, such as reading, vocabulary, writing, discussion, assessment, attention, or text tracking.

### `get_student_profile`

Returns a privacy-safe student profile, including enrolled grade, performance levels, academic needs, present levels, goals, accommodations, and supports.

### `get_relevant_iep_context`

Given a lesson section and task type, returns relevant IEP needs, documented supports, and recommended scaffolds.

Example task types:

```txt
reading
writing
discussion
assessment
attention
self_regulation
```

### `compare_lesson_to_student_needs`

Maps lesson demands to student barriers, IEP-documented supports, and recommended instructional scaffolds.

### `get_teacher_output_template`

Returns the recommended structure for Claude's final teacher-facing response.

---

## Parser Strategy

IEPs and curriculum lessons do not follow one stable format, so the parser does not depend on exact page numbers or one fixed document template.

The parser pipeline is:

```txt
raw document
→ text extraction
→ chunking
→ classification
→ normalization
→ demand/support tagging
→ lesson-to-IEP matching
→ stable MCP context
```

### Lesson parsing

The lesson parser extracts:

- lesson title
- unit
- grade / subject
- objective
- essential question
- vocabulary
- lesson sections
- assessments
- section-level student tasks
- demand tags such as reading, vocabulary, writing, discussion, assessment, attention, and text tracking

### IEP parsing

The IEP parser extracts:

- privacy-safe student alias
- official enrolled grade
- academic performance levels
- strengths
- present levels
- academic needs
- functional needs
- goals
- accommodations
- assessment supports
- behavior/self-regulation supports
- service notes where relevant

It also separates:

```txt
official enrolled grade
≠
academic performance level
```

For example, a student may be officially enrolled in Grade 7 while performing at Grade 2 or 3 in specific reading domains.

---

## Safety and Privacy

The server redacts private student information before exposing data to Claude.

Claude-facing outputs use:

```txt
student-a
```

instead of real names or identifying details.

The server avoids exposing:

- student full name
- student ID
- date of birth
- address
- parent contact information
- signatures
- unnecessary administrative details

Educationally relevant values are preserved, such as:

- enrolled grade
- performance levels
- IEP goals
- accommodations
- service minutes
- assessment supports
- lesson standards
- lesson vocabulary

---

## IEP Supports vs. Recommended Scaffolds

The server distinguishes between two categories:

### IEP-documented supports

Supports explicitly found in the IEP, such as:

- frequent supervised breaks
- graphic organizer
- checklist
- reference sheet
- extended time
- 1:1 check-ins
- setting or scheduling supports

### Recommended instructional scaffolds

Teacher-facing strategies inferred from the lesson demand and student needs, such as:

- paragraph frames
- sentence starters
- oral rehearsal
- partner preparation
- vocabulary cards
- chunked reading checkpoints

This distinction helps teachers understand what is documented in the IEP versus what the system recommends instructionally.

---

## Example Claude Prompt

After connecting the MCP server to Claude Desktop, ask:

```txt
Use the Waypoint MCP server to create a teacher-ready modified lesson plan for this student.

Please:
1. Get the lesson outline.
2. Get the student profile.
3. Analyze lesson demands.
4. Compare lesson demands to student needs.
5. Get relevant IEP context for each major lesson section.
6. Use the teacher output template.
7. Generate a section-by-section support plan.

Do not include student PII.
Separate IEP-documented supports from recommended instructional scaffolds.
```

---

## Example Output Shape

Claude should produce a plan organized like this:

```txt
Teacher Recommendation Report

Student Profile
- Enrolled grade
- Academic performance levels
- Academic needs
- IEP-documented supports

Before the Lesson
- Barrier
- Teacher actions
- Student-facing scaffold

Opening
- Original task
- Student barrier
- IEP-documented support
- Recommended scaffold
- Teacher action

During Reading
- Original task
- Student barrier
- IEP-documented support
- Recommended scaffold
- Teacher action

Independent Practice
- Original task
- Student barrier
- IEP-documented support
- Recommended scaffold
- Teacher action

Discussion
- Original task
- Student barrier
- IEP-documented support
- Recommended scaffold
- Teacher action

Assessment
- Original task
- Student barrier
- IEP-documented support
- Recommended scaffold
- Teacher action

Teacher Checklist
```

---

## Example Output

See `examples/sample_output.md` for a concrete sample teacher-facing output generated from lesson and IEP context.

Additional example evidence:

- `examples/tool_discovery.md` shows Claude discovering the Waypoint MCP tools.
- `examples/tool_outputs.md` summarizes representative MCP tool outputs after loading the sample lesson and IEP.
- `examples/sample_output.md` shows the final teacher-facing differentiation plan.

---

## Evaluation Criteria Fit

### Output quality

The final output is designed for a teacher preparing tomorrow's lesson, not as a generic worksheet generator. It includes section-by-section barriers, IEP-documented supports, recommended scaffolds, teacher actions, student-facing scaffolds, and a classroom checklist.

Evidence:

- `examples/sample_output.md`
- `examples/tool_outputs.md`

### Architecture decisions

The server treats Claude as the reasoning and writing layer, while the MCP server provides structured, privacy-safe context. Lesson and IEP documents are normalized into stable schemas, then connected through demand/support tags so Claude can reason over focused context instead of receiving an entire raw IEP.

Evidence:

- `waypoint_mcp/models/`
- `waypoint_mcp/parsers/`
- `waypoint_mcp/retrieval/matcher.py`
- `waypoint_mcp/tools/`

### Code quality

The implementation is split into loaders, parsers, models, resources, retrieval, and tools. The test suite covers the highest-risk behavior: PII redaction, grade/performance-level parsing, lesson section extraction, demand analysis, and lesson-to-IEP matching.

Run tests:

```bash
py -m pip install -e ".[dev]"
py -m pytest
```

### Domain understanding

The system separates IEP-documented accommodations from recommended instructional scaffolds, distinguishes official enrolled grade from academic performance levels, preserves educationally relevant IEP context, redacts private information, and exposes parser warnings when confidence is low.

---

## Architecture Decisions

### Why normalize into stable schemas?

Lesson and IEP files are dynamic. Different schools, curricula, and IEP systems use different structures and labels.

Instead of relying on one fixed source format, the server maps varied document structures into stable internal schemas.

```txt
unstable documents
→ stable educational schema
→ predictable MCP tools
→ better Claude output
```

### Why use demand/support tags?

Lesson categories and IEP categories do not naturally match.

The server uses bridge tags to connect them.

Example:

```txt
Lesson demand:
reading, vocabulary, text tracking, central idea

IEP supports:
graphic organizer, checklist, reference sheet, breaks

Match:
During Reading → reading comprehension barrier → chunking + organizer + comprehension checks
```

### Why not dump the full IEP into Claude?

A full IEP is long, noisy, and contains private administrative information. Dumping the whole document can produce generic or unsafe outputs.

The server gives Claude focused context instead:

- lesson outline
- student profile
- relevant IEP supports
- section-level lesson demands
- matched lesson-to-IEP recommendations

---

## Testing Checklist

### Automated tests

Install test dependencies and run the focused pytest suite:

```bash
py -m pip install -e ".[dev]"
py -m pytest
```

The tests cover:

- IEP privacy redaction
- official enrolled grade vs academic performance levels
- lesson section extraction
- lesson demand analysis
- lesson-to-IEP support matching

### Claude Desktop checks

Use these prompts in Claude Desktop.

### Tool discovery

```txt
Use the Waypoint MCP server. What tools are available?
```

### Lesson outline

```txt
Call get_lesson_outline and summarize the lesson title, sections, vocabulary, and assessments.
```

### Student profile

```txt
Call get_student_profile and summarize the student needs and supports without PII.
```

### Demand analysis

```txt
Call analyze_lesson_demands and show section-level demands.
```

### Relevant IEP context

```txt
Call get_relevant_iep_context for During Reading with task_type="reading".
```

```txt
Call get_relevant_iep_context for Independent Practice with task_type="writing".
```

### Final end-to-end test

```txt
Use the Waypoint MCP server to generate a teacher-ready modified lesson plan.
Ground the plan in both the lesson and IEP.
Separate IEP-documented supports from recommended scaffolds.
Do not include student PII.
```

---

## Current Limitations

- Parser quality depends on text readability of source PDFs.
- Scanned/image-only PDFs are not supported unless OCR is added.
- Highly unusual IEP formats may produce low-confidence chunks.
- Some recommended scaffolds are pedagogical suggestions, not documented accommodations.
- Parser warnings should be reviewed when confidence is low or redaction volume is high.

---

## Mental Model

```txt
Server = context engine
Parser = meaning adapter
Matcher = lesson-to-IEP bridge
Claude = reasoning and writing layer
Teacher = final user
```

Unstable documents in. Stable educational context out. Teacher-ready plan generated by Claude.
