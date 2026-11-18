# AI Career Path Predictor — Final Handover Report

## 1. Project overview

AI Career Path Predictor is a student-focused Streamlit prototype for exploring a curated set of career examples. It compares confirmed student skills and interests with career tags, presents ranked relevance scores and matching explanations, and offers illustrative roadmaps.

This is a deterministic career-exploration prototype, not a trained machine-learning model and not a production career prediction service.

## 2. Technology stack

- Python 3.10 or newer (the verified environment used Python 3.12.10)
- Streamlit for the application UI and session state
- Pandas and scikit-learn are declared dependencies
- Career recommendation scoring is implemented with deterministic Python logic; it does not use a trained scikit-learn model.

The existing project environment was previously observed with Streamlit 1.66.1, Pandas 2.2.2, and scikit-learn 1.7.2 installed, meeting the minimum versions in `requirements.txt`. The separate Phase 1.21 clean environment resolved Streamlit 1.66.1, Pandas 3.1.0, and scikit-learn 1.9.1. These are observed environment versions, not pinned project versions.

## 3. Implemented features

- Demo-only registration/login and session-based profile flow. Registration validates required fields and email format, requires password confirmation, and rejects duplicate email addresses. Login requires a registered email and matching password; failed login does not create an account.
- Passwords are stored as salted PBKDF2-HMAC-SHA256 hashes in the current Streamlit session, not as plaintext. The account registry is session-only.
- Logout clears session profile/assessment details and returns to public Home; saved careers are intentionally preserved for the current browser session.
- About is available while signed out, shows profile information only while signed in, and provides Home navigation to the landing page or authenticated Dashboard as appropriate.
- Unauthenticated attempts to open protected pages return to Home.
- Confirmed skills and interests assessment
- Ranked recommendations with matched-tag explanations and skill-to-explore suggestions
- Career catalog browsing, including a no-strong-match path
- Session-only saved careers
- Career details and four-phase illustrative roadmaps
- Recommendation/catalog and authentication/navigation regression tests

Authentication is still a demo feature, not production authentication. No persistent account database or production authentication system is implemented.

## 4. Recommendation methodology

The engine matches normalized, exact career skill and interest tags against confirmed assessment inputs. It ranks careers deterministically using:

```text
Score = 100 × (0.70 × skill relevance + 0.30 × interest relevance)
```

Skills contribute 70% and interests contribute 30%. The result is a heuristic relevance indicator, not a calibrated probability, accuracy measure, or guarantee of career fit. Synonyms are not inferred.

## 5. Test results

