import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

import user_data_store
from career_data import CAREERS, assessment_interest_options, assessment_skill_options
from user_data_store import (
    delete_user_data,
    load_user_data,
    save_profile,
    set_roadmap_phase,
    set_saved_career,
)


ISSUER = "https://accounts.google.com"
SUBJECT_A = "oidc-subject-a"
SUBJECT_B = "oidc-subject-b"
PROFILE = {
    "name": "Test Student",
    "age": 24,
    "education": "B.Tech",
    "field": "Computer Science",
    "experience": "Academic projects",
    "skills": ["Python", "SQL"],
    "interests": ["Data Science"],
    "confirmed_skills": ["Python", "SQL"],
    "confirmed_interests": ["Data Science"],
}
APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


class UserDataStoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path = Path(self.temporary_directory.name) / "user-data.sqlite3"
        self.database_path_patch = patch.object(
            user_data_store,
            "DATABASE_PATH",
            self.database_path,
        )
        self.database_path_patch.start()
        self.addCleanup(self.database_path_patch.stop)

    def test_empty_database_returns_empty_user_data_defaults(self):
        self.assertEqual(
            load_user_data(ISSUER, SUBJECT_A),
            {"profile": None, "saved_careers": [], "roadmap_progress": {}},
        )

    def test_profile_persists_across_database_reopen_including_age(self):
        save_profile(ISSUER, SUBJECT_A, PROFILE)

        restored = load_user_data(ISSUER, SUBJECT_A)

        self.assertEqual(restored["profile"], PROFILE)
        self.assertEqual(restored["profile"]["age"], 24)

    def test_saved_career_persists_and_save_unsave_are_idempotent(self):
        set_saved_career(ISSUER, SUBJECT_A, "data-scientist", True)
        set_saved_career(ISSUER, SUBJECT_A, "data-scientist", True)
        self.assertEqual(
            load_user_data(ISSUER, SUBJECT_A)["saved_careers"],
            ["data-scientist"],
        )

        set_saved_career(ISSUER, SUBJECT_A, "data-scientist", False)
        set_saved_career(ISSUER, SUBJECT_A, "data-scientist", False)
        self.assertEqual(
            load_user_data(ISSUER, SUBJECT_A)["saved_careers"],
            [],
        )

    def test_roadmap_progress_persists_and_unchecking_removes_phase(self):
        set_roadmap_phase(
            ISSUER,
            SUBJECT_A,
            "data-scientist",
            "phase-2",
            True,
        )
        self.assertEqual(
            load_user_data(ISSUER, SUBJECT_A)["roadmap_progress"],
            {"data-scientist": ["phase-2"]},
        )

        set_roadmap_phase(
            ISSUER,
            SUBJECT_A,
            "data-scientist",
            "phase-2",
            False,
        )
        self.assertEqual(
            load_user_data(ISSUER, SUBJECT_A)["roadmap_progress"],
            {},
        )

    def test_users_are_isolated_by_issuer_and_subject(self):
        save_profile(ISSUER, SUBJECT_A, PROFILE)
        set_saved_career(ISSUER, SUBJECT_A, "data-scientist", True)
        set_saved_career(ISSUER, SUBJECT_B, "data-analyst", True)

        self.assertEqual(load_user_data(ISSUER, SUBJECT_A)["profile"], PROFILE)
        self.assertEqual(
            load_user_data(ISSUER, SUBJECT_A)["saved_careers"],
            ["data-scientist"],
        )
        self.assertIsNone(load_user_data(ISSUER, SUBJECT_B)["profile"])
        self.assertEqual(
            load_user_data(ISSUER, SUBJECT_B)["saved_careers"],
            ["data-analyst"],
        )

    def test_invalid_identity_is_rejected(self):
        for issuer, subject in (
            ("", SUBJECT_A),
            ("http://accounts.google.com", SUBJECT_A),
            (ISSUER, ""),
            (ISSUER, 123),
        ):
            with self.subTest(issuer=issuer, subject=subject):
                with self.assertRaises(ValueError):
                    load_user_data(issuer, subject)

    def test_invalid_profile_fields_and_age_are_rejected(self):
        for invalid_profile in (
            {**PROFILE, "age": 14},
            {**PROFILE, "age": True},
            {**PROFILE, "education": "Unlisted"},
            {**PROFILE, "skills": ["Unknown skill"]},
            {**PROFILE, "confirmed_interests": ["Web Development"]},
        ):
            with self.subTest(profile_field=invalid_profile):
                with self.assertRaises(ValueError):
                    save_profile(ISSUER, SUBJECT_A, invalid_profile)

    def test_invalid_career_and_phase_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            set_saved_career(ISSUER, SUBJECT_A, "unknown-career", True)
        with self.assertRaises(ValueError):
            set_roadmap_phase(
                ISSUER,
                SUBJECT_A,
                "data-scientist",
                "phase-99",
                True,
            )

    def test_profile_validation_matches_current_assessment_catalog(self):
        profile = {
            **PROFILE,
            "skills": [assessment_skill_options()[0]],
            "confirmed_skills": [assessment_skill_options()[0]],
            "interests": [assessment_interest_options()[0]],
            "confirmed_interests": [assessment_interest_options()[0]],
        }
        save_profile(ISSUER, SUBJECT_A, profile)

        self.assertEqual(load_user_data(ISSUER, SUBJECT_A)["profile"], profile)
        self.assertEqual(len(CAREERS), 10)

    def test_delete_removes_only_the_selected_user_and_cascades_records(self):
        save_profile(ISSUER, SUBJECT_A, PROFILE)
        set_saved_career(ISSUER, SUBJECT_A, "data-scientist", True)
        set_roadmap_phase(ISSUER, SUBJECT_A, "data-scientist", "phase-1", True)
        save_profile(ISSUER, SUBJECT_B, PROFILE)

        delete_user_data(ISSUER, SUBJECT_A)

        self.assertEqual(
            load_user_data(ISSUER, SUBJECT_A),
            {"profile": None, "saved_careers": [], "roadmap_progress": {}},
        )
        self.assertEqual(load_user_data(ISSUER, SUBJECT_B)["profile"], PROFILE)

    def test_each_connection_enables_foreign_key_enforcement(self):
        connection = user_data_store._connect()
        try:
            self.assertEqual(
                connection.execute("PRAGMA foreign_keys").fetchone()[0],
                1,
            )
        finally:
            connection.close()

    def test_database_initialization_preserves_unrelated_existing_tables(self):
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        try:
            connection.execute("CREATE TABLE unrelated_data (value TEXT)")
            connection.execute("INSERT INTO unrelated_data VALUES (?)", ("preserved",))
            connection.commit()
        finally:
            connection.close()

        load_user_data(ISSUER, SUBJECT_A)

        connection = sqlite3.connect(self.database_path)
        try:
            self.assertEqual(
                connection.execute("SELECT value FROM unrelated_data").fetchone()[0],
                "preserved",
            )
        finally:
            connection.close()

    def test_database_errors_are_raised_to_the_caller(self):
        blocked_path = Path(self.temporary_directory.name) / "not-a-directory"
        blocked_path.write_text("block directory creation", encoding="utf-8")
        with patch.object(
            user_data_store,
            "DATABASE_PATH",
            blocked_path / "career-data.sqlite3",
        ):
            with self.assertRaises(OSError):
                load_user_data(ISSUER, SUBJECT_A)

    def test_app_surfaces_database_error_without_exposing_exception_details(self):
        with (
            patch("auth_utils.is_authenticated_user", return_value=True),
            patch("auth_utils.authenticated_user_name", return_value="OIDC Name"),
            patch(
                "auth_utils.authenticated_user_identity",
                return_value=(ISSUER, SUBJECT_A),
            ),
            patch(
                "user_data_store.load_user_data",
                side_effect=sqlite3.OperationalError("private database path"),
            ),
        ):
            app = AppTest.from_file(str(APP_PATH)).run(timeout=20)

        self.assertEqual(len(app.exception), 0)
        rendered_errors = "\n".join(error.value for error in app.error)
        self.assertIn("Your saved career data could not be loaded", rendered_errors)
        self.assertNotIn("private database path", rendered_errors)

    def test_authenticated_app_restores_after_logout_and_new_session(self):
        save_profile(ISSUER, SUBJECT_A, PROFILE)
        set_saved_career(ISSUER, SUBJECT_A, "data-scientist", True)
        set_roadmap_phase(ISSUER, SUBJECT_A, "data-scientist", "phase-1", True)
        auth_patches = (
            patch("auth_utils.is_authenticated_user", return_value=True),
            patch("auth_utils.authenticated_user_name", return_value="OIDC Name"),
            patch(
                "auth_utils.authenticated_user_identity",
                return_value=(ISSUER, SUBJECT_A),
            ),
        )
        with auth_patches[0], auth_patches[1], auth_patches[2]:
            first_session = AppTest.from_file(str(APP_PATH)).run(timeout=20)
            self.assertEqual(len(first_session.exception), 0)
            self.assertEqual(first_session.session_state["profile"], PROFILE)
            self.assertEqual(
                first_session.session_state["saved_careers"],
                ["data-scientist"],
            )
            self.assertEqual(
                first_session.session_state["roadmap_progress"],
                {"data-scientist": ["phase-1"]},
            )

            with patch("streamlit.logout") as logout:
                next(button for button in first_session.button if "Logout" in button.label).click().run(
                    timeout=20
                )
            logout.assert_called_once_with()
            self.assertEqual(load_user_data(ISSUER, SUBJECT_A)["profile"], PROFILE)

            second_session = AppTest.from_file(str(APP_PATH)).run(timeout=20)
            self.assertEqual(len(second_session.exception), 0)
            self.assertEqual(second_session.session_state["profile"], PROFILE)
            self.assertEqual(
                second_session.session_state["saved_careers"],
                ["data-scientist"],
            )
            self.assertEqual(
                second_session.session_state["roadmap_progress"],
                {"data-scientist": ["phase-1"]},
            )

    def test_authenticated_identity_change_replaces_user_scoped_session_data(self):
        profile_a = {**PROFILE, "name": "Student A"}
        profile_b = {**PROFILE, "name": "Student B"}
        save_profile(ISSUER, SUBJECT_A, profile_a)
        save_profile(ISSUER, SUBJECT_B, profile_b)
        set_saved_career(ISSUER, SUBJECT_A, "data-scientist", True)
        set_saved_career(ISSUER, SUBJECT_B, "data-analyst", True)
        set_roadmap_phase(ISSUER, SUBJECT_A, "data-scientist", "phase-1", True)
        set_roadmap_phase(ISSUER, SUBJECT_B, "data-analyst", "phase-2", True)
        with (
            patch("auth_utils.is_authenticated_user", return_value=True),
            patch("auth_utils.authenticated_user_name", return_value="OIDC Name"),
            patch(
                "auth_utils.authenticated_user_identity",
                return_value=(ISSUER, SUBJECT_A),
            ) as identity,
        ):
            app = AppTest.from_file(str(APP_PATH)).run(timeout=20)
            self.assertEqual(app.session_state["profile"], profile_a)
            app.session_state["comparison_career_ids"] = ["data-scientist"]

            identity.return_value = (ISSUER, SUBJECT_B)
            app.run(timeout=20)

        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.session_state["profile"], profile_b)
        self.assertEqual(app.session_state["saved_careers"], ["data-analyst"])
        self.assertEqual(
            app.session_state["roadmap_progress"],
            {"data-analyst": ["phase-2"]},
        )
        self.assertEqual(app.session_state["comparison_career_ids"], [])

    def test_assessment_submission_persists_profile_and_age(self):
        with (
            patch("auth_utils.is_authenticated_user", return_value=True),
            patch("auth_utils.authenticated_user_name", return_value="OIDC Name"),
            patch(
                "auth_utils.authenticated_user_identity",
                return_value=(ISSUER, SUBJECT_A),
            ),
        ):
            app = AppTest.from_file(str(APP_PATH)).run(timeout=20)
            app.button(key="nav_Career Assessment").click().run(timeout=20)
            next(field for field in app.text_input if field.label == "Name *").set_value(
                "Assessment Student"
            )
            next(field for field in app.number_input if field.label == "Age *").set_value(29)
            next(
                checkbox
                for checkbox in app.checkbox
                if checkbox.label
                == "I reviewed and confirm the selected skills and career interests."
            ).set_value(True)
            next(
                button
                for button in app.button
                if button.label == "Generate Career Recommendations"
            ).click().run(timeout=20)

        self.assertEqual(len(app.exception), 0)
        saved_profile = load_user_data(ISSUER, SUBJECT_A)["profile"]
        self.assertEqual(saved_profile["name"], "Assessment Student")
        self.assertEqual(saved_profile["age"], 29)
        self.assertEqual(saved_profile["confirmed_skills"], saved_profile["skills"])
        self.assertEqual(
            saved_profile["confirmed_interests"],
            saved_profile["interests"],
        )

    def test_profile_page_requires_confirmation_and_deletes_current_user_only(self):
        save_profile(ISSUER, SUBJECT_A, PROFILE)
        save_profile(ISSUER, SUBJECT_B, PROFILE)
        with (
            patch("auth_utils.is_authenticated_user", return_value=True),
            patch("auth_utils.authenticated_user_name", return_value="OIDC Name"),
            patch(
                "auth_utils.authenticated_user_identity",
                return_value=(ISSUER, SUBJECT_A),
            ),
        ):
            app = AppTest.from_file(str(APP_PATH)).run(timeout=20)
            app.button(key="nav_My Profile").click().run(timeout=20)
            self.assertEqual(len(app.exception), 0)
            next(
                button for button in app.button
                if button.label == "Delete my saved data"
            ).click().run(timeout=20)
            self.assertTrue(any("Confirm the deletion" in item.value for item in app.warning))
            self.assertEqual(load_user_data(ISSUER, SUBJECT_A)["profile"], PROFILE)

            next(
                checkbox for checkbox in app.checkbox
                if checkbox.label == "I understand and want to delete my saved data."
            ).set_value(True)
            next(
                button for button in app.button
                if button.label == "Delete my saved data"
            ).click().run(timeout=20)

        self.assertEqual(len(app.exception), 0)
        self.assertIsNone(load_user_data(ISSUER, SUBJECT_A)["profile"])
        self.assertEqual(load_user_data(ISSUER, SUBJECT_B)["profile"], PROFILE)


if __name__ == "__main__":
    unittest.main()
