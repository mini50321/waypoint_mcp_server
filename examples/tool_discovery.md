# MCP Tool Discovery

This example captures Claude's tool-discovery response after the Waypoint MCP server was connected. The important signal is that Claude can see the project-specific Waypoint tools for lesson context, IEP context, demand/support matching, parser warnings, and teacher-facing output structure.

## Waypoint Tools Discovered

```text
Waypoint (MCP Server)
- get_lesson_outline — Returns lesson objective, sections, activities, and assessment
- get_lesson_section — Fetches a specific lesson section by name
- analyze_lesson_demands — Analyzes what each section requires from the student
- get_relevant_iep_context — Returns IEP supports relevant to a lesson section and task type
- get_student_profile — Returns student strengths, present levels, goals, and accommodations
- get_parsed_project_context — Returns full normalized lesson/IEP context and match summary
- get_parser_warnings — Returns parser warnings, confidence issues, and redaction counts
- get_teacher_output_template — Returns the final response structure for teacher-facing output
- compare_lesson_to_student_needs — Connects lesson demands to IEP needs and supports
```

## Full Claude Discovery Response

```text
Here are all the tools I currently have available:

Waypoint (MCP Server)
- get_lesson_outline — Returns lesson objective, sections, activities, and assessment
- get_lesson_section — Fetches a specific lesson section by name
- analyze_lesson_demands — Analyzes what each section requires from the student
- get_relevant_iep_context — Returns IEP supports relevant to a lesson section and task type
- get_student_profile — Returns student strengths, present levels, goals, and accommodations
- get_parsed_project_context — Returns full normalized lesson/IEP context and match summary
- get_parser_warnings — Returns parser warnings, confidence issues, and redaction counts
- get_teacher_output_template — Returns the final response structure for teacher-facing output
- compare_lesson_to_student_needs — Connects lesson demands to IEP needs and supports

Web & Search
- web_search — Search the web for current information
- web_fetch — Fetch the contents of a specific URL
- image_search — Search for images on the web

Maps & Places
- places_search — Search for businesses, restaurants, attractions via Google Places
- places_map_display — Display locations on an interactive map

Weather
- weather_fetch — Get current weather for a location

Sports
- fetch_sports_data — Get scores, standings, and game stats for major leagues

Productivity & Messaging
- message_compose — Draft emails, Slack messages, or texts with strategic approaches
- ask_user_input — Present interactive option buttons to gather preferences

Creative & Visual
- visualize:show_widget — Render inline SVG diagrams, charts, or interactive HTML
- image_search — Find and display images

File & Code (Computer Use)
- bash_tool — Run bash commands in a Linux container
- create_file — Create new files
- str_replace — Edit files
- view — View files and directories
- present_files — Share files for the user to download

Recipes
- recipe_display — Show an interactive, scalable recipe widget

MCP Registry
- search_mcp_registry — Search for available MCP connectors
- suggest_connectors — Present connector options to the user
```

## Why This Matters

This verifies that the MCP server is connected successfully and that Claude can discover the tools needed to turn lesson and IEP data into a teacher-ready differentiation plan.