import unittest
import tempfile
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch
from unittest.mock import MagicMock

from streamlit.testing.v1 import AppTest

from career_data import CAREERS
from learning_resources import group_resources_by_phase
from learning_resources import (
    CURATED_RESOURCES,
    RESOURCE_DIFFICULTIES,
    LearningResource,
    render_curated_resources,
    resources_for_career,
    validate_resource_catalog,
    verified_resource_url,
)
from recommendation_engine import rank_careers
from roadmap_progress import calculate_roadmap_progress, set_phase_completion

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


class LearningResourceTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path_patch = patch(
            "user_data_store.DATABASE_PATH",
            Path(self.temporary_directory.name) / "user-data.sqlite3",
        )
        self.database_path_patch.start()
        self.addCleanup(self.database_path_patch.stop)
        self.authenticated_user_patch = patch(
            "auth_utils.is_authenticated_user",
            return_value=True,
        )
        self.authenticated_name_patch = patch(
            "auth_utils.authenticated_user_name",
            return_value="Test Student",
        )
        self.authenticated_identity_patch = patch(
            "auth_utils.authenticated_user_identity",
            return_value=("https://accounts.google.com", "learning-test-subject"),
        )
        self.authenticated_user_patch.start()
        self.authenticated_name_patch.start()
        self.authenticated_identity_patch.start()
        self.addCleanup(self.authenticated_user_patch.stop)
        self.addCleanup(self.authenticated_name_patch.stop)
        self.addCleanup(self.authenticated_identity_patch.stop)
        self.valid_resource = LearningResource(
            resource_id="synthetic-python-reference",
            title="Synthetic Python Reference",
            provider_source="Synthetic Test Source",
            resource_type="documentation",
            url="https://resources.example.invalid/python",
            skill_tags=("Python",),
            gap_tags=("Deep Learning",),
            career_ids=("data-scientist",),
            phase_associations=(("data-scientist", "phase-1"),),
            verification_status="verified",
            verification_date=date.today().isoformat(),
            verification_source_url="https://evidence.example.invalid/verification",
            relevance_note="Synthetic test fixture; associated with the Python skill.",
            access_note="Synthetic test fixture; not an actual resource.",
            difficulty="Beginner",
        )

    def test_production_curated_catalog_contains_only_valid_verified_entries(self):
        self.assertEqual(len(CURATED_RESOURCES), 10)
        self.assertTrue(validate_resource_catalog(CURATED_RESOURCES).is_valid)
        self.assertEqual(
            {resource.resource_id for resource in CURATED_RESOURCES},
            {
                "python-tutorial",
                "scikit-learn-user-guide",
                "mdn-learn-web-development",
                "spring-boot-developing-reference",
                "pytorch-learn-the-basics",
                "pandas-intro-tutorials",
                "docker-build-share-containerized-app",
                "nist-incident-response-csf-profile",
                "playwright-api-testing",
                "android-basics-compose-course",
            },
        )
        self.assertTrue(
            all(resource.verification_status == "verified" for resource in CURATED_RESOURCES)
        )
        self.assertTrue(
            all(resource.difficulty in RESOURCE_DIFFICULTIES for resource in CURATED_RESOURCES)
        )
        self.assertEqual(
            {
                resource.resource_id: resource.difficulty
                for resource in CURATED_RESOURCES
            },
            {
                "python-tutorial": "Beginner",
                "scikit-learn-user-guide": "Intermediate",
                "mdn-learn-web-development": "Beginner",
                "spring-boot-developing-reference": "Intermediate",
                "pytorch-learn-the-basics": "Intermediate",
                "pandas-intro-tutorials": "Beginner",
                "docker-build-share-containerized-app": "Beginner",
                "nist-incident-response-csf-profile": "Advanced",
                "playwright-api-testing": "Intermediate",
                "android-basics-compose-course": "Beginner",
            },
        )
        self.assertTrue(all(resource.verification_date == "2026-10-24" for resource in CURATED_RESOURCES))
        self.assertEqual(
            len({resource.url for resource in CURATED_RESOURCES}),
            len(CURATED_RESOURCES),
        )
        self.assertEqual(
            {
                career["id"]: sum(
                    career["id"] in resource.career_ids
                    or any(
                        associated_career_id == career["id"]
                        for associated_career_id, _ in resource.phase_associations
                    )
                    for resource in CURATED_RESOURCES
                )
                for career in CAREERS
            },
            {career["id"]: 1 for career in CAREERS},
        )

    def test_each_production_resource_has_verified_career_and_phase_mapping(self):
        expected_mappings = {
            "python-tutorial": ("python-developer", "phase-1", ("Python",)),
            "scikit-learn-user-guide": (
                "data-scientist",
                "phase-2",
                ("Machine Learning",),
            ),
            "mdn-learn-web-development": (
                "full-stack-developer",
                "phase-1",
                ("HTML/CSS", "JavaScript"),
            ),
            "spring-boot-developing-reference": (
                "java-backend-developer",
                "phase-2",
                ("Spring Boot",),
            ),
            "pytorch-learn-the-basics": (
                "ai-ml-engineer",
                "phase-2",
                ("Python", "Machine Learning"),
            ),
            "pandas-intro-tutorials": (
                "data-analyst",
                "phase-2",
                ("Python", "Data Analysis"),
            ),
            "docker-build-share-containerized-app": (
                "cloud-devops-engineer",
                "phase-2",
                ("Docker",),
            ),
            "nist-incident-response-csf-profile": (
                "cybersecurity-analyst",
                "phase-2",
                (),
            ),
            "playwright-api-testing": (
                "software-tester-qa-engineer",
                "phase-2",
                ("Test Automation",),
            ),
            "android-basics-compose-course": (
                "mobile-app-developer",
                "phase-1",
                ("Kotlin", "Android Development"),
            ),
        }
        expected_urls = {
            "python-tutorial": "https://docs.python.org/3/tutorial/",
            "scikit-learn-user-guide": "https://scikit-learn.org/stable/user_guide.html",
            "mdn-learn-web-development": "https://developer.mozilla.org/en-US/docs/Learn_web_development",
            "spring-boot-developing-reference": "https://docs.spring.io/spring-boot/reference/using/index.html",
        }

        for resource in CURATED_RESOURCES:
            with self.subTest(resource_id=resource.resource_id):
                career_id, phase_id, skills = expected_mappings[resource.resource_id]
                self.assertTrue(validate_resource_catalog((resource,)).is_valid)
                self.assertEqual(resource.career_ids, (career_id,))
                self.assertEqual(resource.phase_associations, ((career_id, phase_id),))
                self.assertEqual(resource.skill_tags, skills)
                self.assertIn(resource.difficulty, RESOURCE_DIFFICULTIES)
                self.assertEqual(resource.verification_status, "verified")
                if resource.resource_id in expected_urls:
                    self.assertEqual(resource.url, expected_urls[resource.resource_id])
                self.assertEqual(
                    resources_for_career(CURATED_RESOURCES, career_id),
                    (resource,),
                )
                for other_career in CAREERS:
                    if other_career["id"] != career_id:
                        self.assertNotIn(
                            resource,
                            resources_for_career(
                                CURATED_RESOURCES,
                                other_career["id"],
                            ),
                        )
                groups = group_resources_by_phase(CURATED_RESOURCES, career_id)
                self.assertEqual(len(groups), 1)
                self.assertEqual(groups[0].phase_id, phase_id)
                self.assertEqual(groups[0].resources, (resource,))
                self.assertEqual(verified_resource_url(resource), resource.url)

    def test_actual_roadmap_page_renders_resources_only_for_associated_careers(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=20)
        self.assertEqual(len(app.exception), 0)
        app.session_state["page"] = "Learning Roadmap"
        app.session_state["signed_in"] = True
        app.session_state["profile"] = {
            "confirmed_skills": [],
            "confirmed_interests": [],
        }
        app.session_state["roadmap_progress"] = {}

        cases = (
            (
                "python-developer",
                "Python Developer",
                "python-tutorial",
                "The Python Tutorial",
                "Python documentation (docs.python.org)",
                "Introduces Python concepts, data structures, and program structure aligned with the roadmap's Python fundamentals phase.",
                "Phase 1 resources",
                "data-scientist",
            ),
            (
                "data-scientist",
                "Data Scientist",
                "scikit-learn-user-guide",
                "scikit-learn User Guide",
                "scikit-learn documentation (scikit-learn.org)",
                "Covers supervised-learning methods and model topics that align with the roadmap's introductory machine-learning practice phase.",
                "Phase 2 resources",
                "ai-ml-engineer",
            ),
            (
                "full-stack-developer",
                "Full Stack Developer",
                "mdn-learn-web-development",
                "Learn web development",
                "MDN Web Docs (developer.mozilla.org)",
                "MDN describes this learning area as front-end essentials; its web fundamentals align with the roadmap's HTML, CSS, and JavaScript phase.",
                "Phase 1 resources",
                "data-analyst",
            ),
            (
                "java-backend-developer",
                "Java Backend Developer",
                "spring-boot-developing-reference",
                "Developing with Spring Boot",
                "Spring Boot documentation (docs.spring.io)",
                "Covers developing with Spring Boot, including build systems and application configuration, aligned with the roadmap's Spring Boot practice phase.",
                "Phase 2 resources",
                "software-tester-qa-engineer",
            ),
            (
                "ai-ml-engineer",
                "AI/ML Engineer",
                "pytorch-learn-the-basics",
                "Learn the Basics",
                "PyTorch documentation (pytorch.org)",
                "Introduces an end-to-end machine-learning workflow in PyTorch, including data, model building, optimization, and saving models; it assumes basic Python and deep-learning familiarity.",
                "Phase 2 resources",
                "data-scientist",
            ),
            (
                "data-analyst",
                "Data Analyst",
                "pandas-intro-tutorials",
                "What kind of data does pandas handle?",
                "pandas documentation (pandas.pydata.org)",
                "The introductory tutorials use tabular datasets and pandas DataFrames, supporting the roadmap's data-cleaning and analysis practice.",
                "Phase 2 resources",
                "data-scientist",
            ),
            (
                "cloud-devops-engineer",
                "Cloud/DevOps Engineer",
                "docker-build-share-containerized-app",
                "Build and share a containerized application",
                "Docker documentation (docs.docker.com)",
                "A guided Docker tutorial covering containers, images, and a multi-container application stack, aligned with practicing container concepts.",
                "Phase 2 resources",
                "data-scientist",
            ),
            (
                "cybersecurity-analyst",
                "Cybersecurity Analyst",
                "nist-incident-response-csf-profile",
                "Incident Response Recommendations and Considerations for Cybersecurity Risk Management",
                "National Institute of Standards and Technology (NIST)",
                "NIST SP 800-61 Rev. 3 provides incident-response recommendations within the Cybersecurity Framework 2.0, relevant to defensive analysis and incident-response study.",
                "Phase 2 resources",
                "data-scientist",
            ),
            (
                "software-tester-qa-engineer",
                "Software Tester/QA Engineer",
                "playwright-api-testing",
                "API testing",
                "Playwright documentation (playwright.dev)",
                "Explains using Playwright's request context and test runner to exercise application REST APIs, matching the roadmap's API-testing practice.",
                "Phase 2 resources",
                "data-scientist",
            ),
            (
                "mobile-app-developer",
                "Mobile App Developer",
                "android-basics-compose-course",
                "Android Basics with Compose",
                "Android Developers (developer.android.com)",
                "A self-paced course introducing Kotlin and Jetpack Compose while building basic Android apps, matching the roadmap's mobile fundamentals.",
                "Phase 1 resources",
                "data-scientist",
            ),
        )

        for (
            career_id,
            career_title,
            resource_id,
            title,
            provider,
            relevance,
            phase_heading,
            unrelated_career_id,
        ) in cases:
            with self.subTest(career_id=career_id):
                app.session_state["selected_career_id"] = career_id
                app.session_state["selected_career"] = career_title
                app.run(timeout=20)
                self.assertEqual(len(app.exception), 0)

                rendered_text = "\n".join(
                    str(element.value)
                    for collection in (
                        app.title,
                        app.subheader,
                        app.markdown,
                        app.caption,
                    )
                    for element in collection
                    if hasattr(element, "value")
                )
                self.assertIn(title, rendered_text)
                self.assertIn(provider, rendered_text)
                self.assertIn(
                    f"Difficulty: {next(resource.difficulty for resource in CURATED_RESOURCES if resource.resource_id == resource_id)}",
                    rendered_text,
                )
                self.assertIn(relevance, rendered_text)
                self.assertIn(phase_heading, rendered_text)
                self.assertEqual(
                    sum(element.value == title for element in app.subheader),
                    1,
                )

                app.session_state["selected_career_id"] = unrelated_career_id
                unrelated_role = next(
                    career for career in CAREERS if career["id"] == unrelated_career_id
                )
                app.session_state["selected_career"] = unrelated_role["title"]
                app.run(timeout=20)
                self.assertEqual(len(app.exception), 0)
                unrelated_text = "\n".join(
                    str(element.value)
                    for collection in (
                        app.title,
                        app.subheader,
                        app.markdown,
                        app.caption,
                    )
                    for element in collection
                    if hasattr(element, "value")
                )
                self.assertNotIn(title, unrelated_text)

    def test_valid_resource_structure_and_existing_associations_are_accepted(self):
        result = validate_resource_catalog((self.valid_resource,))

        self.assertTrue(result.is_valid, result.errors)

    def test_existing_positional_access_note_field_order_is_preserved(self):
        resource = LearningResource(
            "synthetic-positional",
            "Synthetic positional fixture",
            "Synthetic Test Source",
            "reference",
            None,
            (),
            (),
            (),
            (),
            "unverified",
            None,
            "Legacy positional access note",
            difficulty="Beginner",
        )

        self.assertEqual(resource.access_note, "Legacy positional access note")
        self.assertIsNone(resource.verification_source_url)
        self.assertIsNone(resource.relevance_note)

    def test_duplicate_resource_ids_are_rejected_case_insensitively(self):
        duplicate = replace(self.valid_resource, resource_id="SYNTHETIC-PYTHON-REFERENCE")

        result = validate_resource_catalog((self.valid_resource, duplicate))

        self.assertFalse(result.is_valid)
        self.assertIn("duplicate resource ID", " ".join(result.errors))

    def test_missing_required_fields_are_reported(self):
        result = validate_resource_catalog(({"resource_id": "incomplete"},))

        self.assertFalse(result.is_valid)
        self.assertIn("title", " ".join(result.errors))
        self.assertIn("provider_source", " ".join(result.errors))
        self.assertIn("resource_type", " ".join(result.errors))
        self.assertIn("difficulty", " ".join(result.errors))
        self.assertIn("verification_status", " ".join(result.errors))

    def test_missing_difficulty_is_rejected(self):
        result = validate_resource_catalog(
            (replace(self.valid_resource, difficulty=None),)
        )

        self.assertFalse(result.is_valid)
        self.assertIn("difficulty", " ".join(result.errors))

    def test_unsupported_difficulty_is_rejected(self):
        result = validate_resource_catalog(
            (replace(self.valid_resource, difficulty="Expert"),)
        )

        self.assertFalse(result.is_valid)
        self.assertIn("unsupported difficulty", " ".join(result.errors))

    def test_missing_provider_information_is_rejected(self):
        result = validate_resource_catalog(
            (replace(self.valid_resource, provider_source=" "),)
        )

        self.assertIn("provider_source", " ".join(result.errors))

    def test_missing_verification_evidence_is_rejected_for_verified_resource(self):
        result = validate_resource_catalog(
            (replace(self.valid_resource, verification_source_url=None),)
        )

        self.assertIn("verification source URL", " ".join(result.errors))

    def test_missing_relevance_note_is_rejected_for_verified_resource(self):
        result = validate_resource_catalog(
            (replace(self.valid_resource, relevance_note=None),)
        )

        self.assertIn("relevance note", " ".join(result.errors))

    def test_missing_verification_date_is_rejected_for_verified_resource(self):
        result = validate_resource_catalog(
            (replace(self.valid_resource, verification_date=None),)
        )

        self.assertIn("verification date", " ".join(result.errors))

    def test_invalid_career_reference_is_rejected(self):
        resource = replace(self.valid_resource, career_ids=("unknown-career",))

        result = validate_resource_catalog((resource,))

        self.assertIn("unknown career", " ".join(result.errors))

    def test_invalid_phase_reference_is_rejected(self):
        resource = replace(
            self.valid_resource,
            phase_associations=(("data-scientist", "phase-9"),),
        )

        result = validate_resource_catalog((resource,))

        self.assertIn("unknown roadmap phase", " ".join(result.errors))

    def test_invalid_skill_and_gap_references_are_rejected(self):
        resource = replace(
            self.valid_resource,
            skill_tags=("Invented Skill",),
            gap_tags=("Invented Gap",),
        )

        result = validate_resource_catalog((resource,))

        self.assertIn("unknown skill", " ".join(result.errors))
        self.assertIn("unknown skill gap", " ".join(result.errors))

    def test_unverified_url_is_never_eligible_as_a_clickable_link(self):
        unverified = replace(
            self.valid_resource,
            verification_status="unverified",
            verification_date=None,
            verification_source_url=None,
            relevance_note=None,
        )

        self.assertTrue(validate_resource_catalog((unverified,)).is_valid)
        self.assertIsNone(verified_resource_url(unverified))
        self.assertEqual(
            resources_for_career((unverified,), "data-scientist"),
            (),
        )

        ui = MagicMock()
        render_curated_resources(ui, (unverified,), "data-scientist")

        ui.link_button.assert_not_called()
        ui.info.assert_called_once_with(
            "No curated resources match this career, its skills, or its roadmap phases yet."
        )

    def test_verified_synthetic_resource_renders_associations_and_link(self):
        ui = MagicMock()

        render_curated_resources(ui, (self.valid_resource,), "data-scientist")

        ui.subheader.assert_any_call("Synthetic Python Reference")
        ui.caption.assert_any_call(
            "Provider/source: Synthetic Test Source · Type: documentation · "
            "Difficulty: Beginner"
        )
        ui.write.assert_any_call(
            "Relevance: Synthetic test fixture; associated with the Python skill."
        )
        ui.link_button.assert_called_once_with(
            "Open verified resource",
            "https://resources.example.invalid/python",
        )
        rendered_associations = [call.args[0] for call in ui.write.call_args_list]
        self.assertTrue(any("Skills: Python" in value for value in rendered_associations))
        self.assertTrue(
            any("Skill gaps: Deep Learning" in value for value in rendered_associations)
        )
        self.assertTrue(
            any("Roadmap phases: Phase 1" in value for value in rendered_associations)
        )

    def test_resources_are_filtered_to_the_selected_career(self):
        other_career_resource = replace(
            self.valid_resource,
            resource_id="synthetic-java-reference",
            title="Synthetic Java Reference",
            skill_tags=(),
            gap_tags=(),
            career_ids=("java-backend-developer",),
            phase_associations=(("java-backend-developer", "phase-1"),),
        )

        selected = resources_for_career(
            (self.valid_resource, other_career_resource),
            "data-scientist",
        )

        self.assertEqual(selected, (self.valid_resource,))
        self.assertEqual(resources_for_career((self.valid_resource,), "unknown-career"), ())

    def test_explicit_career_scope_does_not_leak_through_shared_skill(self):
        resource = replace(
            self.valid_resource,
            skill_tags=("Python",),
            gap_tags=(),
            career_ids=("data-scientist",),
            phase_associations=(),
        )

        self.assertEqual(resources_for_career((resource,), "data-scientist"), (resource,))
        self.assertEqual(resources_for_career((resource,), "data-analyst"), ())

    def test_explicit_phase_scope_does_not_leak_through_shared_skill(self):
        resource = replace(
            self.valid_resource,
            career_ids=(),
            phase_associations=(("data-scientist", "phase-1"),),
        )

        self.assertEqual(resources_for_career((resource,), "data-scientist"), (resource,))
        self.assertEqual(resources_for_career((resource,), "data-analyst"), ())

    def test_global_skill_resource_matches_careers_with_that_catalog_skill(self):
        resource = replace(
            self.valid_resource,
            skill_tags=("Python",),
            gap_tags=(),
            career_ids=(),
            phase_associations=(),
        )

        matches = {
            career["id"]
            for career in CAREERS
            if resources_for_career((resource,), career["id"])
        }

        self.assertEqual(
            matches,
            {"data-scientist", "ai-ml-engineer", "data-analyst", "python-developer"},
        )

    def test_global_gap_resource_matches_careers_with_that_catalog_gap(self):
        resource = replace(
            self.valid_resource,
            skill_tags=(),
            gap_tags=("Deep Learning",),
            career_ids=(),
            phase_associations=(),
        )

        matches = {
            career["id"]
            for career in CAREERS
            if resources_for_career((resource,), career["id"])
        }

        self.assertEqual(matches, {"data-scientist", "ai-ml-engineer"})

    def test_phase_resources_are_grouped_by_actual_phase_id_without_duplicates(self):
        shared_tag_resource = replace(
            self.valid_resource,
            skill_tags=("Python",),
            gap_tags=("Deep Learning",),
        )

        groups = group_resources_by_phase(
            (shared_tag_resource,),
            "data-scientist",
        )

        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].phase_id, "phase-1")
        self.assertEqual(groups[0].resources, (shared_tag_resource,))

    def test_resources_without_phase_associations_are_unassigned(self):
        unassigned = replace(self.valid_resource, phase_associations=())

        groups = group_resources_by_phase((unassigned,), "data-scientist")

        self.assertEqual(len(groups), 1)
        self.assertIsNone(groups[0].phase_id)
        self.assertEqual(groups[0].resources, (unassigned,))
        ui = MagicMock()
        render_curated_resources(ui, (unassigned,), "data-scientist")
        ui.markdown.assert_any_call("#### Unassigned resources")

    def test_empty_catalog_renders_roadmap_empty_state(self):
        ui = MagicMock()

        render_curated_resources(ui, (), "data-scientist")

        ui.info.assert_called_once_with(
            "No verified curated resources are available for this area yet."
        )
        ui.link_button.assert_not_called()

    def test_nonempty_catalog_without_career_match_has_distinct_empty_state(self):
        unrelated = replace(
            self.valid_resource,
            career_ids=("data-scientist",),
            phase_associations=(),
            skill_tags=("Python",),
            gap_tags=(),
        )
        ui = MagicMock()

        render_curated_resources(ui, (unrelated,), "java-backend-developer")

        ui.info.assert_called_once_with(
            "No curated resources match this career, its skills, or its roadmap phases yet."
        )
        ui.link_button.assert_not_called()

    def test_resource_matching_and_rendering_do_not_duplicate_cards(self):
        multi_association_resource = replace(
            self.valid_resource,
            skill_tags=("Python",),
            gap_tags=("Deep Learning",),
            phase_associations=(
                ("data-scientist", "phase-1"),
                ("data-scientist", "phase-2"),
            ),
        )
        groups = group_resources_by_phase(
            (multi_association_resource,),
            "data-scientist",
        )
        ui = MagicMock()

        render_curated_resources(
            ui,
            (multi_association_resource,),
            "data-scientist",
        )

        self.assertEqual([group.phase_id for group in groups], ["phase-1", "phase-2"])
        self.assertEqual(resources_for_career((multi_association_resource,), "data-scientist"),
                         (multi_association_resource,))
        ui.subheader.assert_any_call("Synthetic Python Reference")
        self.assertEqual(
            sum(
                call.args == ("Synthetic Python Reference",)
                for call in ui.subheader.call_args_list
            ),
            1,
        )
        rendered_associations = [call.args[0] for call in ui.write.call_args_list]
        self.assertTrue(
            any("Roadmap phases: Phase 1, Phase 2" in value for value in rendered_associations)
        )

    def test_malformed_resource_data_fails_validation_without_raising(self):
        for resources in (None, "bad catalog", {"not": "a catalog"}, (object(),)):
            with self.subTest(resources=resources):
                result = validate_resource_catalog(resources)
                self.assertFalse(result.is_valid)

    def test_resource_rendering_does_not_change_roadmap_progress(self):
        progress_by_career = {}
        set_phase_completion(progress_by_career, "data-scientist", "phase-1", True)
        before = calculate_roadmap_progress(
            CAREERS[0]["roadmap"],
            progress_by_career["data-scientist"],
        )

        render_curated_resources(
            MagicMock(),
            (self.valid_resource,),
            "data-scientist",
        )
        after = calculate_roadmap_progress(
            CAREERS[0]["roadmap"],
            progress_by_career["data-scientist"],
        )

        self.assertEqual(after, before)

    def test_resource_catalog_does_not_change_recommendation_scores_or_order(self):
        before = rank_careers(CAREERS, ["Python", "SQL"], ["Data Science"])
        validation = validate_resource_catalog((self.valid_resource,))
        after = rank_careers(CAREERS, ["Python", "SQL"], ["Data Science"])

        self.assertTrue(validation.is_valid)
        self.assertEqual(
            [(item.career_id, item.score) for item in before],
            [(item.career_id, item.score) for item in after],
        )

    def test_curated_renderer_is_separate_from_gemini_suggestions(self):
        ui = MagicMock()

        render_curated_resources(ui, (self.valid_resource,), "data-scientist")

        rendered_text = " ".join(
            str(call.args[0])
            for method in (ui.markdown, ui.subheader, ui.caption, ui.write)
            for call in method.call_args_list
        )
        self.assertNotIn("AI-generated", rendered_text)
        self.assertNotIn("Gemini", rendered_text)

    def test_verified_url_requires_valid_https_and_verification_date(self):
        self.assertEqual(
            verified_resource_url(self.valid_resource),
            "https://resources.example.invalid/python",
        )
        insecure = replace(self.valid_resource, url="http://resources.example.invalid/python")
        missing_date = replace(self.valid_resource, verification_date=None)

        self.assertFalse(validate_resource_catalog((insecure,)).is_valid)
        self.assertFalse(validate_resource_catalog((missing_date,)).is_valid)

    def test_invalid_learner_and_evidence_urls_are_rejected(self):
        invalid_urls = (
            replace(self.valid_resource, url="http://resources.example.invalid/path"),
            replace(self.valid_resource, url="https:///missing-host"),
            replace(self.valid_resource, url="https://user:pass@resources.example.invalid/path"),
            replace(
                self.valid_resource,
                verification_source_url="http://evidence.example.invalid/check",
            ),
            replace(
                self.valid_resource,
                verification_source_url="https://evidence.example.invalid:bad/check",
            ),
        )

        for resource in invalid_urls:
            with self.subTest(resource=resource):
                self.assertFalse(validate_resource_catalog((resource,)).is_valid)
                self.assertIsNone(verified_resource_url(resource))

    def test_invalid_and_noncanonical_verification_dates_are_rejected(self):
        for invalid_date in ("2026-02-30", "20261024", "not-a-date"):
            with self.subTest(invalid_date=invalid_date):
                resource = replace(self.valid_resource, verification_date=invalid_date)
                self.assertIn(
                    "invalid verification date",
                    " ".join(validate_resource_catalog((resource,)).errors),
                )

    def test_future_verification_date_is_rejected(self):
        future_date = (date.today() + timedelta(days=1)).isoformat()
        resource = replace(self.valid_resource, verification_date=future_date)

        self.assertIn(
            "future verification date",
            " ".join(validate_resource_catalog((resource,)).errors),
        )

    def test_unknown_verification_status_is_rejected(self):
        resource = replace(self.valid_resource, verification_status="unavailable")

        self.assertIn(
            "unsupported verification status",
            " ".join(validate_resource_catalog((resource,)).errors),
        )


if __name__ == "__main__":
    unittest.main()
