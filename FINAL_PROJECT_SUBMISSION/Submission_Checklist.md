# Final Project Submission Checklist

## Verified

- [x] Phase 1.16 authentication files synchronized: `app.py`, `auth_utils.py`, and `tests/test_auth_navigation.py`; existing career code, recommendation code, and regression tests are present.
- [x] Submission README documents validated registration, duplicate-email rejection, password confirmation, registered-account-only login, salted PBKDF2-HMAC-SHA256 hashing, and session-only demo accounts.
- [x] Authentication tests cover successful registration/login, invalid and duplicate registration, incorrect/unregistered credentials, failed-login state, and hash storage.
- [x] Documentation states recommendation scores are heuristic relevance indicators (not probabilities), and career data and roadmaps are illustrative.
- [x] Five screenshot assets remain present: dashboard, assessment, recommendations, skill gaps, and roadmap.
- [x] Main project presentation and submission-folder presentation remain present and have matching SHA-256 checksums.
- [x] The prior presentation-review phase verified both presentations as 19-slide decks with expected slide titles, five embedded screenshots, and valid package integrity.
- [x] Phase 1.17 main project suite: **46 tests passed, 0 failed, 0 skipped; exit code 0.**
- [x] Phase 1.17 submission source suite: **46 tests passed, 0 failed, 0 skipped; exit code 0.**
- [x] Phase 1.19 project-root regression suite: **46 tests passed, 0 failed; exit code 0.** This run was from the main project, not the submission copy.
- [x] Phase 1.19 browser checks used synthetic credentials and verified account registration/login, incorrect and unregistered credential rejection, logout/profile cleanup, and authenticated/unauthenticated Home/About navigation.
- [x] Phase 1.19 browser checks verified confirmed assessment submission, recommendation display and matching details, the no-strong-match state, the four-phase illustrative roadmap, and saved-career add/remove behavior.
- [x] During the final instrumented Phase 1.19 browser pass, no JavaScript console errors or page errors were captured.
- [x] Phase 1.21 clean setup: isolated Python 3.12.10 environment created outside the project; manifest dependencies installed and `pip check` reported no broken requirements.
- [x] Phase 1.21 clean environment: Streamlit 1.66.1, Pandas 3.1.0, and scikit-learn 1.9.1 imported; application server started from `app.py` and returned local HTTP 200.
- [x] Phase 1.21 browser verification loaded the Home page and student SVG; no browser console errors or page errors were captured.
- [x] Phase 1.21 clean-environment project-root suite: **46 tests passed, 0 failed, 0 skipped**. This is separate from the Phase 1.19 project environment run.
- [x] Phase 1.21 clean-environment submission source suite: **46 tests passed, 0 failed, 0 skipped**. This is separate from the earlier Phase 1.17 submission run.
- [x] The Phase 1.21 temporary environment was removed after verification; the existing project `.venv` was inspected but not used for installation, launch, or tests and was not modified.
- [x] SHA-256 comparisons confirm project and submission application source, tests, manifests, assets, presentation files, and screenshots match their pre-verification versions; the existing `.venv` inventory and timestamps were unchanged.
- [x] Main and submission README setup instructions document Python 3.10+, the verified Python 3.12 setup commands, activation, dependency installation/check, launch, and test commands.
- [x] Python syntax validation passed for app/auth source and both test files in both project copies.
- [x] SHA-256 comparisons confirm current application source, tests, launcher, configuration, and assets match project originals. The presentation guide and README were intentionally updated in Phase 1.20 and therefore are not expected to match the main-project documentation copies.
- [x] No presentation or screenshot files were modified during Phase 1.17.
- [x] Phase 1.20 updated only submission documentation; source, presentation, and screenshot preservation hashes were rechecked.
- [x] Phase 1.22 audited the main and submission READMEs, both presentation guides, handover report, checklist, project/source-copy structure, screenshots, and both PowerPoint packages.
- [x] Phase 1.22 presentation title and project naming are consistent. Both decks contain 19 ordered slides, pass ZIP integrity checks, and include the five existing application screenshots.
- [x] Before Phase 1.22 presentation edits, both decks had matching SHA-256 `A7196BA1C2C1543DC76149853C5727AD5CC391BCD06A6B752342BCD519DB37D`.
- [x] Phase 1.22 updated only slide 16 text in each deck. The old 27-test result remains explicitly historical; the verified Phase 1.21 main and submission results and clean setup/`pip check` result are shown.
- [x] Phase 1.22 updated both presentation guides to refer to the five existing dashboard, assessment, recommendations, skill-gap, and roadmap screenshots, and corrected stale test/setup notes. No duplicate screenshots were created.
- [x] Phase 1.22 SHA-256 confirms the main and submission decks match after editing: `0EF1674AA846870C3BB325C48819C561A147DECB52F564D762CE7003A87CBD77`.
- [x] Phase 1.22 revalidated both PowerPoint ZIP packages, 19-slide count, and five embedded images. Slide geometry, slide count, and images were not changed.
- [x] Phase 1.22 updated this checklist and the handover report with the audit and verification boundaries. No Phase 1.22 tests were run or claimed.
- [x] Phase 1.22 SHA-256 comparisons found the ten project/submission source, test, and dependency files identical; all five main/submission screenshot pairs also match. No source, tests, dependencies, screenshots, or `.venv` were changed in this phase.
- [x] Phase 1.23 confirmed the main project and `FINAL_PROJECT_SUBMISSION` include the application, authentication helper, career data, recommendation engine, tests, dependency manifest, configuration, asset, documentation, presentation, screenshots, checklist, and handover report.
- [x] Phase 1.23 SHA-256 comparisons confirmed the corresponding application, authentication, career/recommendation, test, and dependency files match between the main project and submission source copy. Required configuration and the SVG asset are included in both.
- [x] Phase 1.23 main project tests ran with the existing `.venv\Scripts\python.exe -m unittest discover -s tests -q`: **46 tests run, 46 passed, 0 failed, 0 skipped; exit code 0**.
- [x] Phase 1.23 submission source tests ran with the main project's existing `.venv\Scripts\python.exe -m unittest discover -s tests -q`: **46 tests run, 46 passed, 0 failed, 0 skipped; exit code 0**.
- [x] Phase 1.23 test output included Streamlit `missing ScriptRunContext` warnings stating they can be ignored in bare mode; both runs ended with `OK`. No test failures or errors were reported.
- [x] Phase 1.23 verified both PowerPoint files contain 19 slides in the same order, have matching SHA-256 `0EF1674AA846870C3BB325C48819C561A147DECB52F564D762CE7003A87CBD77`, pass ZIP integrity checks, and retain five embedded images matching the five submission screenshots.
- [x] Phase 1.23 confirmed Slide 16 preserves the historical 27-test result and separately reports Phase 1.21's 46-pass main and submission results and successful clean setup/dependency consistency check. Both guides reference the five existing screenshots.
- [x] Phase 1.23 rendered and visually inspected all 19 slides in the identical presentation decks. No obvious readability, alignment, clipping, or image-placement issue was observed; personal/institutional placeholders remain unfilled.
- [x] Phase 1.23 confirmed all five existing screenshots are present, readable, and hash-identical between the main project and submission copy. No Home-page or no-match screenshot is included.
- [x] Phase 1.23 preservation checks found the protected application, authentication, career/recommendation, test, dependency, asset, presentation, and screenshot hashes unchanged; the existing `.venv` inventory and timestamps remained unchanged. Only this checklist and the handover report were updated during this phase.

