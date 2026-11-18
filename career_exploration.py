"""Helpers for browsing the curated catalog and selecting comparison careers."""

from collections.abc import Iterable, Mapping

from career_data import CAREERS

CAREER_SEARCH_FIELDS = ("title", "desc", "skills", "interests", "roadmap")


def career_field_values(career: Mapping[str, object], field: str) -> tuple[str, ...]:
    value = career.get(field)
    if isinstance(value, str):
        values = (value,)
    elif isinstance(value, (list, tuple)):
        values = value
    else:
        return ()

    return tuple(
        item.strip()
        for item in values
        if isinstance(item, str) and item.strip()
    )


def catalog_filter_options(
    careers: Iterable[Mapping[str, object]],
    field: str,
) -> list[str]:
    if field not in ("skills", "interests"):
        return []

    options: list[str] = []
    seen: set[str] = set()
    for career in careers:
        for value in career_field_values(career, field):
            key = value.casefold()
            if key not in seen:
                seen.add(key)
                options.append(value)
    return options


def search_careers(
    careers: Iterable[Mapping[str, object]],
    query: str = "",
    skill_filter: str = "",
    interest_filter: str = "",
) -> list[Mapping[str, object]]:
    search_term = query.strip().casefold()
    matching: list[Mapping[str, object]] = []

    for career in careers:
        if not isinstance(career, Mapping):
            continue
        if search_term and not any(
            search_term in value.casefold()
            for field in CAREER_SEARCH_FIELDS
            for value in career_field_values(career, field)
        ):
            continue
        if skill_filter and skill_filter.casefold() not in {
            value.casefold() for value in career_field_values(career, "skills")
        }:
            continue
        if interest_filter and interest_filter.casefold() not in {
            value.casefold() for value in career_field_values(career, "interests")
        }:
            continue
        matching.append(career)

    return matching


def normalize_comparison_ids(
    selected_ids: Iterable[object],
    careers: Iterable[Mapping[str, object]] = CAREERS,
) -> list[str]:
    if isinstance(selected_ids, str):
        selected_ids = (selected_ids,)

    known_ids = {
        career_id.strip()
        for career in careers
        if isinstance(career, Mapping)
        and isinstance(career_id := career.get("id"), str)
        and career_id.strip()
    }
    normalized: list[str] = []
    for career_id in selected_ids:
        if (
            isinstance(career_id, str)
            and career_id in known_ids
            and career_id not in normalized
        ):
            normalized.append(career_id)
    return normalized


def add_comparison_career(
    selected_ids: Iterable[object],
    career_id: str,
    careers: Iterable[Mapping[str, object]] = CAREERS,
) -> list[str]:
    career_list = list(careers)
    selected = normalize_comparison_ids(selected_ids, career_list)
    if career_id not in {
        item for career in career_list
        if isinstance(career, Mapping)
        and isinstance(item := career.get("id"), str)
    }:
        raise ValueError(f"Unknown career ID: {career_id}")
    if career_id not in selected:
        selected.append(career_id)
    return selected


def remove_comparison_career(
    selected_ids: Iterable[object],
    career_id: str,
    careers: Iterable[Mapping[str, object]] = CAREERS,
) -> list[str]:
    selected = normalize_comparison_ids(selected_ids, careers)
    if career_id in selected:
        selected.remove(career_id)
    return selected
