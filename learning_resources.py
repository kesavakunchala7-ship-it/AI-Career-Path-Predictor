"""Validated, manually curated learning resources for career roadmaps."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date
from urllib.parse import urlsplit

from career_data import CAREERS
from roadmap_progress import roadmap_phase_entries

RESOURCE_TYPES = frozenset(
    {"documentation", "tutorial", "course", "book", "reference", "video"}
)
RESOURCE_DIFFICULTIES = frozenset({"Beginner", "Intermediate", "Advanced"})
VERIFICATION_STATUSES = frozenset({"verified", "unverified"})


@dataclass(frozen=True)
class LearningResource:
    resource_id: str
    title: str
    # Retained for compatibility; this identifies the resource provider/publisher.
    provider_source: str
    resource_type: str
    # Learner-facing destination; only rendered as a link after verification.
    url: str | None = None
    skill_tags: tuple[str, ...] = ()
    gap_tags: tuple[str, ...] = ()
    career_ids: tuple[str, ...] = ()
    phase_associations: tuple[tuple[str, str], ...] = ()
    verification_status: str = "unverified"
    verification_date: str | None = None
    access_note: str | None = None
    verification_source_url: str | None = None
    relevance_note: str | None = None
    difficulty: str | None = None


@dataclass(frozen=True)
class ResourceCatalogValidation:
    errors: tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        return not self.errors


@dataclass(frozen=True)
class ResourceGroup:
    phase_id: str | None
    resources: tuple[LearningResource, ...]


CURATED_RESOURCES: tuple[LearningResource, ...] = (
    LearningResource(
        resource_id="python-tutorial",
        title="The Python Tutorial",
        provider_source="Python documentation (docs.python.org)",
        resource_type="documentation",
        difficulty="Beginner",
        url="https://docs.python.org/3/tutorial/",
        skill_tags=("Python",),
        career_ids=("python-developer",),
        phase_associations=(("python-developer", "phase-1"),),
        verification_status="verified",
        verification_date="2026-10-24",
        verification_source_url="https://docs.python.org/3/tutorial/",
        relevance_note=(
            "Introduces Python concepts, data structures, and program structure "
            "aligned with the roadmap's Python fundamentals phase."
        ),
    ),
    LearningResource(
        resource_id="scikit-learn-user-guide",
        title="scikit-learn User Guide",
        provider_source="scikit-learn documentation (scikit-learn.org)",
        resource_type="documentation",
        difficulty="Intermediate",
        url="https://scikit-learn.org/stable/user_guide.html",
        skill_tags=("Machine Learning",),
        career_ids=("data-scientist",),
        phase_associations=(("data-scientist", "phase-2"),),
        verification_status="verified",
        verification_date="2026-10-24",
        verification_source_url="https://scikit-learn.org/stable/user_guide.html",
        relevance_note=(
            "Covers supervised-learning methods and model topics that align with "
            "the roadmap's introductory machine-learning practice phase."
        ),
    ),
    LearningResource(
        resource_id="mdn-learn-web-development",
        title="Learn web development",
        provider_source="MDN Web Docs (developer.mozilla.org)",
        resource_type="documentation",
        difficulty="Beginner",
        url="https://developer.mozilla.org/en-US/docs/Learn_web_development",
        skill_tags=("HTML/CSS", "JavaScript"),
        career_ids=("full-stack-developer",),
        phase_associations=(("full-stack-developer", "phase-1"),),
        verification_status="verified",
        verification_date="2026-10-24",
        verification_source_url="https://developer.mozilla.org/en-US/docs/Learn_web_development",
        relevance_note=(
            "MDN describes this learning area as front-end essentials; its web "
            "fundamentals align with the roadmap's HTML, CSS, and JavaScript phase."
        ),
    ),
    LearningResource(
        resource_id="spring-boot-developing-reference",
        title="Developing with Spring Boot",
        provider_source="Spring Boot documentation (docs.spring.io)",
        resource_type="documentation",
        difficulty="Intermediate",
        url="https://docs.spring.io/spring-boot/reference/using/index.html",
        skill_tags=("Spring Boot",),
        career_ids=("java-backend-developer",),
        phase_associations=(("java-backend-developer", "phase-2"),),
        verification_status="verified",
        verification_date="2026-10-24",
        verification_source_url="https://docs.spring.io/spring-boot/reference/using/index.html",
        relevance_note=(
            "Covers developing with Spring Boot, including build systems and "
            "application configuration, aligned with the roadmap's Spring Boot practice phase."
        ),
    ),
    LearningResource(
        resource_id="pytorch-learn-the-basics",
        title="Learn the Basics",
        provider_source="PyTorch documentation (pytorch.org)",
        resource_type="tutorial",
        url="https://docs.pytorch.org/tutorials/beginner/basics/intro.html",
        skill_tags=("Python", "Machine Learning"),
        gap_tags=("Deep Learning",),
        career_ids=("ai-ml-engineer",),
        phase_associations=(("ai-ml-engineer", "phase-2"),),
        verification_status="verified",
        verification_date="2026-10-24",
        verification_source_url="https://docs.pytorch.org/tutorials/beginner/basics/intro.html",
        relevance_note=(
            "Introduces an end-to-end machine-learning workflow in PyTorch, including "
            "data, model building, optimization, and saving models; it assumes basic "
            "Python and deep-learning familiarity."
        ),
        difficulty="Intermediate",
    ),
    LearningResource(
        resource_id="pandas-intro-tutorials",
        title="What kind of data does pandas handle?",
        provider_source="pandas documentation (pandas.pydata.org)",
        resource_type="tutorial",
        url="https://pandas.pydata.org/docs/getting_started/intro_tutorials/01_table_oriented.html",
        skill_tags=("Python", "Data Analysis"),
        career_ids=("data-analyst",),
        phase_associations=(("data-analyst", "phase-2"),),
        verification_status="verified",
        verification_date="2026-10-24",
        verification_source_url="https://pandas.pydata.org/docs/getting_started/intro_tutorials/01_table_oriented.html",
        relevance_note=(
            "The introductory tutorials use tabular datasets and pandas DataFrames, "
            "supporting the roadmap's data-cleaning and analysis practice."
        ),
        difficulty="Beginner",
    ),
    LearningResource(
        resource_id="docker-build-share-containerized-app",
        title="Build and share a containerized application",
        provider_source="Docker documentation (docs.docker.com)",
        resource_type="tutorial",
        url="https://docs.docker.com/get-started/tutorials/run-an-app/",
        skill_tags=("Docker",),
        career_ids=("cloud-devops-engineer",),
        phase_associations=(("cloud-devops-engineer", "phase-2"),),
        verification_status="verified",
        verification_date="2026-10-24",
        verification_source_url="https://docs.docker.com/get-started/tutorials/run-an-app/",
        relevance_note=(
            "A guided Docker tutorial covering containers, images, and a multi-container "
            "application stack, aligned with practicing container concepts."
        ),
        difficulty="Beginner",
    ),
    LearningResource(
        resource_id="nist-incident-response-csf-profile",
        title="Incident Response Recommendations and Considerations for Cybersecurity Risk Management",
        provider_source="National Institute of Standards and Technology (NIST)",
        resource_type="reference",
        url="https://csrc.nist.gov/pubs/sp/800/61/r3/final",
        gap_tags=("Incident Response", "Threat Analysis"),
        career_ids=("cybersecurity-analyst",),
        phase_associations=(("cybersecurity-analyst", "phase-2"),),
        verification_status="verified",
        verification_date="2026-10-24",
        verification_source_url="https://csrc.nist.gov/pubs/sp/800/61/r3/final",
        relevance_note=(
            "NIST SP 800-61 Rev. 3 provides incident-response recommendations within "
            "the Cybersecurity Framework 2.0, relevant to defensive analysis and "
            "incident-response study."
        ),
        difficulty="Advanced",
    ),
    LearningResource(
        resource_id="playwright-api-testing",
        title="API testing",
        provider_source="Playwright documentation (playwright.dev)",
        resource_type="documentation",
        url="https://playwright.dev/docs/api-testing",
        skill_tags=("Test Automation",),
        gap_tags=("API Testing",),
        career_ids=("software-tester-qa-engineer",),
        phase_associations=(("software-tester-qa-engineer", "phase-2"),),
        verification_status="verified",
        verification_date="2026-10-24",
        verification_source_url="https://playwright.dev/docs/api-testing",
        relevance_note=(
            "Explains using Playwright's request context and test runner to exercise "
            "application REST APIs, matching the roadmap's API-testing practice."
        ),
        difficulty="Intermediate",
    ),
    LearningResource(
        resource_id="android-basics-compose-course",
        title="Android Basics with Compose",
        provider_source="Android Developers (developer.android.com)",
        resource_type="course",
        url="https://developer.android.com/courses/android-basics-compose/course",
        skill_tags=("Kotlin", "Android Development"),
        career_ids=("mobile-app-developer",),
        phase_associations=(("mobile-app-developer", "phase-1"),),
        verification_status="verified",
        verification_date="2026-10-24",
        verification_source_url="https://developer.android.com/courses/android-basics-compose/course",
        relevance_note=(
            "A self-paced course introducing Kotlin and Jetpack Compose while building "
            "basic Android apps, matching the roadmap's mobile fundamentals."
        ),
        difficulty="Beginner",
    ),
)


def _field(resource: object, name: str, default: object = None) -> object:
    if isinstance(resource, Mapping):
        return resource.get(name, default)
    return getattr(resource, name, default)


def _string_values(value: object) -> tuple[str, ...] | None:
    if not isinstance(value, (list, tuple)):
        return None
    if any(not isinstance(item, str) or not item.strip() for item in value):
        return None
    return tuple(item.strip() for item in value)


def _valid_url(value: str) -> bool:
    try:
        parsed = urlsplit(value)
        return (
            not any(character.isspace() or ord(character) < 32 for character in value)
            and parsed.scheme.casefold() == "https"
            and bool(parsed.hostname)
            and parsed.username is None
            and parsed.password is None
            and (parsed.port is None or 1 <= parsed.port <= 65535)
        )
    except ValueError:
        return False


def _valid_iso_date(value: str) -> bool:
    try:
        parsed = date.fromisoformat(value)
        return parsed.isoformat() == value
    except ValueError:
        return False


def validate_resource_catalog(
    resources: object,
    careers: Iterable[Mapping[str, object]] = CAREERS,
) -> ResourceCatalogValidation:
    if (
        isinstance(resources, (str, bytes, Mapping))
        or not isinstance(resources, Iterable)
    ):
        return ResourceCatalogValidation(("Resource catalog must be a collection.",))

    career_list = list(careers)
    careers_by_id = {
        career["id"]: career
        for career in career_list
        if isinstance(career.get("id"), str) and career["id"].strip()
    }
    valid_skills = {
        value.casefold()
        for career in career_list
        for value in _string_values(career.get("skills", ())) or ()
    }
    valid_gaps = {
        value.casefold()
        for career in career_list
        for value in _string_values(career.get("gap", ())) or ()
    }
    seen_ids: set[str] = set()
    errors: list[str] = []

    for index, resource in enumerate(resources):
        prefix = f"Resource {index + 1}"
        if not isinstance(resource, (LearningResource, Mapping)):
            errors.append(f"{prefix} has an unsupported record structure.")
            continue

        required_fields = (
            "resource_id",
            "title",
            "provider_source",
            "resource_type",
            "difficulty",
            "verification_status",
        )
        values: dict[str, str] = {}
        for field_name in required_fields:
            value = _field(resource, field_name)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{prefix} is missing required field '{field_name}'.")
            else:
                values[field_name] = value.strip()

        resource_id = values.get("resource_id")
        if resource_id:
            normalized_id = resource_id.casefold()
            if normalized_id in seen_ids:
                errors.append(f"{prefix} has a duplicate resource ID.")
            seen_ids.add(normalized_id)

        resource_type = values.get("resource_type")
        if resource_type and resource_type not in RESOURCE_TYPES:
            errors.append(f"{prefix} has an unsupported resource type.")

        difficulty = values.get("difficulty")
        if difficulty and difficulty not in RESOURCE_DIFFICULTIES:
            errors.append(f"{prefix} has an unsupported difficulty level.")

        verification_status = values.get("verification_status")
        if verification_status and verification_status not in VERIFICATION_STATUSES:
            errors.append(f"{prefix} has an unsupported verification status.")

        url = _field(resource, "url")
        if url is not None:
            if not isinstance(url, str) or not url.strip() or not _valid_url(url.strip()):
                errors.append(f"{prefix} has an invalid URL; only valid HTTPS URLs are allowed.")

        verification_date = _field(resource, "verification_date")
        if verification_date is not None:
            if (
                not isinstance(verification_date, str)
                or not _valid_iso_date(verification_date)
            ):
                errors.append(f"{prefix} has an invalid verification date.")
            elif date.fromisoformat(verification_date) > date.today():
                errors.append(f"{prefix} has a future verification date.")
        if verification_status == "verified" and not verification_date:
            errors.append(f"{prefix} requires a verification date when verified.")

        verification_source_url = _field(resource, "verification_source_url")
        if verification_source_url is not None:
            if (
                not isinstance(verification_source_url, str)
                or not verification_source_url.strip()
                or not _valid_url(verification_source_url.strip())
            ):
                errors.append(
                    f"{prefix} has an invalid verification source URL; "
                    "only valid HTTPS URLs are allowed."
                )
        if verification_status == "verified" and not (
            isinstance(verification_source_url, str) and verification_source_url.strip()
        ):
            errors.append(f"{prefix} requires a verification source URL when verified.")

        relevance_note = _field(resource, "relevance_note")
        if relevance_note is not None and (
            not isinstance(relevance_note, str) or not relevance_note.strip()
        ):
            errors.append(f"{prefix} has an invalid relevance note.")
        if verification_status == "verified" and not (
            isinstance(relevance_note, str) and relevance_note.strip()
        ):
            errors.append(f"{prefix} requires a relevance note when verified.")

        access_note = _field(resource, "access_note")
        if access_note is not None and not isinstance(access_note, str):
            errors.append(f"{prefix} has an invalid access note.")

        skill_tags = _string_values(_field(resource, "skill_tags", ()))
        if skill_tags is None:
            errors.append(f"{prefix} has invalid skill associations.")
        elif any(value.casefold() not in valid_skills for value in skill_tags):
            errors.append(f"{prefix} references an unknown skill.")

        gap_tags = _string_values(_field(resource, "gap_tags", ()))
        if gap_tags is None:
            errors.append(f"{prefix} has invalid skill-gap associations.")
        elif any(value.casefold() not in valid_gaps for value in gap_tags):
            errors.append(f"{prefix} references an unknown skill gap.")

        career_ids = _string_values(_field(resource, "career_ids", ()))
        if career_ids is None:
            errors.append(f"{prefix} has invalid career associations.")
        elif any(career_id not in careers_by_id for career_id in career_ids):
            errors.append(f"{prefix} references an unknown career.")

        phase_associations = _field(resource, "phase_associations", ())
        if not isinstance(phase_associations, (list, tuple)):
            errors.append(f"{prefix} has invalid roadmap phase associations.")
            continue
        for association in phase_associations:
            if (
                not isinstance(association, (list, tuple))
                or len(association) != 2
                or not all(isinstance(value, str) and value.strip() for value in association)
            ):
                errors.append(f"{prefix} has a malformed roadmap phase association.")
                continue
            career_id, phase_id = (value.strip() for value in association)
            career = careers_by_id.get(career_id)
            if career is None:
                errors.append(f"{prefix} references an unknown career phase.")
                continue
            valid_phase_ids = {
                identifier
                for identifier, _ in roadmap_phase_entries(career.get("roadmap"))
            }
            if phase_id not in valid_phase_ids:
                errors.append(f"{prefix} references an unknown roadmap phase.")

    return ResourceCatalogValidation(tuple(errors))


def resources_for_career(
    resources: object,
    career_id: str,
    careers: Iterable[Mapping[str, object]] = CAREERS,
) -> tuple[LearningResource, ...]:
    career_list = list(careers)
    if (
        isinstance(resources, (str, bytes, Mapping))
        or not isinstance(resources, Iterable)
    ):
        return ()
    resource_list = tuple(resources)
    validation = validate_resource_catalog(resource_list, career_list)
    if not validation.is_valid:
        return ()

    career = next(
        (
            item for item in career_list
            if isinstance(item.get("id"), str) and item["id"] == career_id
        ),
        None,
    )
    if career is None:
        return ()

    career_skills = {
        value.casefold()
        for value in _string_values(career.get("skills", ())) or ()
    }
    career_gaps = {
        value.casefold()
        for value in _string_values(career.get("gap", ())) or ()
    }
    matching: list[LearningResource] = []
    for resource in resource_list:
        if isinstance(resource, LearningResource):
            entry = resource
        elif isinstance(resource, Mapping):
            entry = LearningResource(
                resource_id=_field(resource, "resource_id", ""),
                title=_field(resource, "title", ""),
                provider_source=_field(resource, "provider_source", ""),
                resource_type=_field(resource, "resource_type", ""),
                difficulty=_field(resource, "difficulty"),
                url=_field(resource, "url"),
                skill_tags=tuple(_field(resource, "skill_tags", ())),
                gap_tags=tuple(_field(resource, "gap_tags", ())),
                career_ids=tuple(_field(resource, "career_ids", ())),
                phase_associations=tuple(_field(resource, "phase_associations", ())),
                verification_status=_field(resource, "verification_status", ""),
                verification_date=_field(resource, "verification_date"),
                verification_source_url=_field(resource, "verification_source_url"),
                relevance_note=_field(resource, "relevance_note"),
                access_note=_field(resource, "access_note"),
            )
        else:
            continue
        if entry.verification_status != "verified":
            continue
        explicitly_scoped = bool(entry.career_ids or entry.phase_associations)
        directly_related = career_id in entry.career_ids
        phase_related = any(
            associated_career_id == career_id
            for associated_career_id, _ in entry.phase_associations
        )
        skill_related = bool(
            career_skills.intersection(value.casefold() for value in entry.skill_tags)
            or career_gaps.intersection(value.casefold() for value in entry.gap_tags)
        )
        if directly_related or phase_related or (not explicitly_scoped and skill_related):
            matching.append(entry)
    return tuple(matching)


def group_resources_by_phase(
    resources: object,
    career_id: str,
    careers: Iterable[Mapping[str, object]] = CAREERS,
) -> tuple[ResourceGroup, ...]:
    career_list = list(careers)
    career = next(
        (
            item for item in career_list
            if isinstance(item.get("id"), str) and item["id"] == career_id
        ),
        None,
    )
    if career is None:
        return ()

    phases = roadmap_phase_entries(career.get("roadmap"))
    phase_ids = {phase_id for phase_id, _ in phases}
    grouped: dict[str, list[LearningResource]] = {
        phase_id: [] for phase_id, _ in phases
    }
    unassigned: list[LearningResource] = []
    for resource in resources_for_career(resources, career_id, career_list):
        applicable_phase_ids = tuple(
            dict.fromkeys(
                phase_id
                for associated_career_id, phase_id in resource.phase_associations
                if associated_career_id == career_id and phase_id in phase_ids
            )
        )
        if applicable_phase_ids:
            for phase_id in applicable_phase_ids:
                if resource not in grouped[phase_id]:
                    grouped[phase_id].append(resource)
        elif resource not in unassigned:
            unassigned.append(resource)

    result = [
        ResourceGroup(phase_id, tuple(grouped[phase_id]))
        for phase_id, _ in phases
        if grouped[phase_id]
    ]
    if unassigned:
        result.append(ResourceGroup(None, tuple(unassigned)))
    return tuple(result)


def verified_resource_url(resource: object) -> str | None:
    if not validate_resource_catalog((resource,)).is_valid:
        return None
    if _field(resource, "verification_status") != "verified":
        return None
    url = _field(resource, "url")
    if isinstance(url, str) and url.strip() and _valid_url(url.strip()):
        return url.strip()
    return None


def render_curated_resources(
    ui: object,
    resources: object,
    career_id: str,
    careers: Iterable[Mapping[str, object]] = CAREERS,
) -> None:
    ui.markdown("### Curated learning resources")
    if (
        isinstance(resources, (str, bytes, Mapping))
        or not isinstance(resources, Iterable)
    ):
        ui.warning("Curated learning resources are unavailable because catalog validation failed.")
        ui.info("No verified curated resources are available for this area yet.")
        return
    resource_list = tuple(resources)
    validation = validate_resource_catalog(resource_list, careers)
    if not validation.is_valid:
        ui.warning("Curated learning resources are unavailable because catalog validation failed.")
        ui.info("No verified curated resources are available for this area yet.")
        return

    if not resource_list:
        ui.info("No verified curated resources are available for this area yet.")
        return

    groups = group_resources_by_phase(resource_list, career_id, careers)
    if not groups:
        ui.info("No curated resources match this career, its skills, or its roadmap phases yet.")
        return

    career = next(
        (
            item for item in careers
            if isinstance(item.get("id"), str) and item["id"] == career_id
        ),
        None,
    )
    phase_descriptions = dict(
        roadmap_phase_entries(career.get("roadmap")) if career is not None else ()
    )
    resource_ids_rendered: set[str] = set()
    for group in groups:
        new_resources = tuple(
            resource
            for resource in group.resources
            if resource.resource_id not in resource_ids_rendered
        )
        if not new_resources:
            continue
        if group.phase_id is None:
            ui.markdown("#### Unassigned resources")
        else:
            ui.markdown(f"#### {group.phase_id.replace('-', ' ').title()} resources")
            description = phase_descriptions.get(group.phase_id)
            if description:
                ui.caption(description)
        for resource in new_resources:
            resource_ids_rendered.add(resource.resource_id)
            ui.subheader(resource.title)
            ui.caption(
                f"Provider/source: {resource.provider_source} · "
                f"Type: {resource.resource_type} · "
                f"Difficulty: {resource.difficulty}"
            )
            if resource.relevance_note:
                ui.write(f"Relevance: {resource.relevance_note}")
            associations = []
            if resource.skill_tags:
                associations.append(f"Skills: {', '.join(resource.skill_tags)}")
            if resource.gap_tags:
                associations.append(f"Skill gaps: {', '.join(resource.gap_tags)}")
            associated_phases = tuple(
                dict.fromkeys(
                    phase_id
                    for associated_career_id, phase_id in resource.phase_associations
                    if associated_career_id == career_id
                )
            )
            if associated_phases:
                associations.append(
                    "Roadmap phases: "
                    + ", ".join(
                        phase_id.replace("-", " ").title()
                        for phase_id in associated_phases
                    )
                )
            if associations:
                ui.write(" · ".join(associations))
            if resource.access_note:
                ui.caption(f"Access note: {resource.access_note}")
            ui.caption(f"Verified on: {resource.verification_date}")
            url = verified_resource_url(resource)
            if url:
                ui.link_button("Open verified resource", url)