The latest full project-root suite before the clean-environment phase was executed during Phase 1.19:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
```

**Phase 1.19 main-project result:** 46 tests run, 46 passed, 0 failed; exit code 0.

**Submission source result from Phase 1.17:** 46 tests run, 46 passed, 0 failed, 0 skipped; exit code 0. The submission copy was not rerun in Phase 1.19.

Python syntax validation passed for the changed app, authentication helper, and authentication tests in both copies. The Phase 1.19 project test used the existing project virtual-environment interpreter; the Phase 1.17 submission test also used that interpreter.

**Phase 1.21 clean-environment result:** A separate temporary Python 3.12.10 environment was created outside the project. Dependencies from `requirements.txt` installed successfully; `python -m pip check` found no broken requirements. The temporary environment ran both the project-root and submission-source suites successfully: 46 passed, 0 failed, 0 skipped in each. It launched `app.py` successfully with a local HTTP 200 response. Browser verification confirmed the Home page and student SVG loaded without console or page errors. See the Phase 1.21 record below for commands and preservation results.

## 6. Documentation files

- `Documentation/README.md` — project description, Windows setup/run instructions, usage, scoring, tests, and limitations.
- `Documentation/PROJECT_PRESENTATION_GUIDE.md` — slide outline, speaker notes, demo instructions, and viva questions.
- `Submission_Checklist.md` — verified contents, current test results, pending items, and limitations.

## 7. Presentation status

- `Presentation/AI_Career_Path_Predictor_Presentation.pptx` contains 19 slides and five genuine application screenshots.
- The main project presentation and submission copy have matching SHA-256 checksums. Before Phase 1.22 edits, both had SHA-256 `A7196BA1C2C1543DC76149853C5727AD5CC391BCD06A6B752342BCD519DB37D`; after the approved Slide 16 text correction, both have SHA-256 `0EF1674AA846870C3BB325C48819C561A147DECB52F564D762CE7003A87CBD77`.
- Both copies parse successfully, have the expected slide titles, contain five embedded images, and pass package integrity checks.
- Phase 1.22 did not render the decks. In Phase 1.23, all 19 slides were rendered and visually inspected; see the final audit below.
- Presenter and institution fields remain labeled placeholders because those details are not available in the reviewed project documentation.

## 8. Submission folder contents

```text
FINAL_PROJECT_SUBMISSION/
|-- Documentation/
|   |-- README.md
|   `-- PROJECT_PRESENTATION_GUIDE.md
|-- Presentation/
|   `-- AI_Career_Path_Predictor_Presentation.pptx
|-- Screenshots/
|   |-- presentation_assessment.png
|   |-- presentation_dashboard.png
|   |-- presentation_recommendations.png
|   |-- presentation_roadmap.png
|   `-- presentation_skill_gaps.png
|-- Source_Code/
|   |-- app.py
|   |-- auth_utils.py
|   |-- career_data.py
|   |-- recommendation_engine.py
|   |-- requirements.txt
|   |-- run.bat
|   |-- .streamlit/config.toml
|   |-- assets/career-student.svg
|   `-- tests/
|       |-- test_recommendation_engine.py
|       `-- test_auth_navigation.py
|-- FINAL_HANDOVER_REPORT.md
`-- Submission_Checklist.md
```

## 9. Phase 1.13–1.21 verification

- **Phase 1.13:** The prior phase's browser verification used a synthetic demo profile and reported correct profile display, logout cleanup, and Home/About navigation. Browser verification was not repeated in Phases 1.14 or 1.17.
- **Phase 1.16:** Added registered-account login validation and registration checks for name, email format, non-empty password, matching confirmation, and duplicate email. Failed login does not authenticate or create accounts. Passwords use salted PBKDF2-HMAC-SHA256 hashes; account data remains session-only.
- **Phase 1.17:** Synchronized `app.py`, new `auth_utils.py`, and updated `tests/test_auth_navigation.py` into `Source_Code`. Updated the submission README, checklist, and this report. Existing career data, recommendation engine, recommendation tests, launcher, configuration, and asset files were already identical and were preserved.
- Phase 1.17 SHA-256 comparisons recorded that the submission app, auth helper, both tests, recommendation and career source, requirements, launcher, Streamlit config, SVG, README, and presentation guide matched their project originals at that time. Phase 1.20 intentionally updated the submission README and presentation guide, so those two documentation files now differ from the main-project copies. The application source, tests, launcher, configuration, and asset hashes still match; the main and submission presentations have matching hashes, and all five screenshot files remain unchanged.
- No browser verification or clean-environment setup was performed during Phase 1.17. No application functionality beyond the Phase 1.16 authentication changes was modified in Phase 1.17.
- **Phase 1.18:** Browser verification used synthetic credentials and observed registration/login behavior, rejection of wrong and unregistered credentials, logout cleanup, Home/About navigation, and session reset. No application code was changed.
- **Phase 1.19 automated tests:** The main project suite ran from the project root and reported **46 passed, 0 failed**. This did not rerun the submission-copy suite.
- **Phase 1.19 browser assessment and recommendations:** Submitted an assessment with confirmed Python, Machine Learning, and SQL skills, plus Data Science and Artificial Intelligence interests. Data Scientist ranked first at **72.0/100**, showing 3 of 5 required skills and 2 of 2 interest tags matched, with matching details and skills to explore. The implementation uses a deterministic 70/30 skill/interest heuristic; the displayed score is not a probability or validated prediction.
- **Phase 1.19 no-match behavior:** Confirmed Communication and Gaming are profile-only options; submitting those inputs showed the no-strong-match warning and no personalized career cards, without an observed crash.
- **Phase 1.19 roadmap and saved careers:** The Data Scientist roadmap showed four phases, three confirmed skills, and skills to explore, and was labeled illustrative. Data Scientist was saved, appeared in Saved Careers, was removed, and then showed the empty state.
- **Phase 1.19 authentication/navigation:** Correct registered credentials succeeded; wrong and unregistered credentials were rejected. About displayed the active synthetic profile; authenticated Home returned to Dashboard; logout cleared the displayed profile and returned to public Home. Unauthenticated About/Home navigation also worked.
- **Phase 1.19 errors and coverage limits:** During the final instrumented browser pass, captured JavaScript console errors and page errors were empty. Protected-page redirect has an automated test but was not forced in the browser. Session reset was not repeated in Phase 1.19 (it was browser-tested in Phase 1.18). Every assessment combination, recommendation path, and role roadmap was not exhaustively tested.
- **Phase 1.20:** Updated the submission README, checklist, handover report, and presentation guide with the Phase 1.19 results. This was a documentation-only phase; no tests or browser scenarios were rerun.
- **Phase 1.21 clean-environment setup:** Created a separate temporary virtual environment outside the project using Python 3.12.10. Installed only the packages from `requirements.txt`, without upgrading pip or changing the manifest. Installation completed successfully; `python -m pip check` reported no broken requirements. Resolved direct dependency versions were Streamlit 1.66.1, Pandas 3.1.0, and scikit-learn 1.9.1; these are observed versions, not pinned requirements.
- **Phase 1.21 application launch:** With the temporary environment activated and the project root as the working directory, launched `streamlit run app.py --server.headless true --server.port 18721`. Streamlit reported startup and `http://127.0.0.1:18721` returned HTTP 200. The browser displayed the Home page and its student SVG; no browser console errors or page errors were captured. No account was created.
- **Phase 1.21 dependency coverage:** The app's only non-standard direct import is Streamlit, which is declared in `requirements.txt`. Pandas and scikit-learn are also declared and installed; current application source does not import them directly.
- **Phase 1.21 clean-environment tests:** Ran `python -m unittest discover -s tests -q` from the project root and again from `FINAL_PROJECT_SUBMISSION/Source_Code`, using the activated temporary environment: **46 tests passed, 0 failed, 0 skipped** in each run. These are fresh results separate from the Phase 1.19 and Phase 1.17 results.
- The test runs printed Streamlit `missing ScriptRunContext` warnings stating they can be ignored in bare mode; both suites completed successfully without test errors.
- Preservation checks confirmed SHA-256 matches for application source, authentication helper, career data, recommendation engine, test files, dependency manifests, assets, presentation files, and screenshots. The existing project `.venv` inventory and timestamps were unchanged. The temporary environment was removed after verification; no new project files or caches were left behind.

