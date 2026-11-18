# AI Career Path Predictor â€” Presentation & Demo Guide

This guide is based on the current project files. It describes a Streamlit career-exploration prototype with deterministic heuristic scoring. It does not describe a trained machine-learning predictor.

## Presentation plan

Suggested presentation length: 8â€“12 minutes, followed by the live demo and viva. Adjust the number of slides to fit the review slot.

### Slide 1 â€” Title

**AI Career Path Predictor**
Student career exploration with skills, interests, and illustrative roadmaps

- College/project name: [Add your details]
- Presenter(s): [Add names]
- Guide/faculty: [Add name]

**Speaker notes:** Introduce this as a student-focused prototype. Clarify that â€œAIâ€ is in the project name, but the current recommendation scorer is a deterministic heuristic, not a trained ML model.

### Slide 2 â€” Introduction

- Students can explore a curated catalog of 10 technology-related career examples.
- The application compares confirmed skills and interests with each roleâ€™s tags.
- Results provide a transparent relevance score and matching details.
- Roadmaps provide illustrative learning phases for career exploration.

**Speaker notes:** Emphasize that the application is intended to support exploration, not make decisions for a student.

### Slide 3 â€” Problem statement

- Students may want a structured way to compare their current interests and skills with example career paths.
- A list of job titles alone does not explain which selected profile tags match a role.
- This project demonstrates a simple, inspectable comparison as a starting point for exploration.

**Speaker notes:** These points describe the motivation for the prototype, not measured research findings. Do not present them as survey results or employment statistics.

### Slide 4 â€” Existing system / context

- Career exploration can involve browsing role descriptions and comparing skills manually.
- This project does not make claims about the capabilities or performance of any specific existing career platform.
- The prototype demonstrates a compact, rules-based comparison with a small curated catalog.

**Speaker notes:** â€œExisting systemâ€ here means the general manual exploration context. The project has no documented competitive analysis or comparison study.

### Slide 5 â€” Proposed system

- Collect profile details and ask the student to select and confirm skills and interests.
- Compare those confirmed labels with the career catalog.
- Rank roles using a deterministic heuristic and show matched tags and explanations.
- Let students browse the catalog, save example roles during the session, and view illustrative roadmaps.

**Speaker notes:** Assessment confirmation is required before ranked results are produced. The app does not use profile defaults alone as confirmed results.

### Slide 6 â€” Project objectives

- Demonstrate an assessment-to-recommendation workflow in Streamlit.
- Make the scoring components visible and understandable.
- Show which skill and interest tags matched a role.
- Provide sample roadmap phases for further exploration.
- Keep limitations clear: the catalog and roadmaps are illustrative, and the score is not a probability.

**Speaker notes:** These are objectives of the prototype, not claims about validated career guidance.

### Slide 7 â€” Technologies used

- **Python** â€” application and recommendation logic.
- **Streamlit** â€” web interface, forms, pages, and session state.
- **Pandas** and **scikit-learn** â€” declared in `requirements.txt`.
- **Current scoring implementation** â€” deterministic Python logic in `recommendation_engine.py`; no trained scikit-learn model is used for career prediction.
- **Gemini** â€” mentioned on the About page as planned/optional; not connected to current recommendation scoring.

**Speaker notes:** Distinguish package declarations from actual runtime use. Do not say that a package or service performs recommendation scoring unless the current code does so.

### Slide 8 â€” System modules

- **User interface and workflow â€” `app.py`:** Home, demo sign-up/login, assessment, results, dashboard, profile, saved careers, roadmap, and About pages.
- **Career catalog and assessment choices â€” `career_data.py`:** 10 career records, skill/interest tags, gaps, roadmap phases, assessment-option helpers, and saved-career ID helpers.
- **Recommendation engine â€” `recommendation_engine.py`:** label normalization, matching, score calculation, ranking, explanations, and meaningful-match detection.
- **Tests â€” `tests/test_recommendation_engine.py`:** tests for scoring, matching, catalog/options, roadmap structure, and saved-career helpers.

