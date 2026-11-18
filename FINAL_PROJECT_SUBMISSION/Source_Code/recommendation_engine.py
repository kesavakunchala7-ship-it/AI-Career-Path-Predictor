"""Deterministic, explainable career ranking based on confirmed profile inputs.

The heuristic score is 70% skill relevance and 30% interest relevance. Both
components must be calculable for a score to be returned; missing inputs or
career metadata produce an explicitly unscored result instead of a default.
"""

from dataclasses import dataclass
from typing import Iterable, Mapping

SKILL_WEIGHT = 0.70
INTEREST_WEIGHT = 0.30


def normalize_label(value: str) -> str:
    """Normalize a label for comparison without changing its displayed form."""
    return " ".join(value.split()).casefold()


def compare_required_skills(
    confirmed_skills: Iterable[object],
    required_skills: Iterable[object],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return readable matched and missing required skills."""
    confirmed_keys = {
        normalize_label(value)
        for value in confirmed_skills
        if isinstance(value, str) and normalize_label(value)
    }
    required_by_key: dict[str, str] = {}
    for value in required_skills:
        if isinstance(value, str):
            label = " ".join(value.split())
            if label:
                required_by_key.setdefault(normalize_label(label), label)
    matched = tuple(label for key, label in required_by_key.items() if key in confirmed_keys)
    missing = tuple(label for key, label in required_by_key.items() if key not in confirmed_keys)
    return matched, missing


@dataclass(frozen=True)
class CareerRecommendation:
    career_id: str
    title: str
    icon: str
    description: str
    score: float | None
    skill_score: float | None
    interest_score: float | None
    matched_skills: tuple[str, ...]
    matched_interests: tuple[str, ...]
    missing_skills: tuple[str, ...]
    recommended_skills: tuple[str, ...]
    unrecognized_skills: tuple[str, ...]
    unrecognized_interests: tuple[str, ...]
    unavailable_components: tuple[str, ...]
    explanation: str


def has_meaningful_career_match(
    recommendations: Iterable[CareerRecommendation],
) -> bool:
    """Return whether any scored career matches at least one confirmed tag."""
    return any(
        recommendation.score is not None
        and recommendation.score > 0
        and (recommendation.matched_skills or recommendation.matched_interests)
        for recommendation in recommendations
    )


def _normalized_values(values: Iterable[object]) -> tuple[set[str], tuple[str, ...]]:
    if isinstance(values, str):
        values = (values,)
    unique: dict[str, str] = {}
    for value in values:
        if isinstance(value, str):
            label = " ".join(value.split())
            if label:
                unique.setdefault(normalize_label(label), label)
    return set(unique), tuple(unique.values())


def rank_careers(
    careers: Iterable[Mapping[str, object]],
    confirmed_skills: Iterable[str],
    confirmed_interests: Iterable[str],
) -> list[CareerRecommendation]:
    """Rank careers using confirmed inputs and return deterministic explanations.

    Skill and interest relevance are independently calculated as matched
    metadata values divided by the count of metadata values for that career.
    The weighted score is only emitted when both confirmed inputs and both
    nonempty metadata components are available.
    """
    skill_keys, normalized_skills = _normalized_values(confirmed_skills)
    interest_keys, normalized_interests = _normalized_values(confirmed_interests)
    confirmed_skill_keys = set(skill_keys)
    confirmed_interest_keys = set(interest_keys)

    career_list = list(careers)
    id_counts: dict[str, int] = {}
    for career in career_list:
        raw_id = career.get("id")
        if isinstance(raw_id, str) and raw_id.strip():
            career_id = raw_id.strip()
            id_counts[career_id] = id_counts.get(career_id, 0) + 1

    results: list[CareerRecommendation] = []
    for career in career_list:
        raw_id = career.get("id")
        raw_title = career.get("title")
        career_id = raw_id.strip() if isinstance(raw_id, str) else ""
        title = raw_title.strip() if isinstance(raw_title, str) else ""
        icon = career.get("icon")
        description = career.get("desc")
        icon = icon if isinstance(icon, str) else ""
        description = description if isinstance(description, str) else ""

        metadata_issues: list[str] = []
        if not career_id:
            metadata_issues.append("career identifier")
        elif id_counts[career_id] > 1:
            metadata_issues.append("unique career identifier")
        if not title:
            metadata_issues.append("career title")

        required_skills = career.get("skills")
        if not isinstance(required_skills, (list, tuple)) or not required_skills:
            required_skills = ()
            metadata_issues.append("required skills")
        elif not all(isinstance(value, str) and value.strip() for value in required_skills):
            required_skills = tuple(
                value.strip() for value in required_skills
                if isinstance(value, str) and value.strip()
            )
            metadata_issues.append("valid required skills")

        career_interests = career.get("interests")
        if not isinstance(career_interests, (list, tuple)) or not career_interests:
            career_interests = ()
            metadata_issues.append("interest tags")
        elif not all(isinstance(value, str) and value.strip() for value in career_interests):
            career_interests = tuple(
                value.strip() for value in career_interests
                if isinstance(value, str) and value.strip()
            )
            metadata_issues.append("valid interest tags")

        skill_labels_by_key: dict[str, str] = {}
        for value in required_skills:
            label = " ".join(value.split())
            skill_labels_by_key.setdefault(normalize_label(label), label)
        interest_labels_by_key: dict[str, str] = {}
        for value in career_interests:
            label = " ".join(value.split())
            interest_labels_by_key.setdefault(normalize_label(label), label)
        skill_labels = tuple(skill_labels_by_key.values())
        interest_labels = tuple(interest_labels_by_key.values())
        matched_skills = tuple(value for key, value in skill_labels_by_key.items() if key in confirmed_skill_keys)
        matched_interests = tuple(value for key, value in interest_labels_by_key.items() if key in confirmed_interest_keys)
        missing_skills = tuple(value for key, value in skill_labels_by_key.items() if key not in confirmed_skill_keys)

        raw_recommended = career.get("gap", ())
        gap_skills = raw_recommended if isinstance(raw_recommended, (list, tuple)) else ()
        recommended_by_key: dict[str, str] = {}
        for value in (*missing_skills, *gap_skills):
            if isinstance(value, str):
                label = " ".join(value.split())
                key = normalize_label(label)
                if label and key not in confirmed_skill_keys:
                    recommended_by_key.setdefault(key, label)
        recommended_skills = tuple(recommended_by_key.values())

        unrecognized_skills = tuple(
            value for value in normalized_skills
            if normalize_label(value) not in skill_labels_by_key
        )
        unrecognized_interests = tuple(
            value for value in normalized_interests
            if normalize_label(value) not in interest_labels_by_key
        )

        unavailable: list[str] = []
        if not confirmed_skill_keys:
            unavailable.append("confirmed skills")
        elif not skill_labels:
            unavailable.append("required-skill metadata")
        if not confirmed_interest_keys:
            unavailable.append("confirmed interests")
        elif not interest_labels:
            unavailable.append("interest-tag metadata")
        if metadata_issues:
            unavailable.extend(metadata_issues)

        skill_score = (
            len(matched_skills) / len(skill_labels)
            if skill_labels and confirmed_skill_keys else None
        )
        interest_score = (
            len(matched_interests) / len(interest_labels)
            if interest_labels and confirmed_interest_keys else None
        )
        score = (
            (skill_score * SKILL_WEIGHT + interest_score * INTEREST_WEIGHT) * 100
            if skill_score is not None
            and interest_score is not None
            and not metadata_issues
            else None
        )

        if score is None:
            reasons = ", ".join(dict.fromkeys(unavailable)) or "complete input and career metadata"
            explanation = f"No heuristic score is available because {reasons} are unavailable."
        else:
            explanation = (
                f"Matched {len(matched_skills)} of {len(skill_labels)} required skills "
                f"and {len(matched_interests)} of {len(interest_labels)} interest tags. "
                "The score weights skill relevance at 70% and interest relevance at 30%."
            )
            if unrecognized_skills or unrecognized_interests:
                explanation += " Inputs without matching tags do not contribute to this score."

        results.append(CareerRecommendation(
            career_id=career_id,
            title=title or "Career metadata unavailable",
            icon=icon,
            description=description,
            score=score,
            skill_score=skill_score,
            interest_score=interest_score,
            matched_skills=matched_skills,
            matched_interests=matched_interests,
            missing_skills=missing_skills,
            recommended_skills=recommended_skills,
            unrecognized_skills=unrecognized_skills,
            unrecognized_interests=unrecognized_interests,
            unavailable_components=tuple(dict.fromkeys(unavailable)),
            explanation=explanation,
        ))

    return sorted(
        results,
        key=lambda result: (
            result.score is None,
            -(result.score if result.score is not None else 0.0),
            result.career_id,
            result.title.casefold(),
            result.description.casefold(),
            result.icon,
            result.matched_skills,
            result.matched_interests,
            result.missing_skills,
            result.recommended_skills,
            result.unavailable_components,
        ),
    )