## 10. Phase 1.22 final submission and placeholder audit

- Inspected the main project README and presentation guide; submission Documentation README and presentation guide; final handover report and checklist; project and submission source structures; all five project and submission screenshots; and both PowerPoint files.
- Project title is consistently **AI Career Path Predictor** across README, guides, deck title, and source project. Both presentation copies had 19 slides in order and identical pre-edit hashes. Package integrity was valid before and after the edit.
- The title slide still has blank `Presenter` and `Institution` lines. Both presentation guides retain `[Add your details]`, `[Add names]`, and `[Add name]` fields for college/project name, presenter(s), and guide/faculty. No confirmed personal or institutional values were available. Department, academic year, and roll number are also pending if required.
- The five stored screenshot files are Dashboard, Assessment, Recommendations, Skill Gaps, and Roadmap. Both guides now point to those existing files; they do not claim the set includes a Home-page or no-strong-match capture.
- Slide 16 was text-corrected only in both decks. It retains the historical **27 passed** result as historical and separately lists Phase 1.21: main project **46 passed, 0 failed, 0 skipped**; submission copy **46 passed, 0 failed, 0 skipped**; clean setup and `pip check` succeeded. The only modified package member was `ppt/slides/slide16.xml`; slide order, slide count, geometry, and embedded images were preserved.
- Both decks were rechecked for 19 slides, five embedded image files, and ZIP integrity; their final SHA-256 hashes match at `0EF1674AA846870C3BB325C48819C561A147DECB52F564D762CE7003A87CBD77`. The five embedded images match the five submission screenshot files, and each submission screenshot hash matches its corresponding main-project screenshot.
- Presentation text, package structure, and screenshot content were inspected, but the decks were **not rendered in Phase 1.22**. Visual readability/layout is therefore not claimed as verified in this audit.
- Updated both presentation guides, this handover report, and `Submission_Checklist.md`. SHA-256 checks confirmed project/submission application source, authentication helper, career data, recommendation engine, tests, requirements, and run scripts match; screenshots remain identical across copies. No application source, tests, dependency manifests, screenshots, or assets were changed. The existing `.venv` was not used or modified. No Phase 1.22 tests were run.

