from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass(slots=True)
class LessonData:
    lesson_id: str = "lesson-001"
    title: str | None = None
    grade: str | None = None
    subject: str | None = None
    unit: str | None = None
    standards: list[str] = field(default_factory=list)
    objective: list[str] = field(default_factory=list)
    objectives: list[str] = field(default_factory=list)
    essential_question: str | None = None
    skill_focus: str | None = None
    text_or_materials: list[str] = field(default_factory=list)
    materials: list[str] = field(default_factory=list)
    vocabulary: list[str] = field(default_factory=list)
    sections: list[dict[str, Any]] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)
    assessments: list[str] = field(default_factory=list)
    global_demands: list[str] = field(default_factory=list)
    lesson_demands: list[dict[str, Any]] = field(default_factory=list)
    parser_confidence: float = 0.0
    provenance: list[dict[str, Any]] = field(default_factory=list)
    raw_chunks: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
