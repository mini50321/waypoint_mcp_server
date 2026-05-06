from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass(slots=True)
class IEPData:
    student_alias: str = "student-a"
    official_enrolled_grade: str | None = None
    academic_performance_levels: list[dict[str, Any]] = field(default_factory=list)
    grade: str | None = None
    disability_category: str | None = None
    strengths: list[str] = field(default_factory=list)
    interests: list[str] = field(default_factory=list)
    present_levels: list[str] = field(default_factory=list)
    academic_needs: list[str] = field(default_factory=list)
    functional_needs: list[str] = field(default_factory=list)
    goals: list[str] = field(default_factory=list)
    accommodations: list[str] = field(default_factory=list)
    modifications: list[str] = field(default_factory=list)
    assessment_supports: list[str] = field(default_factory=list)
    behavior_supports: list[str] = field(default_factory=list)
    self_regulation_supports: list[str] = field(default_factory=list)
    assistive_technology: list[str] = field(default_factory=list)
    service_notes: list[str] = field(default_factory=list)
    privacy_redactions: dict[str, Any] = field(default_factory=dict)
    parser_confidence: float = 0.0
    provenance: list[dict[str, Any]] = field(default_factory=list)
    raw_chunks: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