## 11. Known limitations

- Career catalog data is static and illustrative; there is no live job-market data.
- Recommendations use a deterministic heuristic, not a trained ML model.
- Scores are not calibrated probabilities or career-outcome predictions.
- Matching is based on normalized labels and does not automatically recognize synonyms.
- Roadmaps and durations are illustrative, not personalized, validated, or employer-required.
- Authentication is demo-only and not production-ready. Registered accounts and password hashes exist only in the current session; there is no persistent account database or production authentication system.
- Profile/assessment data and saved careers are session-only; logout clears profile data while preserving saved careers in that browser session.
- Accuracy, salary, placement, and employment metrics are not specified.

## 12. Pending items

- Provide exact presenter name(s) and preferred display spelling.
- Provide the official institution/college name.
- Provide department, guide/faculty/supervisor name and title, academic year, and roll number only if required by the submission format.
- Keep these fields blank or as existing placeholders until confirmed; none were inferred.
- The clean-environment run used Python 3.12.10 only. Other documented Python 3.10+ versions, including the installed Python 3.14.3, were not tested.
- If additional browser coverage is required, test protected-page redirection directly and exercise more assessment/recommendation inputs and career roadmaps. Protected-page behavior has an automated regression test, but was not browser-forced in Phase 1.19 or Phase 1.21.
- PowerPoint visual rendering/readability was not verified in Phase 1.22; it was completed in Phase 1.23.

## 13. Final readiness status

**Ready for submission after required personal details and visual review.** At the time of Phase 1.22, those details and visual review were still pending. The Phase 1.23 visual review has since been completed; required personal/institutional fields remain pending. The package is a student prototype and is **not production-ready**.

## 14. Phase 1.23 final handover and submission-readiness audit

### Project structure

The main project is located at the workspace root. Its application files are `app.py`, `auth_utils.py`, `career_data.py`, `recommendation_engine.py`, and `requirements.txt`; supporting files include `run.bat`, `.streamlit/config.toml`, `assets/career-student.svg`, and `tests/test_auth_navigation.py` plus `tests/test_recommendation_engine.py`. The main README and presentation guide are at the project root.

The submission copy is under `FINAL_PROJECT_SUBMISSION/`:

- `Source_Code/` contains the same application, authentication, career/recommendation, requirements, launcher, Streamlit configuration, SVG asset, and tests.
- `Documentation/README.md` and `Documentation/PROJECT_PRESENTATION_GUIDE.md` contain submission-specific setup and presentation guidance.
- `Presentation/AI_Career_Path_Predictor_Presentation.pptx` is the submission deck.
- `Screenshots/` contains the five existing application screenshots: `presentation_dashboard.png`, `presentation_assessment.png`, `presentation_recommendations.png`, `presentation_skill_gaps.png`, and `presentation_roadmap.png`.
- `Submission_Checklist.md` and this `FINAL_HANDOVER_REPORT.md` record readiness and verification.

### Verification history