## Pending User Input

- [ ] Presenter name(s): provide exact spelling and preferred display format.
- [ ] Institution / college: provide the official name.
- [ ] Department: provide the official department name, if required.
- [ ] Guide / faculty / supervisor: provide the exact name and title, if required.
- [ ] Academic year: provide the exact year/range, if required.
- [ ] Roll number: provide the exact value, if required.
- [ ] Until supplied, keep the title-slide presenter and institution lines blank and the guide placeholders unchanged; no details were inferred.

## Pending Verification

- [ ] Phase 1.19 did not browser-test protected-page redirection, session reset, every assessment/recommendation combination, all career roadmaps, or the entire assessment and roadmap data surface. Protected-page redirection has an automated regression test; session reset was browser-tested in Phase 1.18.
- [ ] Phase 1.23 did not repeat browser workflows. Phase 1.21's browser check covered the Home page and student SVG, and Phase 1.19 covered the specific flows recorded in this checklist; exhaustive browser coverage remains outstanding.
- [ ] The clean-environment run used Python 3.12.10 only; other documented Python 3.10+ versions, including the installed Python 3.14.3, were not tested.
- [ ] Whether department, guide/faculty, academic year, and roll number are mandatory cannot be confirmed without the recipient's submission requirements.
- [ ] Production deployment, live job-market data, model accuracy, and career outcomes are not tested or established by this project.

## Recorded test runs

Phase 1.21 clean-environment command executed from the main project root with the temporary environment activated:

```powershell
python -m unittest discover -s tests -q
```

Result: **46 tests run, 46 passed, 0 failed, 0 skipped; exit code 0.**

Phase 1.21 clean-environment submission source command executed from `FINAL_PROJECT_SUBMISSION\Source_Code` using the same temporary environment:

```powershell
python -m unittest discover -s tests -q
```

Result: **46 tests run, 46 passed, 0 failed, 0 skipped; exit code 0.**

Previously recorded Phase 1.19 main project command:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
```

Result: **46 tests run, 46 passed, 0 failed; exit code 0.**

Previously recorded Phase 1.17 submission source command executed from `FINAL_PROJECT_SUBMISSION\Source_Code` using the existing main-project virtual-environment interpreter:

```powershell
D:\AI_Career_Path_Predictor_UI_Phase1\AI_Career_Path_Predictor_UI\.venv\Scripts\python.exe -m unittest discover -s tests -q
```

Result: **46 tests run, 46 passed, 0 failed, 0 skipped; exit code 0.**

Phase 1.23 main project command, executed from the project root with the existing virtual-environment interpreter:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
```

Result: **46 tests run, 46 passed, 0 failed, 0 skipped; exit code 0.** Streamlit emitted its `missing ScriptRunContext` bare-mode warning.

Phase 1.23 submission source command, executed from `FINAL_PROJECT_SUBMISSION\Source_Code` with the existing main-project virtual-environment interpreter:

```powershell
D:\AI_Career_Path_Predictor_UI_Phase1\AI_Career_Path_Predictor_UI\.venv\Scripts\python.exe -m unittest discover -s tests -q
```

Result: **46 tests run, 46 passed, 0 failed, 0 skipped; exit code 0.** Streamlit emitted its `missing ScriptRunContext` bare-mode warning.

## Limitations to disclose

- The recommendation system is a deterministic prototype, not a trained ML model.
- Scores are heuristic relevance indicators, not calibrated probabilities or career-fit guarantees.
- The catalog and roadmaps are illustrative examples, not live job-market data, verified employer requirements, or validated learning plans.
- Authentication is demo-only and not production-ready. Registration accounts and salted PBKDF2-HMAC-SHA256 password hashes are held in session state; there is no persistent account database or production authentication system.
- Profile/assessment data and saved careers are session-only. Logout clears profile details and preserves saved careers in the current session; no persistence across session reset is guaranteed.
- Accuracy, salary, placement, and employment metrics are not specified.
