from __future__ import annotations

LESSON_SECTION_SYNONYMS: dict[str, list[str]] = {
    "opening": ["opening", "launch", "warm-up", "do now", "engage", "anticipatory set", "intro", "introduction"],
    "direct_instruction": ["direct instruction", "teacher modeling", "i do", "mini lesson"],
    "guided_practice": ["guided practice", "we do", "collaborative practice"],
    "during_reading": ["during reading", "close reading", "read and annotate"],
    "independent_practice": ["independent practice", "you do", "student work time", "apply", "application"],
    "discussion": ["discussion", "share out", "student-led discussion", "partner talk"],
    "assessment": ["assessment", "exit ticket", "check for understanding", "quick write", "quiz", "reflection"],
}

LESSON_DEMAND_TAG_PATTERNS: dict[str, list[str]] = {
    "reading": ["read", "text", "passage", "annotate"],
    "vocabulary": ["vocabulary", "key term", "word meaning"],
    "comprehension": ["comprehension", "understand", "interpret", "main idea"],
    "central_idea": ["central idea", "main idea", "theme"],
    "writing": ["write", "written", "response", "paragraph"],
    "claim_evidence_reasoning": ["claim", "evidence", "reasoning", "cer"],
    "discussion": ["discuss", "partner", "share", "talk"],
    "assessment": ["assessment", "exit ticket", "quiz", "check for understanding"],
    "attention": ["focus", "attention", "sustain", "on-task"],
    "working_memory": ["multi-step", "remember", "track", "sequence"],
    "text_tracking": ["track text", "line by line", "annotate", "where in the text"],
}

IEP_NEED_TAG_PATTERNS: dict[str, list[str]] = {
    "reading_comprehension": ["reading comprehension", "comprehension", "main idea", "inference"],
    "vocabulary_support": ["vocabulary", "word meaning", "academic language"],
    "writing_support": ["written expression", "writing", "sentence", "paragraph"],
    "attention_support": ["attention", "focus", "on-task", "self-regulation", "behavior"],
    "organization_support": ["organization", "task completion", "planner", "executive function"],
}

IEP_SUPPORT_TAG_PATTERNS: dict[str, list[str]] = {
    "chunking": ["chunk", "break into parts"],
    "graphic_organizer": ["graphic organizer", "organizer"],
    "sentence_starter": ["sentence starter", "sentence frame"],
    "paragraph_frame": ["paragraph frame", "writing frame"],
    "extra_time": ["extra time", "extended time"],
    "repeated_directions": ["repeat directions", "repeated directions"],
    "visual_support": ["visual support", "visual cue", "anchor chart"],
    "vocabulary_preview": ["pre-teach vocabulary", "vocabulary preview"],
    "text_tracking_aid": ["text tracking", "line reader", "tracking aid"],
    "comprehension_check": ["comprehension check", "check for understanding"],
    "small_group": ["small group"],
    "one_to_one_checkin": ["1:1", "one-to-one", "check-in"],
    "breaks": ["break", "movement break"],
    "alternate_response": ["alternate response", "alternative response"],
    "oral_response": ["oral response", "verbal response"],
    "reduced_quantity": ["reduced quantity", "reduced workload"],
}

DEMAND_TO_SUPPORT_BRIDGE: dict[str, list[str]] = {
    "reading": ["chunking", "text_tracking_aid", "comprehension_check"],
    "vocabulary": ["vocabulary_preview", "visual_support"],
    "comprehension": ["graphic_organizer", "comprehension_check"],
    "central_idea": ["graphic_organizer", "chunking"],
    "writing": ["sentence_starter", "paragraph_frame", "graphic_organizer"],
    "claim_evidence_reasoning": ["paragraph_frame", "graphic_organizer"],
    "discussion": ["sentence_starter", "one_to_one_checkin"],
    "assessment": ["extra_time", "alternate_response", "oral_response"],
    "attention": ["breaks", "one_to_one_checkin", "repeated_directions"],
    "working_memory": ["chunking", "visual_support", "repeated_directions"],
    "text_tracking": ["text_tracking_aid", "chunking"],
}


def normalize_lesson_section_type(text: str) -> str:
    lowered = text.lower()
    for section_type, synonyms in LESSON_SECTION_SYNONYMS.items():
        if any(synonym in lowered for synonym in synonyms):
            return section_type
    return "unknown"


def infer_tags(text: str, patterns: dict[str, list[str]]) -> list[str]:
    lowered = text.lower()
    tags: list[str] = []
    for tag, keywords in patterns.items():
        if any(keyword in lowered for keyword in keywords):
            tags.append(tag)
    return tags


def infer_lesson_demand_tags(text: str, section_name: str = "") -> list[str]:
    joined = f"{section_name}\n{text}".strip()
    tags = infer_tags(joined, LESSON_DEMAND_TAG_PATTERNS)
    return tags or ["reading"]


def infer_iep_need_tags(text: str) -> list[str]:
    return infer_tags(text, IEP_NEED_TAG_PATTERNS)


def infer_iep_support_tags(text: str) -> list[str]:
    return infer_tags(text, IEP_SUPPORT_TAG_PATTERNS)


def infer_bridge_support_tags(demand_tags: list[str]) -> list[str]:
    supports: list[str] = []
    for demand_tag in demand_tags:
        supports.extend(DEMAND_TO_SUPPORT_BRIDGE.get(demand_tag, []))
    return list(dict.fromkeys(supports))