- **Phase 1.19:** The main project suite reported 46 passed and 0 failed. The submission copy was not rerun in that phase. The phase also browser-tested the specific authentication, assessment, recommendation, no-match, roadmap, and saved-career scenarios listed above; it was not exhaustive.
- **Phase 1.21:** Python 3.12.10 clean-environment setup using the documented requirements succeeded, `pip check` found no broken requirements, and Streamlit returned local HTTP 200. Both the main and submission suites each reported 46 passed, 0 failed, and 0 skipped. Browser verification loaded Home and the student SVG without captured console or page errors.
- **Phase 1.22:** Placeholder/presentation audit completed and the authorized Slide 16 and guide corrections were applied. The historical 27-test result remains historical. Both 19-slide decks passed ZIP integrity checks, retained five embedded screenshots, and matched. No tests or visual rendering were claimed for that phase.
- **Phase 1.23:** Using the existing project `.venv` (Python 3.12.10), ran `.\.venv\Scripts\python.exe -m unittest discover -s tests -q` from the main project root and the equivalent command from `FINAL_PROJECT_SUBMISSION\Source_Code` using the main project's absolute interpreter path. Each run completed with 46 tests, 46 passed, 0 failed, 0 skipped, and exit code 0. Streamlit emitted `missing ScriptRunContext` warnings stating they can be ignored in bare mode. No dependency installation or upgrade was performed.

### Source, documentation, presentation, and screenshot checks

- SHA-256 comparisons confirmed the main and submission copies match for `app.py`, `auth_utils.py`, `career_data.py`, `recommendation_engine.py`, both test files, and `requirements.txt`. The submission copy also includes matching launcher/configuration and the career SVG asset. No required application files were found missing from the submission source copy.
- The main and submission presentation decks are byte-identical, contain 19 slides in the same order, pass ZIP integrity checks, and retain five embedded images. Their SHA-256 is `0EF1674AA846870C3BB325C48819C561A147DECB52F564D762CE7003A87CBD77`. Slide 16 correctly separates the historical 27-test result from the Phase 1.21 results.
- The presentation guides refer to the five existing screenshots; all five screenshot files exist, were readable on inspection, match their corresponding copies by SHA-256, and match the embedded presentation images. There is no Home-page or no-match screenshot.
- All 19 slides were rendered and visually inspected in Phase 1.23. No obvious readability, alignment, clipping, or image-placement issue was observed. This review does not constitute official submission approval.
- The main README, submission README, documentation README, both presentation guides, checklist, and handover report were reviewed for setup, implemented behavior, recommendation scoring, limitations, test history, and placeholder status. This Phase 1.23 update changed only this handover report and the checklist.

### Preservation

Phase 1.23 SHA-256 and environment-inventory checks confirmed no changes to application/authentication/career/recommendation source, tests, dependency files, assets, presentation files, screenshots, or the existing `.venv`. Temporary slide-render and test-output files were stored outside the project and cleaned up after verification. No source, tests, dependencies, PowerPoint content, or screenshots were changed in Phase 1.23.

### Pending details and verification

- Presenter name(s) and official institution/college name are requested by the title-slide fields and remain blank/pending user input.
- Department, guide/faculty/supervisor name and title, academic year, and roll number remain pending if required by the receiving institution; the applicable submission format was not supplied, so their mandatory status is unknown.
- Phase 1.23 did not repeat browser workflows. The Phase 1.21 Home-page smoke check and Phase 1.19 browser scenarios are recorded above; exhaustive browser scenarios, all assessment/recommendation combinations, and every roadmap remain untested.
- Only Python 3.12.10 was used for clean-environment verification and Phase 1.23 test runs; other supported Python versions were not verified.
- The application has no live job-market data; recommendations are heuristic indicators, career outcomes are not guaranteed, roadmaps are illustrative, and demo authentication/accounts/saved careers are session-only. Production readiness is not established.

### Final readiness

**Ready for submission after required personal details and visual review.** The visual review has been completed. Presenter and institution details remain pending, and the mandatory status of the other listed academic fields depends on requirements not provided. This report does not claim official approval or production readiness.