**Speaker notes:** Describe the responsibilities of these modules; avoid implying that each is a separate deployed service.

### Slide 9 â€” System architecture

```text
Student
  â”‚
  â–¼
Streamlit interface (app.py)
  â”œâ”€â”€ assessment options and career catalog â”€â”€â–º career_data.py
  â”œâ”€â”€ confirmed skills and interests â”€â”€â”€â”€â”€â”€â”€â”€â”€â–º recommendation_engine.py
  â”‚                                               â”‚
  â”‚                                               â””â”€â”€ ranked results and explanations
  â””â”€â”€ session state: profile and saved careers

Tests (tests/test_recommendation_engine.py) exercise the catalog helpers
and recommendation-engine behavior.
```

**Speaker notes:** This is a module-level view of the current application. There is no connected database or external recommendation API.

### Slide 10 â€” Application workflow

1. Open the Home page and choose demo sign-up or demo login.
2. Complete the Career Assessment.
3. Review and select skills and interests.
4. Confirm the selected inputs and submit.
5. Review ranked recommendations, matching details, and explanations.
6. Save a role, browse the catalog when there is no strong match, or open a roleâ€™s roadmap.

**Speaker notes:** Demo authentication does not create a persistent account. Saved careers and assessment data are session-only.

### Slide 11 â€” Career recommendation methodology

- The engine reads the confirmed skills and interests.
- It compares normalized labels with each careerâ€™s `skills` and `interests`.
- Normalization ignores capitalization and collapses whitespace.
- Each component is a fraction of distinct career tags matched.
- Ranking is deterministic; equal scores are ordered by career identifier.
- Unknown inputs do not count as matches; synonyms are not inferred.

**Speaker notes:** Career `gap` values are used as skills to explore; they do not become required skill tags for the scoring calculation.

### Slide 12 â€” Scoring formula

```text
Skill relevance    = matched required skills / distinct required skills
Interest relevance = matched interest tags / distinct interest tags

Score = 100 Ã— (0.70 Ã— skill relevance + 0.30 Ã— interest relevance)
```

- Skills contribute **70%**.
- Interests contribute **30%**.
- The output is a heuristic relevance score, not a calibrated probability, model accuracy, or guarantee of career fit.
- A combined score is unavailable when required inputs or career metadata are missing.

**Speaker notes and example:** For Java Backend Developer, selecting Java and SQL matches 2 of its 5 skills. Selecting Backend Development matches 1 of its 2 interests:

```text
100 Ã— (0.70 Ã— 2/5 + 0.30 Ã— 1/2) = 43.0
```

This is an arithmetic example of the current rule, not evidence of predictive accuracy.

### Slide 13 â€” Skill-gap identification

- Recommendation cards show matched required skills and list skills to explore.
- For a career, skills to explore can include its missing required skills and its curated `gap` entries.
- The roadmap page separately compares confirmed skills with the roleâ€™s required skills and example gap skills.
- These comparisons are illustrative and are not a validated assessment of a studentâ€™s abilities.

**Speaker notes:** A displayed gap does not mean an employer has verified that the skill is mandatory. The labels come from the projectâ€™s curated catalog.

### Slide 14 â€” Career learning roadmaps

- Each catalog role has four roadmap phases:
  1. Foundations
  2. Core skills
  3. Applied projects
  4. Portfolio and applications
- Phase descriptions are stored with each career in `career_data.py`.
- The UI displays example month ranges for the first three phases.
- The ranges are approximate illustrative planning examples, not guaranteed timelines, personalized schedules, employer requirements, or validated industry estimates.
- The app does not curate courses or external learning resources.

**Speaker notes:** Do not present the phase durations as research-based estimates or a promise of completion time.

### Slide 15 â€” Application screenshots

The submission already includes five genuine application screenshots. Use these existing files; do not create duplicates or present a screenshot as a page it does not show.

