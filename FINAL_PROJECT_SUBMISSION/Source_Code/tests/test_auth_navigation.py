import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

from auth_utils import (
    authenticate_account,
    hash_password,
    register_account,
    verify_password,
)


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


class AuthenticationNavigationTests(unittest.TestCase):
    @staticmethod
    def submit_login(app, email, password):
        app.text_input[0].set_value(email)
        app.text_input[1].set_value(password)
        next(button for button in app.button if button.label == "Login").click().run(timeout=20)
        return app

    @staticmethod
    def submit_registration(app, name, email, password, confirmation=None):
        next(button for button in app.button if button.label == "Sign Up").click().run(timeout=20)
        app.text_input[0].set_value(name)
        app.text_input[1].set_value(email)
        app.text_input[2].set_value(password)
        app.text_input[3].set_value(password if confirmation is None else confirmation)
        next(button for button in app.button if button.label == "Create Account").click().run(timeout=20)
        return app

    def create_app(self, page, signed_in, profile=None, saved_careers=None):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=15)
        app.session_state["page"] = page
        app.session_state["signed_in"] = signed_in
        if profile is not None:
            app.session_state["profile"] = profile
        if saved_careers is not None:
            app.session_state["saved_careers"] = saved_careers
        app.run(timeout=15)
        self.assertEqual(len(app.exception), 0)
        return app

    @staticmethod
    def button_by_key(app, key):
        return next(button for button in app.button if button.key == key)

    @staticmethod
    def displayed_content(app):
        element_names = (
            "title", "header", "subheader", "markdown", "caption", "text",
            "success", "info", "warning", "error",
        )
        return "\n".join(
            str(element.value)
            for name in element_names
            for element in getattr(app, name, [])
        )

    def test_password_is_stored_as_salted_pbkdf2_hash(self):
        password = "SamplePrototypePassword!23"
        stored_hash = hash_password(password)

        self.assertNotEqual(stored_hash, password)
        self.assertTrue(stored_hash.startswith("pbkdf2_sha256$"))
        self.assertTrue(verify_password(password, stored_hash))
        self.assertFalse(verify_password("incorrect-password", stored_hash))
        self.assertFalse(verify_password(password, "pbkdf2_sha256$1$00$00"))

    def test_registration_accepts_valid_account_and_stores_hash(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=20)
        self.submit_registration(
            app,
            "Registered Test Student",
            "Student@example.invalid",
            "SamplePrototypePassword!23",
        )

        self.assertEqual(len(app.exception), 0)
        self.assertTrue(app.session_state["signed_in"])
        self.assertEqual(app.session_state["page"], "Career Assessment")
        account = app.session_state["accounts"]["student@example.invalid"]
        self.assertEqual(account["name"], "Registered Test Student")
        self.assertNotEqual(account["password_hash"], "SamplePrototypePassword!23")
        self.assertTrue(
            authenticate_account(
                app.session_state["accounts"],
                "STUDENT@example.invalid",
                "SamplePrototypePassword!23",
            )
        )

    def test_registration_rejects_missing_name_email_or_password(self):
        invalid_registrations = (
            ("", "name@example.invalid", "Password!23", "Enter your full name."),
            ("Student", "", "Password!23", "Enter your email address."),
            ("Student", "password@example.invalid", "", "Enter a password."),
        )
        for name, email, password, expected_error in invalid_registrations:
            with self.subTest(error=expected_error):
                accounts = {}
                self.assertEqual(
                    register_account(accounts, name, email, password),
                    expected_error,
                )
                self.assertEqual(accounts, {})

    def test_registered_user_can_log_in_and_sees_registered_profile(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=20)
        self.submit_registration(
            app,
            "Login Test Student",
            "login-test@example.invalid",
            "SamplePrototypePassword!23",
        )
        next(button for button in app.button if "Logout" in button.label).click().run(timeout=20)

        self.submit_login(app, "LOGIN-TEST@example.invalid", "SamplePrototypePassword!23")

        self.assertEqual(len(app.exception), 0)
        self.assertTrue(app.session_state["signed_in"])
        self.assertEqual(app.session_state["page"], "Dashboard")
        self.assertEqual(app.session_state["profile"]["name"], "Login Test Student")
        self.assertTrue(any("Welcome, Login Test Student" in item.value for item in app.title))

    def test_login_rejects_registered_email_with_wrong_password(self):
        accounts = {}
        self.assertIsNone(
            register_account(
                accounts,
                "Registered Student",
                "registered@example.invalid",
                "CorrectPrototypePassword!23",
            )
        )
        app = AppTest.from_file(str(APP_PATH)).run(timeout=20)
        app.session_state["accounts"] = accounts
        app.run(timeout=20)

        self.submit_login(app, "registered@example.invalid", "wrong-password")

        self.assertFalse(app.session_state["signed_in"])
        self.assertEqual(
            app.error[-1].value,
            "Email or password is incorrect. Register first if you do not have an account.",
        )

    def test_login_rejects_unregistered_email_without_creating_account(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=20)
        before_accounts = dict(app.session_state["accounts"])

        self.submit_login(app, "unknown@example.invalid", "AnyPrototypePassword!23")

        self.assertFalse(app.session_state["signed_in"])
        self.assertEqual(app.session_state["page"], "Home")
        self.assertEqual(app.session_state["accounts"], before_accounts)
        self.assertTrue(app.error)

    def test_login_rejects_empty_email(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=20)

        self.submit_login(app, "", "SomePrototypePassword!23")

        self.assertFalse(app.session_state["signed_in"])
        self.assertEqual(app.error[-1].value, "Enter your email address.")

    def test_login_rejects_empty_password(self):
        accounts = {}
        self.assertIsNone(
            register_account(
                accounts,
                "Registered Student",
                "registered@example.invalid",
                "CorrectPrototypePassword!23",
            )
        )
        app = AppTest.from_file(str(APP_PATH)).run(timeout=20)
        app.session_state["accounts"] = accounts
        app.run(timeout=20)

        self.submit_login(app, "registered@example.invalid", "")

        self.assertFalse(app.session_state["signed_in"])
        self.assertEqual(app.error[-1].value, "Enter your password.")

    def test_login_rejects_invalid_email(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=20)

        self.submit_login(app, "not-an-email", "SomePrototypePassword!23")

        self.assertFalse(app.session_state["signed_in"])
        self.assertEqual(app.error[-1].value, "Enter a valid email address.")

    def test_registration_rejects_invalid_email_without_account_creation(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=20)
        self.submit_registration(
            app,
            "Invalid Email Student",
            "not-an-email",
            "SomePrototypePassword!23",
        )

        self.assertFalse(app.session_state["signed_in"])
        self.assertEqual(app.session_state["accounts"], {})
        self.assertEqual(app.error[-1].value, "Enter a valid email address.")

    def test_registration_rejects_empty_password_without_account_creation(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=20)
        self.submit_registration(app, "Empty Password Student", "empty@example.invalid", "")

        self.assertFalse(app.session_state["signed_in"])
        self.assertEqual(app.session_state["accounts"], {})
        self.assertEqual(app.error[-1].value, "Enter a password.")

    def test_registration_rejects_mismatched_password_confirmation(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=20)
        self.submit_registration(
            app,
            "Mismatch Student",
            "mismatch@example.invalid",
            "SomePrototypePassword!23",
            confirmation="DifferentPrototypePassword!23",
        )

        self.assertFalse(app.session_state["signed_in"])
        self.assertEqual(app.session_state["accounts"], {})
        self.assertEqual(app.error[-1].value, "Passwords do not match.")

    def test_registration_rejects_duplicate_email_case_insensitively(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=20)
        self.submit_registration(
            app,
            "First Student",
            "duplicate@example.invalid",
            "FirstPrototypePassword!23",
        )
        app.session_state["signed_in"] = False
        app.session_state["page"] = "Sign Up"
        app.run(timeout=20)
        before_accounts = dict(app.session_state["accounts"])
        app.text_input[0].set_value("Second Student")
        app.text_input[1].set_value("DUPLICATE@example.invalid")
        app.text_input[2].set_value("SecondPrototypePassword!23")
        app.text_input[3].set_value("SecondPrototypePassword!23")
        next(button for button in app.button if button.label == "Create Account").click().run(timeout=20)

        self.assertFalse(app.session_state["signed_in"])
        self.assertEqual(app.session_state["accounts"], before_accounts)
        self.assertEqual(
            app.error[-1].value,
            "An account with this email is already registered. Please log in.",
        )

    def test_failed_login_does_not_authenticate_or_register_user(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=20)

        self.submit_login(app, "absent@example.invalid", "UnregisteredPrototypePassword!23")

        self.assertFalse(app.session_state["signed_in"])
        self.assertEqual(app.session_state["accounts"], {})

    def test_about_shows_current_authenticated_profile(self):
        app = self.create_app(
            "About",
            True,
            profile={"name": "Current Test User"},
        )

        self.assertIn("Current demo profile: Current Test User", self.displayed_content(app))

    def test_logout_clears_profile_and_preserves_saved_careers(self):
        app = self.create_app(
            "About",
            True,
            profile={
                "name": "Previous Test User",
                "age": 22,
                "experience": "Academic projects",
                "skills": ["Python"],
                "interests": ["Data Science"],
                "confirmed_skills": ["Python"],
                "confirmed_interests": ["Data Science"],
            },
            saved_careers=["data-scientist"],
        )
        logout = next(button for button in app.button if "Logout" in button.label)
        logout.click().run(timeout=15)

        self.assertEqual(len(app.exception), 0)
        self.assertFalse(app.session_state["signed_in"])
        self.assertEqual(app.session_state["page"], "Home")
        self.assertEqual(app.session_state["profile"]["name"], "")
        self.assertEqual(app.session_state["profile"]["confirmed_skills"], [])
        self.assertNotIn("age", app.session_state["profile"])
        self.assertNotIn("experience", app.session_state["profile"])
        self.assertEqual(app.session_state["saved_careers"], ["data-scientist"])

        self.button_by_key(app, "public_about").click().run(timeout=15)
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.session_state["page"], "About")
        self.assertNotIn("Previous Test User", self.displayed_content(app))

    def test_about_home_button_returns_to_public_home_after_logout(self):
        app = self.create_app("About", False)

        self.button_by_key(app, "public_home").click().run(timeout=15)

        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.session_state["page"], "Home")
        self.assertTrue(any("Explore Career Paths" in item.value for item in app.markdown))

    def test_about_home_button_returns_authenticated_user_to_dashboard(self):
        app = self.create_app(
            "About",
            True,
            profile={"name": "Current Test User"},
        )

        self.button_by_key(app, "public_home").click().run(timeout=15)

        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.session_state["page"], "Dashboard")
        self.assertTrue(any("Welcome, Current Test User" in item.value for item in app.title))

    def test_unauthenticated_protected_route_redirects_home(self):
        app = self.create_app("My Profile", False)

        self.assertEqual(app.session_state["page"], "Home")
        self.assertEqual(len(app.exception), 0)


if __name__ == "__main__":
    unittest.main()
