from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from waypoint_mcp.models.iep import IEPData
from waypoint_mcp.models.lesson import LessonData


@dataclass(slots=True)
class ParsedProjectContext:
    source_summary: dict[str, Any] = field(default_factory=dict)
    lesson: LessonData = field(default_factory=LessonData)
    iep: IEPData = field(default_factory=IEPData)
    matches: list[dict[str, Any]] = field(default_factory=list)
    parser_warnings: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
