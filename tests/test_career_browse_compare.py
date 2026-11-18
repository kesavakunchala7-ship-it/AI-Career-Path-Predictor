import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from career_data import CAREERS, normalize_saved_career_ids, toggle_saved_career_id
from career_exploration import (
    add_comparison_career,
    career_field_values,
    catalog_filter_options,
    normalize_comparison_ids,
    remove_comparison_career,
    search_careers,
)
from recommendation_engine import rank_careers


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


class CareerBrowseCompareTests(unittest.TestCase):
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
            return_value=("https://accounts.google.com", "browse-test-subject"),
        )
        self.authenticated_user_patch.start()
        self.authenticated_name_patch.start()
        self.authenticated_identity_patch.start()
        self.addCleanup(self.authenticated_user_patch.stop)
        self.addCleanup(self.authenticated_name_patch.stop)
        self.addCleanup(self.authenticated_identity_patch.stop)

    def test_browsing_shows_the_complete_existing_catalog(self):
        results = search_careers(CAREERS)

        self.assertEqual(len(results), len(CAREERS))
        self.assertEqual(
            [career["id"] for career in results],
            [career["id"] for career in CAREERS],
        )

    def test_search_matches_existing_catalog_fields_case_insensitively(self):
        self.assertEqual(
            [career["id"] for career in search_careers(CAREERS, "DATA SCIENTIST")],
            ["data-scientist"],
        )
        self.assertIn(
            "data-scientist",
            [career["id"] for career in search_careers(CAREERS, "Python fundamentals")],
        )
        self.assertIn(
            "java-backend-developer",
            [career["id"] for career in search_careers(CAREERS, "Spring Boot")],
        )

    def test_catalog_filters_use_only_existing_skills_and_interests(self):
        skill_options = catalog_filter_options(CAREERS, "skills")
        interest_options = catalog_filter_options(CAREERS, "interests")

        self.assertIn("Python", skill_options)
        self.assertIn("Data Science", interest_options)
        self.assertEqual(catalog_filter_options(CAREERS, "salary"), [])
        filtered = search_careers(
            CAREERS,
            skill_filter="python",
            interest_filter="data science",
        )
        self.assertEqual(
            [career["id"] for career in filtered],
            ["data-scientist", "data-analyst"],
        )

    def test_empty_search_results_are_returned_without_error(self):
        self.assertEqual(search_careers(CAREERS, "unlisted career topic"), [])

    def test_comparison_selection_uses_unique_stable_career_ids(self):
        selected = add_comparison_career([], "data-scientist")
        selected = add_comparison_career(selected, "data-scientist")
        selected = add_comparison_career(selected, "data-analyst")

        self.assertEqual(selected, ["data-scientist", "data-analyst"])
        self.assertEqual(
            normalize_comparison_ids(
                ["data-scientist", "unknown", "data-scientist", "data-analyst"]
            ),
            ["data-scientist", "data-analyst"],
        )

    def test_comparison_career_can_be_removed(self):
        selected = remove_comparison_career(
            ["data-scientist", "data-analyst"],
            "data-scientist",
        )

        self.assertEqual(selected, ["data-analyst"])
        self.assertEqual(
            remove_comparison_career(selected, "data-scientist"),
            ["data-analyst"],
        )

    def test_missing_career_metadata_is_handled_safely(self):
        incomplete_careers = [
            {"id": "minimal"},
            {"id": "partial", "title": "Partial role", "skills": None},
        ]

        self.assertEqual(career_field_values(incomplete_careers[0], "skills"), ())
        self.assertEqual(career_field_values(incomplete_careers[1], "skills"), ())
        self.assertEqual(catalog_filter_options(incomplete_careers, "interests"), [])
        self.assertEqual(search_careers(incomplete_careers), incomplete_careers)
        self.assertEqual(search_careers(incomplete_careers, "missing phrase"), [])

    def test_existing_saved_career_behavior_remains_available(self):
        saved = toggle_saved_career_id([], "data-scientist")
        self.assertEqual(saved, ["data-scientist"])
        self.assertEqual(
            normalize_saved_career_ids(["Data Scientist", "data-scientist"]),
            ["data-scientist"],
        )
        self.assertEqual(
            toggle_saved_career_id(saved, "data-scientist"),
            [],
        )

    def test_browse_page_renders_every_career(self):
        app = self.create_browse_app()
        rendered_text = "\n".join(
            element.value
            for element in (*app.title, *app.subheader, *app.markdown)
        )

        for career in CAREERS:
            self.assertIn(career["title"], rendered_text)

    def test_browse_page_search_and_filter_update_visible_results(self):
        app = self.create_browse_app()
        app.text_input(key="career_browse_search").set_value("Spring Boot").run(timeout=20)
        self.assertTrue(
            any("Java Backend Developer" in element.value for element in app.subheader)
        )
        self.assertTrue(
            any("Showing 1 of 10 catalog careers." in element.value for element in app.caption)
        )

        app.text_input(key="career_browse_search").set_value("").run(timeout=20)
        app.selectbox(key="career_browse_skill").set_value("Cloud Computing").run(timeout=20)
        self.assertTrue(
            any("Cloud/DevOps Engineer" in element.value for element in app.subheader)
        )
        self.assertTrue(
            any("Showing 1 of 10 catalog careers." in element.value for element in app.caption)
        )

    def test_browse_page_shows_an_empty_state_for_unmatched_search(self):
        app = self.create_browse_app()
        app.text_input(key="career_browse_search").set_value("no-catalog-match").run(timeout=20)

        self.assertTrue(
            any(
                "No careers match those filters" in element.value
                for element in app.markdown
            )
        )

    def test_browse_page_adds_and_removes_comparison_selections(self):
        app = self.create_browse_app()
        add_button = self.button_by_key(app, "comparison_toggle_data-scientist")
        self.assertEqual(add_button.label, "Add to comparison")
        add_button.click().run(timeout=20)

        self.assertEqual(
            app.session_state["comparison_career_ids"],
            ["data-scientist"],
        )
        self.assertEqual(
            self.button_by_key(app, "comparison_toggle_data-scientist").label,
            "Remove from comparison",
        )
        self.button_by_key(app, "comparison_toggle_data-scientist").click().run(timeout=20)
        self.assertEqual(app.session_state["comparison_career_ids"], [])

    def test_browse_page_reuses_saved_career_and_roadmap_actions(self):
        app = self.create_browse_app()
        self.button_by_key(app, "browse_save_data-scientist").click().run(timeout=20)
        self.assertEqual(app.session_state["saved_careers"], ["data-scientist"])

        self.button_by_key(app, "browse_roadmap_data-scientist").click().run(timeout=20)
        self.assertEqual(app.session_state["page"], "Learning Roadmap")
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(
            any("Data Scientist" in element.value for element in app.title)
        )

    def test_browsing_and_comparison_do_not_change_recommendation_results(self):
        before = rank_careers(CAREERS, ["Python", "SQL"], ["Data Science"])
        selected = add_comparison_career([], "data-scientist")
        after = rank_careers(CAREERS, ["Python", "SQL"], ["Data Science"])

        self.assertEqual(selected, ["data-scientist"])
        self.assertEqual(
            [(item.career_id, item.score) for item in before],
            [(item.career_id, item.score) for item in after],
        )

    @staticmethod
    def button_by_key(app, key):
        return next(button for button in app.button if button.key == key)

    def create_browse_app(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=20)
        app.session_state["page"] = "Browse & Compare Careers"
        app.session_state["signed_in"] = True
        app.session_state["profile"] = {
            "name": "Browse Test",
            "confirmed_skills": [],
            "confirmed_interests": [],
        }
        app.run(timeout=20)
        self.assertEqual(len(app.exception), 0)
        return app


if __name__ == "__main__":
    unittest.main()
