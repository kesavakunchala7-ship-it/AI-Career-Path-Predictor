import unittest
from pathlib import Path
import tempfile
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from career_data import CAREERS
from recommendation_engine import rank_careers
from roadmap_progress import (
    calculate_roadmap_progress,
    roadmap_phase_entries,
    set_phase_completion,
)


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"
PHASES = CAREERS[0]["roadmap"]


class RoadmapProgressTests(unittest.TestCase):
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
            return_value=("https://accounts.google.com", "roadmap-test-subject"),
        )
        self.authenticated_user_patch.start()
        self.authenticated_name_patch.start()
        self.authenticated_identity_patch.start()
        self.addCleanup(self.authenticated_user_patch.stop)
        self.addCleanup(self.authenticated_name_patch.stop)
        self.addCleanup(self.authenticated_identity_patch.stop)

    def test_initial_progress_has_all_phases_incomplete(self):
        progress = calculate_roadmap_progress(PHASES, [])

        self.assertEqual(progress.total, 4)
        self.assertEqual(progress.completed, 0)
        self.assertEqual(progress.remaining, 4)
        self.assertEqual(progress.percentage, 0)

    def test_marking_one_phase_complete_updates_counts_and_percentage(self):
        progress_by_career = {}
        set_phase_completion(progress_by_career, "data-scientist", "phase-1", True)
        progress = calculate_roadmap_progress(
            PHASES,
            progress_by_career["data-scientist"],
        )

        self.assertEqual(progress.completed, 1)
        self.assertEqual(progress.remaining, 3)
        self.assertEqual(progress.percentage, 25)

    def test_unmarking_a_completed_phase_restores_incomplete_counts(self):
        progress_by_career = {"data-scientist": ["phase-1"]}
        set_phase_completion(progress_by_career, "data-scientist", "phase-1", False)
        progress = calculate_roadmap_progress(
            PHASES,
            progress_by_career["data-scientist"],
        )

        self.assertEqual(progress_by_career["data-scientist"], [])
        self.assertEqual(progress.completed, 0)
        self.assertEqual(progress.remaining, 4)
        self.assertEqual(progress.percentage, 0)

    def test_progress_is_independent_for_each_career(self):
        progress_by_career = {}
        set_phase_completion(progress_by_career, "data-scientist", "phase-1", True)

        self.assertEqual(
            calculate_roadmap_progress(
                PHASES,
                progress_by_career["data-scientist"],
            ).completed,
            1,
        )
        self.assertEqual(
            calculate_roadmap_progress(
                PHASES,
                progress_by_career.get("data-analyst", []),
            ).completed,
            0,
        )

    def test_empty_or_missing_roadmap_data_is_safe(self):
        for roadmap in (None, [], "", {}):
            with self.subTest(roadmap=roadmap):
                self.assertEqual(roadmap_phase_entries(roadmap), ())
                self.assertEqual(
                    calculate_roadmap_progress(roadmap, ["phase-1"]),
                    calculate_roadmap_progress([], []),
                )

    def test_unknown_completed_phases_are_not_counted(self):
        progress = calculate_roadmap_progress(PHASES, ["phase-1", "phase-99"])

        self.assertEqual(progress.completed, 1)
        self.assertEqual(progress.remaining, 3)

    def test_switching_careers_in_app_preserves_session_progress(self):
        app = AppTest.from_file(str(APP_PATH)).run(timeout=20)
        app.session_state["page"] = "Learning Roadmap"
        app.session_state["signed_in"] = True
        app.session_state["selected_career_id"] = "data-scientist"
        app.session_state["selected_career"] = "Data Scientist"
        app.session_state["profile"] = {"confirmed_skills": []}
        app.run(timeout=20)
        self.assertEqual(len(app.exception), 0)

        app.checkbox(key="roadmap_complete_data-scientist_phase-1").set_value(True).run(timeout=20)
        self.assertEqual(
            app.session_state["roadmap_progress"]["data-scientist"],
            ["phase-1"],
        )

        app.session_state["selected_career_id"] = "data-analyst"
        app.session_state["selected_career"] = "Data Analyst"
        app.run(timeout=20)
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(
            app.session_state["roadmap_progress"]["data-scientist"],
            ["phase-1"],
        )

        app.session_state["selected_career_id"] = "data-scientist"
        app.session_state["selected_career"] = "Data Scientist"
        app.run(timeout=20)
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(app.checkbox(key="roadmap_complete_data-scientist_phase-1").value)
        self.assertEqual(app.metric[1].value, "1")
        self.assertEqual(app.metric[2].value, "3")
        self.assertEqual(app.metric[3].value, "25%")

    def test_progress_updates_do_not_change_recommendation_scores_or_order(self):
        before = rank_careers(
            CAREERS,
            ["Python", "SQL"],
            ["Data Science"],
        )
        progress_by_career = {}
        set_phase_completion(progress_by_career, "data-scientist", "phase-1", True)
        after = rank_careers(
            CAREERS,
            ["Python", "SQL"],
            ["Data Science"],
        )

        self.assertEqual(
            [(item.career_id, item.score) for item in before],
            [(item.career_id, item.score) for item in after],
        )


if __name__ == "__main__":
    unittest.main()
