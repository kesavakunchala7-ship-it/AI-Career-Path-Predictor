# Main Logic Implementation

These sections reproduce the project's existing deterministic career-matching implementation. The code excerpts are from the source files named above each block; shared helper functions are referenced across sections rather than reimplemented differently.

## SCREENSHOT 1 – INPUT PROCESSING & SKILL MATCHING

**Original source: `main_logic.py`**

```python
from collections.abc import Iterable as IterableABC
from typing import Iterable


def normalize_label(value: str) -> str:
    """Collapse whitespace and ignore letter case when comparing labels."""
    return " ".join(value.split()).casefold()


def process_student_inputs(
    confirmed_skills: Iterable[object],
    confirmed_interests: Iterable[object],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Clean and de-duplicate student selections without changing display case.

    A string is treated as one selection, not an iterable of characters.
    Non-string entries are ignored, matching the existing engine's input rules.
    Non-iterable containers are rejected with a clear error.
    """
    for field_name, values in (
        ("confirmed_skills", confirmed_skills),
        ("confirmed_interests", confirmed_interests),
    ):
        if not isinstance(values, (str, IterableABC)):
            raise TypeError(f"{field_name} must be a string or an iterable of labels.")

    _, skills = _normalized_values(confirmed_skills)
    _, interests = _normalized_values(confirmed_interests)
    return skills, interests


def _normalized_values(values: Iterable[object]) -> tuple[set[str], tuple[str, ...]]:
    """Return normalized comparison keys and unique, readable input labels."""
    if isinstance(values, str):
        values = (values,)
    unique: dict[str, str] = {}
    for value in values:
        if isinstance(value, str):
            label = " ".join(value.split())
            if label:
                unique.setdefault(normalize_label(label), label)
    return set(unique), tuple(unique.values())


def _match_labels(
    confirmed_labels: Iterable[object],
    career_labels: Iterable[object],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Match unique normalized tags while retaining catalog display labels."""
    confirmed_keys, _ = _normalized_values(confirmed_labels)
    _, normalized_career_labels = _normalized_values(career_labels)
    matched = tuple(
        label for label in normalized_career_labels
        if normalize_label(label) in confirmed_keys
    )
    missing = tuple(
        label for label in normalized_career_labels
        if normalize_label(label) not in confirmed_keys
    )
    return matched, missing


def match_skills(
    confirmed_skills: Iterable[object],
    required_skills: Iterable[object],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return the matched and missing required skills for one career."""
    return _match_labels(confirmed_skills, required_skills)
```

**Original source: `career_data.py` — actual catalog skill requirements**

```python
"skills": ["Python", "Machine Learning", "Statistics", "SQL", "Data Analysis"],
"skills": ["Java", "SQL", "REST APIs", "Spring Boot", "Git"],
```

Input labels are whitespace-normalized, compared without case sensitivity, and deduplicated while retaining their readable display spelling. Skill matches are returned using the career catalog's labels, together with the required skills that were not matched.

## SCREENSHOT 2 – INTEREST MATCHING & SCORE CALCULATION

**Original source: `main_logic.py`**

```python
from math import isfinite

SKILL_WEIGHT = 0.70
INTEREST_WEIGHT = 0.30


def match_interests(
    confirmed_interests: Iterable[object],
    career_interests: Iterable[object],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return the matched and unmatched interest tags for one career."""
    return _match_labels(confirmed_interests, career_interests)


def calculate_weighted_career_score(
    skill_match: float | None,
    interest_match: float | None,
) -> float | None:
    """Combine match ratios into the app's 0-100 score, or return no score.

    Each component is a ratio from 0 to 1. Missing components produce no
    combined score; invalid or out-of-range ratios raise ``ValueError``.
    """
    if skill_match is None or interest_match is None:
        return None
    if (
        not isfinite(skill_match)
        or not isfinite(interest_match)
        or not 0 <= skill_match <= 1
        or not 0 <= interest_match <= 1
    ):
        raise ValueError("Skill and interest matches must be finite ratios from 0 to 1.")
    return (skill_match * SKILL_WEIGHT + interest_match * INTEREST_WEIGHT) * 100
```

Interest matching uses the same shared `_match_labels` helper shown in Screenshot 1. Each match component is a ratio from `0` to `1`, calculated in `rank_careers` as matched catalog tags divided by the career's unique tags. The existing weighted result is represented as a percentage from `0` to `100`:

**Career Score = (Skill Match × 0.70) + (Interest Match × 0.30)**

The project converts this weighted ratio to the displayed percentage by multiplying it by `100`.

## SCREENSHOT 3 – CAREER RANKING & RECOMMENDATION

**Original source: `main_logic.py`**

The full functions below are shown so the catalog-based recommendation and sorting logic are not truncated. They use the input, normalization, matching, and scoring helpers from Screenshots 1 and 2.

```python
from dataclasses import dataclass
from typing import Iterable, Mapping

from career_data import CAREERS


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


def recommend_careers(
    confirmed_skills: Iterable[str],
    confirmed_interests: Iterable[str],
) -> list[CareerRecommendation]:
    """Rank the project's actual curated careers for confirmed student inputs."""
    return rank_careers(CAREERS, confirmed_skills, confirmed_interests)


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
    normalized_skill_inputs, normalized_interest_inputs = process_student_inputs(
        confirmed_skills,
        confirmed_interests,
    )
    skill_keys, normalized_skills = _normalized_values(normalized_skill_inputs)
    interest_keys, normalized_interests = _normalized_values(normalized_interest_inputs)
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
        matched_skills, missing_skills = match_skills(
            confirmed_skill_keys,
            skill_labels,
        )
        matched_interests, _ = match_interests(
            confirmed_interest_keys,
            interest_labels,
        )

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
            calculate_weighted_career_score(skill_score, interest_score)
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

    # Scores sort descending; invalid scores follow, with stable metadata as tie-breakers.
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
```

`recommend_careers` passes the actual `CAREERS` catalog into `rank_careers`. The function creates one `CareerRecommendation` per catalog entry and returns the list sorted by descending score; unscored entries follow scored ones, with metadata tie-breakers for deterministic ordering. In `app.py`, the Results page calls this function and displays the score (to one decimal place out of 100), title, description, matched skills, matched interests, suggested skills, and explanation in recommendation cards. If there is no meaningful match, the UI shows a warning rather than presenting the catalog as a personalized ranking.