- **Dashboard:** `../Screenshots/presentation_dashboard.png`
- **Assessment:** `../Screenshots/presentation_assessment.png`
- **Recommendations:** `../Screenshots/presentation_recommendations.png`
- **Skill gaps:** `../Screenshots/presentation_skill_gaps.png`
- **Roadmap:** `../Screenshots/presentation_roadmap.png`

**Speaker notes:** The stored captures show a synthetic demo profile. The submission does not currently include a Home-page or no-strong-match screenshot among these five files.

### Slide 16 â€” Testing and verification

- Existing tests use Pythonâ€™s `unittest` framework.
- Coverage includes 70/30 scoring, matching and normalization, unknown inputs, missing metadata, stable ordering, assessment-option/catalog coverage, roadmap structure, and saved-career helper behavior.
- Test command:

  ```powershell
  python -m unittest discover -s tests -v
  ```

- An earlier historical run reported **27 tests passed**; that count is not a current result.
- Phase 1.21 clean-environment verification used Python 3.12.10. Installing `requirements.txt` succeeded and `python -m pip check` reported no broken requirements.
- Phase 1.21 ran `python -m unittest discover -s tests -q` from both the main project root and `FINAL_PROJECT_SUBMISSION/Source_Code`: **46 passed, 0 failed, 0 skipped** in each.
- Phase 1.19 browser checks covered synthetic-account authentication/navigation, assessment submission, recommendation matching, a no-strong-match case, a four-phase roadmap, and saving/removing a career. This was focused scenario testing, not exhaustive browser coverage; protected-page redirection was covered by an automated test but not forced in the browser.
- Phase 1.21 launched `app.py` successfully with a local HTTP 200 response. Browser verification loaded the Home page and student SVG; no console or page errors were captured.

**Speaker notes:** If presenting current test results, run the tests immediately before the review and report the actual output. Do not describe unit tests as proving recommendation accuracy or industry validity.

### Slide 17 â€” Limitations

- The catalog has 10 curated roles and is not live labor-market data.
- Scoring is a deterministic heuristic, not a trained ML predictor.
- Scores are not calibrated probabilities or guarantees of career fit.
- Matching normalizes case and whitespace but does not infer synonyms.
- Some selectable profile-only options have no matching career tags.
- Roadmaps and durations are illustrative, not validated learning plans or industry estimates.
- Authentication is demo-only; assessment data and saved careers are session-only.
- No database, live job-market service, Gemini/LLM recommendation scoring, or curated learning-resource service is connected.

**Speaker notes:** Be direct about limitations. Do not add accuracy, salary, placement, or employment claims; those measurements are not specified in the current implementation.

### Slide 18 â€” Future enhancements

Potential future work, only if approved and implemented later:

- Review and expand career-tag coverage.
- Evaluate the heuristic with students and document a suitable evaluation method.
- Consider optional learning resources with clear sourcing and maintenance.
- Consider persistent storage and real authentication.
- Evaluate whether explicit, reviewed synonym mappings would be useful.

**Speaker notes:** These are ideas, not existing features. Do not imply they are committed, underway, or already available.

### Slide 19 â€” Conclusion

- The project demonstrates a complete student-facing career exploration flow.
- It compares confirmed profile tags with a curated catalog using a transparent 70/30 heuristic.
- It provides matching explanations, session-only saved careers, a no-strong-match catalog path, and illustrative roadmaps.
- It is a prototype for exploration, not a trained predictor or a source of verified career requirements.

**Speaker notes:** Close by inviting questions about the implementation and its limitations.

## Live demo instructions

### Before the presentation

1. Open PowerShell in the project directory.
2. Activate the virtual environment if already created:

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

   Or use Command Prompt:

   ```bat
   .venv\Scripts\activate.bat
   ```

3. Launch the app:

   ```powershell
   streamlit run app.py
   ```

4. Open `http://localhost:8501` if the browser does not open automatically.
5. Confirm the application is showing the current project before the audience arrives. The steps above describe how to run it; they do not guarantee that a particular computer has the requirements installed.

### Demo A â€” Assessment and a ranked result

