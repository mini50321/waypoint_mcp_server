from __future__ import annotations

import re

from waypoint_mcp.models.iep import IEPData
from waypoint_mcp.parsers.chunker import chunk_pages
from waypoint_mcp.parsers.classifier import IEP_CATEGORIES, classify_text_with_confidence
from waypoint_mcp.parsers.taxonomy import infer_iep_need_tags, infer_iep_support_tags

_EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
_PHONE_RE = re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?){2}\d{4}\b")
_DOB_RE = re.compile(r"\b(?:dob|date of birth)\b.*", flags=re.IGNORECASE)
_ADDRESS_RE = re.compile(r"\b\d{1,6}\s+[A-Za-z0-9.\s]+\b(?:street|st|road|rd|ave|avenue|blvd|lane|ln)\b", re.IGNORECASE)
_STUDENT_ID_RE = re.compile(r"\b(student\s*id|id#|state\s*id)\b.*", flags=re.IGNORECASE)
_NAME_FIELD_RE = re.compile(r"^\s*(student\s*name|name|student)\s*:\s*.+$", flags=re.IGNORECASE)
_SCHOOL_FIELD_RE = re.compile(r"^\s*(school|district|campus)\s*:\s*.+$", flags=re.IGNORECASE)
_ID_FIELD_RE = re.compile(r"^\s*(student\s*id|id|state\s*id)\s*:\s*.+$", flags=re.IGNORECASE)
_ALNUM_ID_RE = re.compile(r"\b[A-Z0-9]{6,}\b")
_MULTI_NAME_RE = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b")

_NEED_PATTERNS: dict[str, list[str]] = {
    "reading comprehension": ["comprehension", "central idea", "main idea", "infer"],
    "vocabulary support": ["vocabulary", "academic language", "word meaning"],
    "written expression": ["written expression", "writing", "sentence", "paragraph"],
    "attention/self-regulation": ["attention", "focus", "self-regulation", "behavior", "break"],
    "organization/executive functioning": ["organization", "planner", "task completion", "executive function"],
}

_GRADE_WORDS: dict[str, str] = {
    "kindergarten": "K",
    "first": "1",
    "second": "2",
    "third": "3",
    "fourth": "4",
    "fifth": "5",
    "sixth": "6",
    "seventh": "7",
    "eighth": "8",
    "ninth": "9",
    "tenth": "10",
    "eleventh": "11",
    "twelfth": "12",
}


def _redact_pii_field_based(text: str) -> tuple[str, dict[str, int], int, int]:
    counters = {
        "name_redactions": 0,
        "id_redactions": 0,
        "school_redactions": 0,
        "contact_redactions": 0,
        "address_redactions": 0,
    }
    total_lines = len(text.splitlines()) or 1
    redacted_lines = 0

    def _sub_count(pattern: re.Pattern[str], replacement: str, value: str, counter_key: str) -> str:
        nonlocal redacted_lines
        updated, hits = pattern.subn(replacement, value)
        if hits > 0:
            counters[counter_key] += hits
            redacted_lines += hits
        return updated

    redacted = text
    redacted = _sub_count(_EMAIL_RE, "[redacted-email]", redacted, "contact_redactions")
    redacted = _sub_count(_PHONE_RE, "[redacted-phone]", redacted, "contact_redactions")
    redacted = _sub_count(_DOB_RE, "[redacted-dob]", redacted, "contact_redactions")
    redacted = _sub_count(_ADDRESS_RE, "[redacted-address]", redacted, "address_redactions")
    redacted = _sub_count(_STUDENT_ID_RE, "[redacted-student-id]", redacted, "id_redactions")

    for field_pattern, replacement, counter_key in (
        (re.compile(r"(student\s*name\s*:)\s*.+", flags=re.IGNORECASE), r"\1 [redacted-student-name]", "name_redactions"),
        (re.compile(r"(school\s*:)\s*.+", flags=re.IGNORECASE), r"\1 [redacted-school]", "school_redactions"),
        (re.compile(r"(district\s*:)\s*.+", flags=re.IGNORECASE), r"\1 [redacted-district]", "school_redactions"),
    ):
        redacted, hits = field_pattern.subn(replacement, redacted)
        if hits > 0:
            counters[counter_key] += hits
            redacted_lines += hits

    return redacted, counters, total_lines, redacted_lines


def _extract_blocked_terms(text: str) -> list[str]:
    blocked: set[str] = set()
    name_match = re.search(r"student\s*name\s*:\s*(.+)", text, flags=re.IGNORECASE)
    school_match = re.search(r"(?:school|district)\s*:\s*(.+)", text, flags=re.IGNORECASE)
    for match in (name_match, school_match):
        if not match:
            continue
        value = match.group(1).splitlines()[0]
        for token in re.findall(r"[A-Za-z][A-Za-z'-]{2,}", value):
            blocked.add(token.lower())
    return sorted(blocked)


