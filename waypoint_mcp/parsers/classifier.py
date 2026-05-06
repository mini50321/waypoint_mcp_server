from __future__ import annotations

IEP_CATEGORIES: dict[str, list[str]] = {
    "present_levels": ["present level", "plaafp", "academic achievement", "functional performance"],
    "goals": ["annual goal", "measurable goal", "short-term objective", "benchmark"],
    "accommodations": ["accommodation", "supplementary aids", "program accommodations"],
    "modifications": ["modification", "modified assignment", "modified curriculum"],
    "assessment_supports": ["testing accommodation", "assessment accommodation", "state assessment"],
    "behavior_supports": ["behavior", "attention", "self-regulation", "break", "counseling"],
    "strengths": ["strength", "interests", "student strengths"],
}

LESSON_CATEGORIES: dict[str, list[str]] = {
    "overview": ["lesson", "unit", "grade", "subject"],
    "objectives": ["objective", "learning target", "students will", "i can"],
    "standards": ["standard", "ccss", "ri.", "rl.", "w.", "sl."],
    "materials": ["materials", "resources", "handout", "slide"],
    "vocabulary": ["vocabulary", "key terms", "academic vocabulary"],
    "lesson_section": [
        "opening",
        "intro",
        "during reading",
        "guided practice",
        "independent practice",
        "discussion",
        "exit ticket",
    ],
    "assessment": ["assessment", "exit ticket", "quiz", "independent practice"],
}


def classify_text_with_confidence(text: str, categories: dict[str, list[str]]) -> tuple[str, float]:
    text_lower = text.lower()
    scores = {
        category: sum(1 for keyword in keywords if keyword in text_lower)
        for category, keywords in categories.items()
    }
    best_category = max(scores, key=scores.get)
    total_score = sum(scores.values())
    if scores[best_category] == 0:
        return "other", 0.0
    confidence = scores[best_category] / max(total_score, 1)
    return best_category, round(confidence, 3)


def classify_text(text: str, categories: dict[str, list[str]]) -> str:
    category, _ = classify_text_with_confidence(text, categories)
    return category