1. On Home, choose **Get Started** and complete the sign-up form with demo information. The sign-up is not real account creation. Alternatively, use the Home demo login form.
2. On Career Assessment, enter a name if needed. Review the preselected profile values; do not treat defaults as confirmed choices.
3. Select **Java** and **SQL** as skills. If other defaults are selected, remove them for this focused example.
4. Select **Backend Development** as the interest. If other defaults are selected, remove them.
5. Read the notes identifying profile-only options.
6. Check **I reviewed and confirm the selected skills and career interests.**
7. Select **Generate Career Recommendations**.
8. Point out the Java Backend Developer card. For these inputs, it should show:
   - 2 of 5 required skills matched (Java, SQL)
   - 1 of 2 interest tags matched (Backend Development)
   - **43.0/100** heuristic relevance
   - An explanation describing the 70%/30% weights
9. Explain the calculation: `100 Ã— (0.70 Ã— 2/5 + 0.30 Ã— 1/2) = 43.0`.
10. Point out the other careers' matched tags and the skills-to-explore list. Clarify that the catalog and those suggestions are illustrative.

If the visible result differs, check that only the specified tags are selected and that the assessment was submitted with confirmation.

### Demo B â€” Save and open a roadmap

1. On a recommendation card, select **Save Career**.
2. Open **Saved Careers** from the sidebar and show the saved role.
3. Return to results using the sidebar. Open the role using **View Details**.
4. Show all four roadmap phases, the required-skill comparison, and the duration note.
5. Select **Back to Results** to return.
6. If demonstrating removal, use **Remove Saved** on the saved-career page. Saved careers exist only for this browser session.

### Demo C â€” No-strong-match path

1. Open **Career Assessment** from the sidebar.
2. Select **Communication** as the only skill and **Gaming** as the only interest; remove other selected values.
3. Check the assessment confirmation box and submit.
4. Explain that both are profile-only choices without matching career tags in the current catalog.
5. Show the no-strong-match message. Select **Review Assessment** to demonstrate the return path, or use **Explore Career Catalog** to show catalog roles without a personalized ranking.
6. From the catalog, **View Learning Roadmap** opens a role roadmap.

### Finish the demo

- Return to the Home page or leave the app on Results for questions.
- Explain that saved careers and assessment data are session-only.
- Stop the local server from its terminal with `Ctrl+C` when the presentation is finished.

## Viva questions and answers

### 1. What is the purpose of this project?

It is a Streamlit prototype that helps students explore example careers by comparing confirmed skills and interests with a curated catalog.

### 2. Does the project use a trained AI or machine-learning model?

No. Career scoring is calculated by deterministic Python logic. The current application does not use a trained ML model for career prediction.

### 3. Why is â€œAIâ€ in the project name?

It is part of the project title. The current recommendation implementation is a rules-based heuristic; the name does not mean a trained AI model is connected.

### 4. What is Streamlit?

Streamlit is the Python framework used here to build the interactive web application, including forms, buttons, pages, and displayed results.

### 5. What are the main project modules?

`app.py` builds the interface and workflow, `career_data.py` provides the curated roles and assessment options, and `recommendation_engine.py` performs matching and scoring. The `tests` directory contains regression tests.

### 6. How are skills matched?

The engine compares confirmed skill labels with each careerâ€™s required skill tags. It ignores case and normalizes whitespace, but it does not automatically understand synonyms.

### 7. How are interests matched?

Confirmed interests are compared with each careerâ€™s interest tags using the same label normalization. Only matching tags count toward the interest component.

### 8. What is the recommendation formula?

The score is `100 Ã— (0.70 Ã— skill relevance + 0.30 Ã— interest relevance)`. Skill relevance is the fraction of distinct required career skills matched; interest relevance is the fraction of career interest tags matched.

### 9. Is a score of 80 an 80% probability of succeeding in that career?

No. It is a heuristic relevance score, not a calibrated probability, career-fit guarantee, or model-accuracy measure.

### 10. What happens to unknown inputs?