def _sanitize_line(line: str) -> str:
    if _NAME_FIELD_RE.match(line):
        return "[redacted-student-name]"
    if _SCHOOL_FIELD_RE.match(line):
        return "[redacted-school]"
    if _ID_FIELD_RE.match(line):
        return "[redacted-student-id]"
    if "student" in line.lower() and _MULTI_NAME_RE.search(line):
        line = _MULTI_NAME_RE.sub("[redacted-student-name]", line)
    if any(token in line.lower() for token in ("school", "district", "campus")) and ":" in line:
        line = line.split(":", 1)[0] + ": [redacted-school]"
    if any(token in line.lower() for token in ("id", "student id", "state id")):
        line = _ALNUM_ID_RE.sub("[redacted-id]", line)
    return line.strip()


def _clean_lines(text: str) -> list[str]:
    lines = [line.strip("-*0123456789. ").strip() for line in text.splitlines()]
    sanitized = [_sanitize_line(line) for line in lines]
    return [
        line
        for line in sanitized
        if line and len(line) > 2 and line.lower() not in {"[redacted-student-name]", "[redacted-school]", "[redacted-student-id]"}
    ]


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


def _infer_need_tags(lines: list[str]) -> list[str]:
    joined = " ".join(lines).lower()
    needs: list[str] = []
    for need, keywords in _NEED_PATTERNS.items():
        if any(keyword in joined for keyword in keywords):
            needs.append(need)
    needs.extend(infer_iep_need_tags(" ".join(lines)))
    return list(dict.fromkeys(needs))


def _normalize_grade_token(text: str) -> str | None:
    lowered = text.lower().strip()
    digit_match = re.search(r"\b(\d{1,2})\b", lowered)
    if digit_match:
        return digit_match.group(1)
    for word, numeric in _GRADE_WORDS.items():
        if word in lowered:
            return numeric
    return None


def _extract_official_grade(full_text: str) -> str | None:
    patterns = [
        re.compile(r"\b(?:current\s+)?grade\s*[:\-]\s*([A-Za-z0-9 ]+)", flags=re.IGNORECASE),
        re.compile(r"\bstudent\s+is\s+in\s+([A-Za-z]+)\s+grade\b", flags=re.IGNORECASE),
        re.compile(r"\b([A-Za-z]+)\s+grade\b", flags=re.IGNORECASE),
    ]
    for pattern in patterns:
        for match in pattern.findall(full_text):
            candidate = _normalize_grade_token(str(match))
            if candidate:
                return candidate
    return None


