import unittest

from career_data import (
    CAREERS,
    assessment_interest_options,
    assessment_skill_options,
    normalize_saved_career_ids,
    toggle_saved_career_id,
    unmatched_assessment_interest_options,
    unmatched_assessment_skill_options,
)
from recommendation_engine import (
    compare_required_skills,
    has_meaningful_career_match,
    normalize_label,
    rank_careers,
)


def career(career_id, skills=("Python", "SQL"), interests=("Data Science", "Research"), **overrides):
    result = {
        "id": career_id,
        "title": career_id.replace("-", " ").title(),
        "icon": "",
        "desc": "",
        "skills": skills,
        "interests": interests,
        "gap": ["Visualization"],
    }
    result.update(overrides)
    return result


class RecommendationEngineTests(unittest.TestCase):
    def test_uses_seventy_thirty_weighting(self):
        ranked = rank_careers(
            [career("weighted", skills=["Python", "SQL"], interests=["Data Science", "Research"])],
            ["Python"],
            ["Data Science", "Research"],
        )

        self.assertEqual(ranked[0].skill_score, 0.5)
        self.assertEqual(ranked[0].interest_score, 1.0)
        self.assertAlmostEqual(ranked[0].score, 65.0)

    def test_ranks_by_score_and_explains_components(self):
        ranked = rank_careers(
            [
                career("partial", skills=["Python", "SQL"], interests=["Data Science"]),
                career("strong", skills=["Python"], interests=["Data Science"]),
            ],
            ["Python"],
            ["Data Science"],
        )

        self.assertEqual([item.career_id for item in ranked], ["strong", "partial"])
        self.assertIn("Matched 1 of 1 required skills", ranked[0].explanation)
        self.assertIn("70%", ranked[0].explanation)
        self.assertEqual(ranked[0].missing_skills, ())
        self.assertEqual(ranked[1].missing_skills, ("SQL",))
        self.assertEqual(ranked[1].recommended_skills, ("SQL", "Visualization"))

    def test_duplicate_and_case_variants_do_not_inflate_matches(self):
        ranked = rank_careers(
            [career("unique", skills=["Python", "SQL"], interests=["Data Science"])],
            [" python ", "Python", "UNKNOWN", 17],
            ["DATA SCIENCE", "Data Science"],
        )

        self.assertEqual(ranked[0].matched_skills, ("Python",))
        self.assertEqual(ranked[0].matched_interests, ("Data Science",))
        self.assertAlmostEqual(ranked[0].score, 65.0)
        self.assertEqual(ranked[0].unrecognized_skills, ("UNKNOWN",))
        self.assertIn("Inputs without matching tags", ranked[0].explanation)

    def test_internal_whitespace_is_normalized_for_inputs_and_metadata(self):
        ranked = rank_careers(
            [
                career(
                    "whitespace",
                    skills=["Machine   Learning", "SQL"],
                    interests=["Data\tScience", "Research"],
                )
            ],
            [" machine \t learning "],
            [" data   science "],
        )

        self.assertEqual(ranked[0].matched_skills, ("Machine Learning",))
        self.assertEqual(ranked[0].matched_interests, ("Data Science",))
        self.assertEqual(ranked[0].missing_skills, ("SQL",))
        self.assertIn("Matched 1 of 2 required skills", ranked[0].explanation)
        self.assertIn("and 1 of 2 interest tags", ranked[0].explanation)
        self.assertAlmostEqual(ranked[0].score, 50.0)

    def test_metadata_duplicates_are_deduplicated_after_normalization(self):
        ranked = rank_careers(
            [
                career(
                    "deduplicated",
                    skills=["Python", " python ", "SQL"],
                    interests=["Data Science", " data   science ", "Research"],
                )
            ],
            ["PYTHON"],
            ["data science"],
        )

        self.assertEqual(ranked[0].matched_skills, ("Python",))
        self.assertEqual(ranked[0].matched_interests, ("Data Science",))
        self.assertEqual(ranked[0].missing_skills, ("SQL",))
        self.assertIn("Matched 1 of 2 required skills", ranked[0].explanation)
        self.assertIn("and 1 of 2 interest tags", ranked[0].explanation)
        self.assertAlmostEqual(ranked[0].score, 50.0)

    def test_normalize_label_preserves_display_case_but_normalizes_comparison(self):
        self.assertEqual(normalize_label("  Machine \t Learning "), "machine learning")

    def test_roadmap_skill_comparison_normalizes_but_preserves_required_labels(self):
        matched, missing = compare_required_skills(
            [" python ", "MACHINE\t LEARNING"],
            ["Python", "Machine   Learning", "SQL"],
        )

        self.assertEqual(matched, ("Python", "Machine Learning"))
        self.assertEqual(missing, ("SQL",))

    def test_missing_confirmed_inputs_have_no_combined_score(self):
        ranked = rank_careers([career("incomplete")], [], ["Data Science"])

        self.assertIsNone(ranked[0].score)
        self.assertIsNone(ranked[0].skill_score)
        self.assertEqual(ranked[0].interest_score, 0.5)
        self.assertIn("confirmed skills", ranked[0].unavailable_components)
        self.assertIn("No heuristic score is available", ranked[0].explanation)

    def test_missing_metadata_is_reported_without_a_score(self):
        ranked = rank_careers(
            [career("missing", skills=None, interests=["Data Science"])],
            ["Python"],
            ["Data Science"],
        )

        self.assertIsNone(ranked[0].score)
        self.assertIsNone(ranked[0].skill_score)
        self.assertIn("required skills", ranked[0].unavailable_components)

    def test_ties_use_stable_career_identifier(self):
        catalog = [
            career("zeta", skills=["Python"], interests=["Data Science"]),
            career("alpha", skills=["Python"], interests=["Data Science"]),
        ]
        first = rank_careers(catalog, ["Python"], ["Data Science"])
        second = rank_careers(reversed(catalog), ["Python"], ["Data Science"])

        self.assertEqual([item.career_id for item in first], ["alpha", "zeta"])
        self.assertEqual([item.career_id for item in first], [item.career_id for item in second])

    def test_duplicate_identifiers_are_not_scored(self):
        catalog = [
            career("duplicate", skills=["Python"], interests=["Data Science"], title="Duplicate", desc="Second"),
            career("duplicate", skills=["Python"], interests=["Data Science"], title="Duplicate", desc="First"),
        ]
        ranked = rank_careers(catalog, ["Python"], ["Data Science"])
        reversed_ranked = rank_careers(reversed(catalog), ["Python"], ["Data Science"])

        self.assertTrue(all(item.score is None for item in ranked))
        self.assertTrue(all("unique career identifier" in item.unavailable_components for item in ranked))
        self.assertEqual(
            [item.description for item in ranked],
            [item.description for item in reversed_ranked],
        )

    def test_empty_and_unknown_inputs_are_handled_deterministically(self):
        catalog = [career("b"), career("a")]
        first = rank_careers(catalog, ["not in catalog"], ["unknown interest"])
        second = rank_careers(catalog, ["not in catalog"], ["unknown interest"])

        self.assertEqual([item.career_id for item in first], ["a", "b"])
        self.assertEqual(
            [(item.score, item.unrecognized_skills, item.unrecognized_interests) for item in first],
            [(item.score, item.unrecognized_skills, item.unrecognized_interests) for item in second],
        )
        self.assertTrue(all(item.score == 0.0 for item in first))
        self.assertFalse(has_meaningful_career_match(first))

    def test_empty_confirmed_inputs_are_not_a_meaningful_match(self):
        ranked = rank_careers(CAREERS, [], [])

        self.assertTrue(all(item.score is None for item in ranked))
        self.assertFalse(has_meaningful_career_match(ranked))

    def test_meaningful_match_requires_a_positive_score_and_matched_tag(self):
        matching = rank_careers(
            [career("matching", skills=["Python"], interests=["Data Science"])],
            ["Python"],
            ["unknown interest"],
        )
        self.assertTrue(has_meaningful_career_match(matching))

    def test_string_inputs_are_treated_as_single_values(self):
        ranked = rank_careers(
            [career("single", skills=["Python"], interests=["Data Science"])],
            "Python",
            "Data Science",
        )

        self.assertEqual(ranked[0].matched_skills, ("Python",))
        self.assertEqual(ranked[0].matched_interests, ("Data Science",))
        self.assertEqual(ranked[0].score, 100.0)

    def test_curated_catalog_has_stable_identifiers_and_complete_metadata(self):
        self.assertEqual(len({item["id"] for item in CAREERS}), len(CAREERS))
        self.assertTrue(all(item["title"] and item["skills"] and item["interests"] for item in CAREERS))

    def test_assessment_interest_options_include_catalog_tags_and_existing_choices(self):
        options = assessment_interest_options()

        self.assertTrue(
            {
                interest
                for role in CAREERS
                for interest in role["interests"]
            }.issubset(options)
        )
        self.assertTrue(
            {
                "Artificial Intelligence",
                "Web Development",
                "Data Science",
                "Cyber Security",
                "Mobile App Development",
                "Cloud & DevOps",
                "Research & Innovation",
                "Business & Management",
                "Gaming",
                "Teaching",
                "UI/UX Design",
            }.issubset(options)
        )
        self.assertEqual(len(options), len(set(options)))

    def test_assessment_skill_options_include_catalog_tags_and_existing_choices(self):
        options = assessment_skill_options()
        catalog_skills = {
            skill
            for role in CAREERS
            for skill in role["skills"]
        }

        self.assertTrue(catalog_skills.issubset(options))
        self.assertTrue(
            {
                "Python",
                "Java",
                "C++",
                "JavaScript",
                "HTML/CSS",
                "SQL",
                "Machine Learning",
                "Data Analysis",
                "Cloud Computing",
                "Communication",
                "Problem Solving",
                "Team Work",
                "Leadership",
                "Creativity",
                "React",
                "Statistics",
                "Git",
            }.issubset(options)
        )
        self.assertEqual(len(options), len(set(options)))

    def test_unmatched_assessment_options_identify_profile_only_choices(self):
        self.assertEqual(
            set(unmatched_assessment_skill_options()),
            {
                "C++",
                "Communication",
                "Problem Solving",
                "Team Work",
                "Leadership",
                "Creativity",
            },
        )
        self.assertEqual(
            set(unmatched_assessment_interest_options()),
            {"Gaming", "Teaching", "UI/UX Design"},
        )

    def test_career_gap_skills_are_not_required_matching_tags(self):
        gap_only_skill = "Illustrative Gap Skill"
        catalog = [
            career(
                "gap-only",
                skills=["Python"],
                interests=["Data Science"],
                gap=[gap_only_skill],
            )
        ]

        recommendation = rank_careers(
            catalog,
            [gap_only_skill],
            ["Data Science"],
        )[0]

        self.assertNotIn(gap_only_skill, assessment_skill_options(catalog))
        self.assertEqual(recommendation.skill_score, 0.0)
        self.assertEqual(recommendation.matched_skills, ())
        self.assertEqual(recommendation.unrecognized_skills, (gap_only_skill,))
        self.assertAlmostEqual(recommendation.score, 30.0)

    def test_expanded_catalog_covers_backend_and_related_career_interests(self):
        careers_by_id = {item["id"]: item for item in CAREERS}
        expected_titles = {
            "java-backend-developer": "Java Backend Developer",
            "python-developer": "Python Developer",
            "cloud-devops-engineer": "Cloud/DevOps Engineer",
            "cybersecurity-analyst": "Cybersecurity Analyst",
            "software-tester-qa-engineer": "Software Tester/QA Engineer",
            "mobile-app-developer": "Mobile App Developer",
        }
        for career_id, title in expected_titles.items():
            self.assertEqual(careers_by_id[career_id]["title"], title)
            self.assertTrue(careers_by_id[career_id]["skills"])
            self.assertTrue(careers_by_id[career_id]["interests"])
            self.assertTrue(careers_by_id[career_id]["gap"])

        backend = careers_by_id["java-backend-developer"]
        self.assertIn("Java", backend["skills"])
        self.assertIn("Backend Development", backend["interests"])

    def test_all_career_roadmaps_are_role_specific_and_java_backend_starts_with_java(self):
        self.assertEqual(len(CAREERS), 10)
        self.assertTrue(
            all(
                isinstance(career_item.get("roadmap"), list)
                and len(career_item["roadmap"]) == 4
                and all(isinstance(phase, str) and phase.strip() for phase in career_item["roadmap"])
                for career_item in CAREERS
            )
        )

        java_backend = next(
            career_item for career_item in CAREERS
            if career_item["id"] == "java-backend-developer"
        )
        introduction = java_backend["roadmap"][0].casefold()
        self.assertIn("java fundamentals", introduction)
        self.assertIn("object-oriented programming", introduction)
        self.assertNotIn("python", introduction)

    def test_java_and_backend_inputs_match_java_backend_developer(self):
        ranked = rank_careers(
            CAREERS,
            ["Java", "SQL"],
            ["Backend Development"],
        )

        self.assertEqual(ranked[0].career_id, "java-backend-developer")
        self.assertAlmostEqual(ranked[0].score, 43.0)
        self.assertEqual(ranked[0].matched_skills, ("Java", "SQL"))
        self.assertEqual(ranked[0].matched_interests, ("Backend Development",))
        self.assertEqual(
            ranked[0].missing_skills,
            ("REST APIs", "Spring Boot", "Git"),
        )

    def test_existing_career_ids_and_saved_career_compatibility_are_preserved(self):
        existing = {
            "data-scientist": "Data Scientist",
            "ai-ml-engineer": "AI/ML Engineer",
            "full-stack-developer": "Full Stack Developer",
            "data-analyst": "Data Analyst",
        }
        careers_by_id = {item["id"]: item for item in CAREERS}
        for career_id, title in existing.items():
            self.assertEqual(careers_by_id[career_id]["title"], title)

        self.assertEqual(
            normalize_saved_career_ids(["Data Scientist", "full-stack-developer"]),
            ["data-scientist", "full-stack-developer"],
        )

    def test_recommended_skill_gaps_deduplicate_by_normalized_label(self):
        ranked = rank_careers(
            [
                career(
                    "deduplicated-gaps",
                    skills=["Python"],
                    interests=["Data Science"],
                    gap=[" SQL ", "sql", "Visualization"],
                )
            ],
            ["Python"],
            ["Data Science"],
        )

        self.assertEqual(ranked[0].recommended_skills, ("SQL", "Visualization"))

    def test_saved_career_titles_migrate_to_unique_stable_ids(self):
        saved = normalize_saved_career_ids(
            ["Data Scientist", "data-scientist", " Data   Scientist ", "Unknown Role"]
        )

        self.assertEqual(saved, ["data-scientist"])

    def test_saved_career_toggle_uses_ids_and_migrates_legacy_titles(self):
        saved = toggle_saved_career_id(["Data Scientist", "data-scientist"], "data-scientist")
        self.assertEqual(saved, [])

        saved = toggle_saved_career_id(saved, "data-scientist")
        self.assertEqual(saved, ["data-scientist"])
        self.assertEqual(normalize_saved_career_ids(saved), ["data-scientist"])


if __name__ == "__main__":
    unittest.main()
