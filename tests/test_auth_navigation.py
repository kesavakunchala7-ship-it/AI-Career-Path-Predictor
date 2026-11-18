import unittest
from pathlib import Path
import tempfile
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from auth_utils import (
    authenticated_user_name,
    authenticated_user_identity,
    hash_password,
    is_authenticated_user,
    verify_password,
)


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


class AuthenticationNavigationTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path_patch = patch(
            "user_data_store.DATABASE_PATH",
            Path(self.temporary_directory.name) / "user-data.sqlite3",
        )
        self.database_path_patch.start()
        self.addCleanup(self.database_path_patch.stop)

    def create_app(self, page="Home"):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=15)
        app.session_state["page"] = page
        app.run(timeout=15)
        self.assertEqual(len(app.exception), 0)
        return app

    @staticmethod
    def button_by_key(app, key):
        return next(button for button in app.button if button.key == key)

    def test_password_hashing_remains_salted_and_non_reversible(self):
        password = "SamplePrototypePassword!23"
        first_hash = hash_password(password)
        second_hash = hash_password(password)

        self.assertNotEqual(first_hash, password)
        self.assertNotEqual(first_hash, second_hash)
        self.assertTrue(first_hash.startswith("pbkdf2_sha256$"))
        self.assertTrue(verify_password(password, first_hash))
        self.assertFalse(verify_password("incorrect-password", first_hash))
        self.assertFalse(verify_password(password, "pbkdf2_sha256$1$00$00"))

    def test_authentication_requires_streamlit_oidc_boolean_claim(self):
        self.assertTrue(is_authenticated_user({"is_logged_in": True}))
        self.assertFalse(is_authenticated_user({"is_logged_in": False}))
        self.assertFalse(is_authenticated_user({"is_logged_in": "true"}))
        self.assertFalse(is_authenticated_user({"signed_in": True}))
        self.assertFalse(is_authenticated_user({}))

    def test_profile_name_uses_safe_oidc_name_or_fallback(self):
        self.assertEqual(authenticated_user_name({"name": "  Ada Student  "}), "Ada Student")
        self.assertEqual(authenticated_user_name({"name": ""}), "Student")
        self.assertEqual(authenticated_user_name({"email": "ada@example.invalid"}), "Student")
        self.assertEqual(authenticated_user_name({"name": 123}), "Student")

    def test_authenticated_identity_uses_only_verified_issuer_and_subject(self):
        self.assertEqual(
            authenticated_user_identity(
                {
                    "is_logged_in": True,
                    "iss": "https://accounts.google.com",
                    "sub": "stable-subject",
                    "email": "not-an-ownership-key@example.invalid",
                }
            ),
            ("https://accounts.google.com", "stable-subject"),
        )
        self.assertIsNone(
            authenticated_user_identity(
                {"is_logged_in": True, "email": "student@example.invalid"}
            )
        )
        self.assertIsNone(
            authenticated_user_identity(
                {
                    "is_logged_in": True,
                    "iss": "http://accounts.google.com",
                    "sub": "stable-subject",
                }
            )
        )
        self.assertIsNone(
            authenticated_user_identity(
                {
                    "is_logged_in": True,
                    "iss": "https://[invalid",
                    "sub": "stable-subject",
                }
            )
        )

    def test_home_offers_google_login_without_local_password_collection(self):
        app = self.create_app()

        self.assertTrue(any(button.label == "Continue with Google" for button in app.button))
        self.assertEqual(len(app.text_input), 0)
        self.assertFalse(any(button.label == "Login" for button in app.button))

    def test_login_button_invokes_streamlit_oidc(self):
        app = self.create_app()

        with patch("streamlit.login") as login:
            next(button for button in app.button if button.label == "Continue with Google").click().run(
                timeout=15
            )

        login.assert_called_once_with()
        self.assertEqual(len(app.exception), 0)

    def test_signup_page_uses_oidc_instead_of_local_account_storage(self):
        app = self.create_app("Sign Up")
        self.assertTrue(any(button.label == "Continue with Google" for button in app.button))

        with patch("streamlit.login") as login:
            next(button for button in app.button if button.label == "Continue with Google").click().run(
                timeout=15
            )

        login.assert_called_once_with()
        self.assertNotIn("accounts", app.session_state)

    def test_session_signed_in_flag_cannot_bypass_oidc_guard(self):
        app = self.create_app()
        app.session_state["signed_in"] = True
        app.session_state["page"] = "Results"
        app.run(timeout=15)

        self.assertFalse(app.session_state["signed_in"])
        self.assertEqual(app.session_state["page"], "Home")
        self.assertEqual(len(app.exception), 0)

    def test_authenticated_navigation_preserves_profile_and_assessment_state(self):
        profile = {
            "name": "",
            "confirmed_skills": ["Python"],
            "confirmed_interests": ["Data Science"],
        }
        app = self.create_app()
        app.session_state["page"] = "Dashboard"
        app.session_state["profile"] = profile.copy()
        app.session_state["saved_careers"] = ["data-scientist"]
        app.session_state["_loaded_user_identity"] = (
            "https://accounts.google.com",
            "test-subject",
        )

        with (
            patch("auth_utils.is_authenticated_user", return_value=True),
            patch("auth_utils.authenticated_user_name", return_value="OIDC Student"),
            patch(
                "auth_utils.authenticated_user_identity",
                return_value=("https://accounts.google.com", "test-subject"),
            ),
        ):
            app.run(timeout=15)
            self.assertTrue(app.session_state["signed_in"])
            self.assertEqual(app.session_state["profile"]["name"], "OIDC Student")
            for page in ("Career Assessment", "Results", "Dashboard"):
                self.button_by_key(app, f"nav_{page}").click().run(timeout=15)
                self.assertEqual(len(app.exception), 0)
                self.assertTrue(app.session_state["signed_in"])
                self.assertEqual(app.session_state["page"], page)
                self.assertEqual(
                    app.session_state["profile"]["confirmed_skills"],
                    ["Python"],
                )
                self.assertEqual(
                    app.session_state["profile"]["confirmed_interests"],
                    ["Data Science"],
                )
                self.assertEqual(app.session_state["saved_careers"], ["data-scientist"])

    def test_authenticated_oidc_callback_from_new_session_opens_dashboard(self):
        app = self.create_app()

        with (
            patch("auth_utils.is_authenticated_user", return_value=True),
            patch("auth_utils.authenticated_user_name", return_value="Google Student"),
            patch(
                "auth_utils.authenticated_user_identity",
                return_value=("https://accounts.google.com", "test-subject"),
            ),
        ):
            app.run(timeout=15)

        self.assertTrue(app.session_state["signed_in"])
        self.assertEqual(app.session_state["page"], "Dashboard")
        self.assertTrue(
            any("Welcome, Google Student" in title.value for title in app.title)
        )
        self.assertFalse(
            any(button.label == "Continue with Google" for button in app.button)
        )

    def test_logout_invokes_streamlit_oidc_logout(self):
        app = self.create_app()
        with (
            patch("auth_utils.is_authenticated_user", return_value=True),
            patch("auth_utils.authenticated_user_name", return_value="OIDC Student"),
            patch(
                "auth_utils.authenticated_user_identity",
                return_value=("https://accounts.google.com", "test-subject"),
            ),
            patch("streamlit.logout") as logout,
        ):
            app.session_state["page"] = "Dashboard"
            app.run(timeout=15)
            next(button for button in app.button if "Logout" in button.label).click().run(
                timeout=15
            )

        logout.assert_called_once_with()
        self.assertEqual(len(app.exception), 0)

    def test_unauthenticated_protected_page_redirects_home(self):
        app = self.create_app()
        app.session_state["page"] = "My Profile"
        app.run(timeout=15)

        self.assertEqual(app.session_state["page"], "Home")
        self.assertFalse(app.session_state["signed_in"])
        self.assertEqual(len(app.exception), 0)


if __name__ == "__main__":
    unittest.main()