Inputs without matching career tags are treated as unrecognized and do not count as matches. If no role has a positive match, the app displays a no-strong-match message and offers assessment review or catalog browsing.

### 11. How does the application show a skill gap?

Recommendation cards list missing required skills and curated gap skills as skills to explore. The roadmap page compares confirmed skills with required skills and example gap skills. These are illustrative catalog comparisons, not validated assessments.

### 12. What does each roadmap contain?

Each career has four phases: foundations, core skills, applied projects, and portfolio/applications. The descriptions and first three displayed month ranges are illustrative, not validated schedules.

### 13. Are roadmap durations guaranteed or employer requirements?

No. They are approximate illustrative planning examples and are not guaranteed completion times, personalized schedules, employer-required timelines, or validated industry estimates.

### 14. How many careers are in the current catalog?

Ten curated career examples. They are static project data, not a live job-market feed.

### 15. Why must students confirm their assessment?

The Results page requires confirmed skills and interests. Preselected profile values are not considered confirmed until the student reviews and submits the assessment.

### 16. What do profile-only options mean?

They can be selected in the assessment but currently have no matching skill or interest tags in the career catalog. They therefore do not contribute to career relevance matches.

### 17. Can users save careers?

Yes. Users can save a recommendation and see or remove it on the Saved Careers page. The saved list is held for the current browser session, not stored in a persistent database.

### 18. Is sign-up real authentication?

No. Sign-up and login are demo-only interface flows; there is no connected authentication service.

### 19. What testing is present?

The project has `unittest` tests for scoring, matching and normalization, unknown inputs, missing metadata, ordering, assessment-option coverage, roadmap structure, and saved-career helpers. A test suite does not establish real-world recommendation accuracy.

### 20. Which test command can be used?

From the project directory with the virtual environment active, run `python -m unittest discover -s tests -v`. The Windows README documents creating and activating a Python 3.12 environment.

### 21. What are important limitations?

The catalog is static and illustrative; scoring is heuristic and exact-label based after normalization; there is no trained model, live job-market data, connected Gemini scoring, database, persistent saved data, or curated learning-resource service.

### 22. What improvements could be considered later?

Possible future work includes evaluating the heuristic, reviewing catalog/tag coverage, providing sourced learning resources, or considering persistence and real authentication. These are ideas only and are not current features.

### 23. Which dependencies are listed?

`requirements.txt` lists Streamlit, Pandas, and scikit-learn. The presence of scikit-learn in that file does not mean a trained scikit-learn model is used for recommendation scoring.

### 24. How could the score be improved or validated?

The current implementation does not specify an accuracy metric or validation study. A future evaluation would need an explicitly designed dataset and evaluation method before reporting performance numbers. No such metrics are currently specified.

## Important technical explanations

### Relevance components

For a given career, the engine first deduplicates career tags after case/whitespace normalization. It counts how many required skills match the confirmed skill set, then divides by that careerâ€™s distinct required skill count. It calculates interest relevance in the same way using interest tags. The weights are constants in `recommendation_engine.py`: skill weight `0.70`, interest weight `0.30`.

### â€œSkills to exploreâ€ versus matching tags

The `gap` list in `career_data.py` contributes suggestions shown as skills to explore. Scoring uses the careerâ€™s `skills` and `interests` metadata, not the `gap` list as additional required skills. Missing required skills can also appear in the skills-to-explore display.

### Unknown and no-match inputs

The engine reports confirmed labels that do not match a given careerâ€™s tags as unrecognized for that role. Scores may be zero when inputs are present but none match; `has_meaningful_career_match` checks for a positive score with at least one matched tag. If none qualify, the UI offers a catalog view without presenting it as a personalized ranking.

### Data and persistence

Career titles, tags, gaps, and roadmap phases are defined statically in `career_data.py`. The app uses Streamlit session state for profile information and saved careers. A persistent database is not connected.

### Screenshot guidance

Use the five existing submission screenshots listed under Slide 15. They are genuine captures of the current demo UI; do not duplicate them or label them as Home/no-strong-match views.
