"""Progress helpers for illustrative career roadmaps."""

from collections.abc import MutableMapping, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class RoadmapProgress:
    total: int
    completed: int
    remaining: int
    percentage: float


def roadmap_phase_entries(roadmap: object) -> tuple[tuple[str, str], ...]:
    if isinstance(roadmap, (str, bytes)) or not isinstance(roadmap, Sequence):
        return ()

    return tuple(
        (f"phase-{index + 1}", description)
        for index, description in enumerate(roadmap)
        if isinstance(description, str) and description.strip()
    )


def calculate_roadmap_progress(
    roadmap: object,
    completed_phase_ids: object,
) -> RoadmapProgress:
    phase_ids = {phase_id for phase_id, _ in roadmap_phase_entries(roadmap)}
    if isinstance(completed_phase_ids, (list, tuple, set, frozenset)):
        completed_ids = phase_ids.intersection(completed_phase_ids)
    else:
        completed_ids = set()

    total = len(phase_ids)
    completed = len(completed_ids)
    percentage = round(completed * 100 / total, 1) if total else 0.0
    return RoadmapProgress(
        total=total,
        completed=completed,
        remaining=total - completed,
        percentage=percentage,
    )


def set_phase_completion(
    progress_by_career: MutableMapping[str, list[str]],
    career_id: str,
    phase_id: str,
    completed: bool,
) -> None:
    completed_ids = progress_by_career.setdefault(career_id, [])
    if completed:
        if phase_id not in completed_ids:
            completed_ids.append(phase_id)
    elif phase_id in completed_ids:
        completed_ids.remove(phase_id)
