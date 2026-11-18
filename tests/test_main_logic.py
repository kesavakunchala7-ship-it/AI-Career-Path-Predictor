import unittest

from career_data import CAREERS
from main_logic import (
    calculate_weighted_career_score,
    match_interests,
    match_skills,
    process_student_inputs,
    rank_careers,
    recommend_careers,
)


class MainLogicTests(unittest.TestCase):
    def test_student_inputs_are_trimmed_and_deduplicated(self):
        self.assertEqual(
            process_student_inputs(
                [" Python ", "python", "Machine\tLearning", None],
                ["DATA Science", " data   science ", 5],
            ),
            (("Python", "Machine Learning"), ("DATA Science",)),
        )

    def test_string_inputs_are_treated_as_one_selection(self):
        self.assertEqual(
            process_student_inputs(" Python ", "Data Science"),
            (("Python",), ("Data Science",)),
        )

    def test_non_iterable_student_input_is_rejected(self):
        with self.assertRaisesRegex(TypeError, "confirmed_skills"):
            process_student_inputs(42, ["Data Science"])

    def test_skill_and_interest_matching_uses_normalized_labels(self):
        self.assertEqual(
            match_skills([" python "], ["Python", "SQL"]),
            (("Python",), ("SQL",)),
        )
        self.assertEqual(
            match_interests([" DATA Science "], ["Data Science", "Research"]),
            (("Data Science",), ("Research",)),
        )

    def test_weighted_score_matches_existing_percentage_representation(self):
        self.assertAlmostEqual(calculate_weighted_career_score(0.5, 1.0), 65.0)
        self.assertEqual(calculate_weighted_career_score(1.0, 0.0), 70.0)
        self.assertIsNone(calculate_weighted_career_score(None, 1.0))

    def test_weighted_score_rejects_invalid_match_ratios(self):
        for invalid_score in (-0.1, 1.1, float("inf"), float("nan")):
            with self.subTest(invalid_score=invalid_score):
                with self.assertRaises(ValueError):
                    calculate_weighted_career_score(invalid_score, 0.5)

    def test_recommend_careers_uses_the_curated_catalog_and_existing_ranking(self):
        skills = ["Java", "SQL"]
        interests = ["Backend Development"]

        self.assertEqual(
            recommend_careers(skills, interests),
            rank_careers(CAREERS, skills, interests),
        )
        self.assertEqual(
            recommend_careers(skills, interests)[0].career_id,
            "java-backend-developer",
        )


if __name__ == "__main__":
    unittest.main()
