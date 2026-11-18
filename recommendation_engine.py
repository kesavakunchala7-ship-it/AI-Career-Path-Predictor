"""Backward-compatible imports for the career logic in :mod:`main_logic`."""

from main_logic import (
    INTEREST_WEIGHT,
    SKILL_WEIGHT,
    CareerRecommendation,
    calculate_weighted_career_score,
    compare_required_skills,
    has_meaningful_career_match,
    match_interests,
    match_skills,
    normalize_label,
    process_student_inputs,
    rank_careers,
    recommend_careers,
)

__all__ = [
    "INTEREST_WEIGHT",
    "SKILL_WEIGHT",
    "CareerRecommendation",
    "calculate_weighted_career_score",
    "compare_required_skills",
    "has_meaningful_career_match",
    "match_interests",
    "match_skills",
    "normalize_label",
    "process_student_inputs",
    "rank_careers",
    "recommend_careers",
]
