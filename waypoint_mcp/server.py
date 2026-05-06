from __future__ import annotations

import os
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from waypoint_mcp.loaders.iep_loader import load_iep_pages
from waypoint_mcp.loaders.lesson_loader import load_lesson_pages
from waypoint_mcp.parsers.context_builder import build_parsed_project_context
from waypoint_mcp.parsers.iep_parser import parse_iep
from waypoint_mcp.parsers.lesson_parser import parse_lesson
from waypoint_mcp.resources.iep_resources import register_iep_resources
from waypoint_mcp.resources.lesson_resources import register_lesson_resources
from waypoint_mcp.tools.iep_tools import register_iep_tools
from waypoint_mcp.tools.lesson_tools import register_lesson_tools
from waypoint_mcp.tools.modification_tools import register_modification_tools


def _log_state(state: str, detail: str = "") -> None:
    suffix = f" - {detail}" if detail else ""
    print(f"[WAYPOINT_MCP] {state}{suffix}", file=sys.stderr, flush=True)


def _get_config() -> dict[str, str]:
    return {
        "lesson_path": os.getenv("WAYPOINT_LESSON_PATH", "data/lesson"),
        "iep_path": os.getenv("WAYPOINT_IEP_PATH", "data/iep"),
        "student_alias": os.getenv("WAYPOINT_STUDENT_ALIAS", "student-a"),
    }


def _assert_files_exist(config: dict[str, str]) -> None:
    for key in ("lesson_path", "iep_path"):
        path = Path(config[key])
        if not path.exists():
            raise FileNotFoundError(f"Required file missing for {key}: {path}")


def create_server() -> FastMCP:
    _log_state("STARTING", "Reading configuration")
    config = _get_config()
    _log_state("VALIDATING_INPUTS", f"lesson={config['lesson_path']} iep={config['iep_path']}")
    _assert_files_exist(config)

    _log_state("LOADING_DOCUMENTS")
    lesson_payload = load_lesson_pages(config["lesson_path"])
    iep_payload = load_iep_pages(config["iep_path"])

    _log_state("PARSING_DOCUMENTS")
    lesson_data = parse_lesson(lesson_payload["pages"])
    iep_data = parse_iep(iep_payload["pages"], student_alias=config["student_alias"])
    parsed_context = build_parsed_project_context(
        lesson_data=lesson_data,
        iep_data=iep_data,
        lesson_path=config["lesson_path"],
        iep_path=config["iep_path"],
        lesson_pages=lesson_payload["pages"],
        iep_pages=iep_payload["pages"],
    )

    _log_state("REGISTERING_MCP", "Resources and tools")
    mcp = FastMCP("waypoint-special-education")
    register_lesson_resources(mcp, lesson_data)
    register_iep_resources(mcp, iep_data)

    register_lesson_tools(mcp, lesson_data)
    register_iep_tools(mcp, iep_data)
    register_modification_tools(mcp, lesson_data, iep_data, parsed_context=parsed_context)
    _log_state("READY", "Server initialized")
    return mcp


def main() -> None:
    server = create_server()
    _log_state("WAITING_FOR_CLIENT", "MCP stdio transport running")
    server.run()


if __name__ == "__main__":
    main()