def _extract_academic_performance_levels(lines: list[str]) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    domain_patterns: dict[str, list[str]] = {
        "math_performance_level": ["math", "numeracy", "i-ready math", "iready math"],
        "reading_level": ["reading", "reading level"],
        "vocabulary_level": ["vocabulary", "word knowledge"],
        "literature_comprehension_level": ["literature comprehension", "literary comprehension"],
        "informational_text_comprehension_level": ["informational text comprehension", "informational comprehension"],
    }
    for line in lines:
        lowered = line.lower()
        if "grade" not in lowered:
            continue
        grade_value = _normalize_grade_token(line)
        if not grade_value:
            continue
        for domain, keywords in domain_patterns.items():
            if any(keyword in lowered for keyword in keywords):
                results.append({"domain": domain, "reported_level": grade_value, "source_text": line[:220]})
                break
    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in results:
        key = (item["domain"], item["reported_level"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def parse_iep(pages: list[dict[str, object]], student_alias: str = "student-a") -> IEPData:
    chunks = chunk_pages("iep", pages)
    iep = IEPData(student_alias=student_alias)
    original_full_text = "\n".join(str(page.get("text", "")) for page in pages if page.get("text"))
    blocked_terms = _extract_blocked_terms(original_full_text)
    full_text, pii_counters, total_lines, redacted_lines = _redact_pii_field_based(original_full_text)
    full_lines = _clean_lines(full_text)
    iep.official_enrolled_grade = _extract_official_grade(original_full_text)
    iep.academic_performance_levels = _extract_academic_performance_levels(full_lines)

    for chunk in chunks:
        chunk.text, _, _, _ = _redact_pii_field_based(chunk.text)
        category, confidence = classify_text_with_confidence(chunk.text, IEP_CATEGORIES)
        chunk.category = category
        chunk.normalized_category = category
        chunk.confidence = confidence
        chunk.need_tags = infer_iep_need_tags(chunk.text)
        chunk.support_tags = infer_iep_support_tags(chunk.text)
        chunk_id = f"iep-{chunk.page:03d}-{len(iep.raw_chunks)+1:03d}"
        iep.provenance.append(
            {
                "chunk_id": chunk_id,
                "source": "iep",
                "page": chunk.page,
                "heading": chunk.heading,
                "confidence": confidence,
                "category": category,
            }
        )
        iep.raw_chunks.append(chunk.to_dict())

        lines = _clean_lines(chunk.text)
        if not lines:
            continue

        if category == "strengths":
            iep.strengths.extend(lines)
        elif category == "present_levels":
            iep.present_levels.extend(lines)
            iep.academic_needs.extend(_infer_need_tags(lines))
        elif category == "goals":
            iep.goals.extend(lines)
        elif category == "accommodations":
            iep.accommodations.extend(lines)
            iep.academic_needs.extend(chunk.need_tags or [])
        elif category == "modifications":
            iep.modifications.extend(lines)
        elif category == "assessment_supports":
            iep.assessment_supports.extend(lines)
        elif category == "behavior_supports":
            iep.behavior_supports.extend(lines)
            iep.academic_needs.extend(chunk.need_tags or [])
        else:
            lowered = " ".join(lines).lower()
            if any(word in lowered for word in ["goal", "objective", "benchmark"]):
                iep.goals.extend(lines)
            if any(word in lowered for word in ["accommodation", "support", "checklist", "graphic organizer"]):
                iep.accommodations.extend(lines)
            if any(word in lowered for word in ["present level", "functional performance", "current performance"]):
                iep.present_levels.extend(lines)
            if any(word in lowered for word in ["behavior", "regulation", "break", "counseling"]):
                iep.behavior_supports.extend(lines)
            if any(word in lowered for word in ["assessment", "testing", "extended time"]):
                iep.assessment_supports.extend(lines)

        iep.academic_needs.extend(_infer_need_tags(lines))
        iep.self_regulation_supports.extend(
            [line for line in lines if any(token in line.lower() for token in ("self-regulation", "break", "calm"))]
        )
        iep.service_notes.extend(
            [line for line in lines if any(token in line.lower() for token in ("service", "minutes", "frequency"))]
        )

    if iep.official_enrolled_grade:
        iep.grade = iep.official_enrolled_grade
    else:
        grade_match = re.search(r"\bgrade\s*(\d+)\b", full_text, flags=re.IGNORECASE)
        if grade_match:
            iep.grade = grade_match.group(1)

    disability_match = re.search(
        r"\b(disability|eligibility|exceptionality)\b\s*[:\-]?\s*([A-Za-z0-9 ,/()-]+)",
        full_text,
        flags=re.IGNORECASE,
    )
    if disability_match:
        iep.disability_category = disability_match.group(2).splitlines()[0].strip()

    if not iep.present_levels:
        iep.present_levels = [line for line in full_lines if "present" in line.lower() and "level" in line.lower()][:6]

    if not iep.goals:
        iep.goals = [line for line in full_lines if "goal" in line.lower()][:8]

    if not iep.accommodations:
        iep.accommodations = [
            line
            for line in full_lines
            if any(keyword in line.lower() for keyword in ["accommodation", "extra time", "checklist", "organizer"])
        ][:10]

    # Hard safety filter to prevent accidental PII in Claude-facing outputs.
    forbidden_markers = ("student name", "school:", "district:", "student id", "id:", "redacted-student-name", "redacted-school")
    iep.strengths = [line for line in iep.strengths if not any(marker in line.lower() for marker in forbidden_markers)]
    iep.present_levels = [line for line in iep.present_levels if not any(marker in line.lower() for marker in forbidden_markers)]
    iep.goals = [line for line in iep.goals if not any(marker in line.lower() for marker in forbidden_markers)]
    iep.accommodations = [line for line in iep.accommodations if not any(marker in line.lower() for marker in forbidden_markers)]
    iep.modifications = [line for line in iep.modifications if not any(marker in line.lower() for marker in forbidden_markers)]
    iep.assessment_supports = [
        line for line in iep.assessment_supports if not any(marker in line.lower() for marker in forbidden_markers)
    ]
    iep.behavior_supports = [line for line in iep.behavior_supports if not any(marker in line.lower() for marker in forbidden_markers)]

    iep.strengths = _dedupe_keep_order(iep.strengths)
    iep.present_levels = _dedupe_keep_order(iep.present_levels)
    iep.academic_needs = _dedupe_keep_order(iep.academic_needs)
    iep.goals = _dedupe_keep_order(iep.goals)
    iep.accommodations = _dedupe_keep_order(iep.accommodations)
    iep.modifications = _dedupe_keep_order(iep.modifications)
    iep.assessment_supports = _dedupe_keep_order(iep.assessment_supports)
    iep.behavior_supports = _dedupe_keep_order(iep.behavior_supports)
    iep.functional_needs = _dedupe_keep_order(
        [need for need in iep.academic_needs if "attention" in need or "organization" in need]
    )
    iep.self_regulation_supports = _dedupe_keep_order(iep.self_regulation_supports)
    iep.service_notes = _dedupe_keep_order(iep.service_notes)
    iep.privacy_redactions = {
        "student_name": True,
        "student_id": True,
        "school_name": True,
        **pii_counters,
        "count": sum(pii_counters.values()),
        "total_lines": total_lines,
        "redacted_lines": min(redacted_lines, total_lines),
        "redaction_ratio": round(min(redacted_lines, total_lines) / max(total_lines, 1), 3),
        "blocked_terms": blocked_terms,
    }
    all_confidences = [float(chunk.get("confidence", 0.0)) for chunk in iep.raw_chunks]
    iep.parser_confidence = round(sum(all_confidences) / len(all_confidences), 3) if all_confidences else 0.0

    return iep
