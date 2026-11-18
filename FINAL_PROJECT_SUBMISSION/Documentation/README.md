# AI Career Path Predictor

## Project overview

AI Career Path Predictor is a student-focused Streamlit prototype for exploring a curated set of career examples. Students can confirm skills and interests, compare those selections with career tags, view heuristic relevance scores, save careers during the current app session, and explore illustrative roadmaps.

This project is a decision-support and career-exploration demo. It does not predict a student's future or guarantee that a role is a good fit.

## Problem statement

Students exploring technology careers may want a simple way to compare their interests and skills with example roles. This prototype demonstrates one transparent, rule-based way to make that comparison.

## Proposed solution

The app collects profile details and confirmed skills and interests, then compares those tags with the requirements and interest tags in a small curated career catalog. It displays the comparison and an illustrative learning roadmap for each role.

## Features

- Demo-only registration and sign-in; users must register before login, and login checks the registered email and password.
- Registered accounts are stored in the current Streamlit session with salted PBKDF2 password hashes; duplicate email registration is rejected.
- Logging out clears the current session's profile and returns to the public Home page; saved careers remain in the browser session.
- Career assessment for profile details, skills, and interests.
- Assessment options include all career skill and interest tags. Some profile-only choices currently have no matching career tag; the assessment identifies these, and they do not contribute to relevance matches.
- Assessment confirmation is required before the Results page ranks careers.
- Career recommendations show a heuristic score, matched skills and interests, skills to explore, and an explanation.
- A career catalog can be browsed without personalized ranking when there is no strong match.
- Career details include example skills, a skill comparison, four roadmap phases, and a note that roadmaps are illustrative.
- Saved careers are kept only for the current browser session.
- Dashboard, profile, saved-career, roadmap, and About pages.

## Technologies used

- **Python** and **Streamlit** power the application.
- `requirements.txt` declares **Streamlit**, **Pandas**, and **scikit-learn** dependencies. The current career scoring is implemented as a deterministic Python heuristic; it does not use a trained scikit-learn model.
- The About page lists Gemini as planned/optional technology. A Gemini API or other language model is not connected to recommendation scoring.

## Project structure

```text
AI_Career_Path_Predictor_UI/
|-- app.py                         # Streamlit application and page flows
|-- auth_utils.py                  # Session account validation and password hashing
|-- career_data.py                 # Curated career catalog and assessment options
|-- recommendation_engine.py       # Tag matching, scoring, ranking, explanations
|-- requirements.txt               # Declared Python package dependencies
|-- README.md                      # Project and setup guide
|-- assets/
|   `-- career-student.svg          # Home-page illustration
|-- tests/
|   |-- test_recommendation_engine.py # Recommendation and catalog regression tests
|   `-- test_auth_navigation.py    # Authentication, session cleanup, and navigation regression tests
`-- .streamlit/
    `-- config.toml                # Streamlit theme configuration
```

## System requirements

- Windows 11, following the setup commands below.
- Python 3.10 or newer. The Phase 1.21 clean-environment verification used Python 3.12.10; other Python versions were not part of that clean setup check.
- Internet access may be needed when installing packages. The app also references an online font in its page styling; if it is unavailable, the browser may use a fallback font.

## Installation and setup (Windows)

1. Extract the project archive if you are starting from the ZIP.
2. Open the `AI_Career_Path_Predictor_UI` project folder in VS Code.
3. Open a PowerShell terminal in that folder.
4. Check Python and create and activate a virtual environment. The commands below use Python 3.12, which was used for the clean setup verification:

   ```powershell
   py -3.12 --version
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   The project documentation requires Python 3.10 or newer. If you use another installed Python 3.10+ version, replace `3.12` in the `py` commands with that version.

   If PowerShell blocks script activation, use Command Prompt and run:

   ```bat
   .venv\Scripts\activate.bat
   ```

5. Install the packages declared by the project and verify dependency consistency:

   ```powershell
   python -m pip install -r requirements.txt
   python -m pip check
   ```

These instructions describe setting up a fresh project environment. Phase 1.21 installation, launch, and tests used a separate temporary environment; the existing `.venv` was inspected but not modified.

## Run the application

For a one-step Windows launch, double-click `run.bat` in the project folder. It creates a local `.venv` if needed, installs/checks the dependencies, and starts the app.

Alternatively, from the project folder with the virtual environment active, run:

```powershell
streamlit run app.py
```

Streamlit normally opens the app in your browser. If it does not, open:

```text
http://localhost:8501
```

To stop the local server, focus its terminal and press `Ctrl+C`.

## How to use the application

1. Open the Home page and review the project description. Select **Get Started** to register a demo account, or enter the email and password for an account already registered in this browser session. Login does not create accounts.
2. After demo sign-up, the app opens **Career Assessment**. From other pages, use the sidebar to navigate there.
3. Enter the requested profile details and choose the skills you have reviewed and confirm.
4. Choose career interests. The notes below the selectors identify profile-only options that do not currently match career tags.
5. Check the confirmation box and submit the assessment. A skill, an interest, and confirmation are required to continue.
6. On **Career Recommendations**, review each role's score, matched skills and interests, skills to explore, and score explanation.
7. If the app reports no strong match, select **Review Assessment** to revise your inputs or **Explore Career Catalog** to browse the example roles without a personalized ranking.
8. On a ranked recommendation, use **Save Career** to add a role to **Saved Careers**. Remove it from the recommendation or saved-career page when you no longer want it saved. Saved careers last only for the current browser session.
9. Select **View Details** or **View Learning Roadmap** where available to open a role's overview and roadmap. Use **Back to Results** to return to the Results page. Use **Edit Assessment** on My Profile or the sidebar to revisit the assessment.

## Authentication limitations

Registration requires a full name, a valid email, a non-empty password, and matching password confirmation. Duplicate emails are rejected without regard to case. Login succeeds only when the registered email and password match; missing or invalid inputs and unknown or incorrect credentials are rejected, and failed login does not create an account. Passwords are stored as salted PBKDF2-HMAC-SHA256 hashes in Streamlit session state, not as plaintext; hashes are not displayed. The account registry is session-only and is lost when that session ends. This is demo authentication only: there is no persistent account database or production-ready authentication system.

## Recommendation scoring

Students must submit confirmed skills and interests before the Results page ranks careers. Preselected profile values alone are not treated as confirmed assessment inputs.

For each career:

- **Skill relevance** is the fraction of that career's distinct required skill tags that match confirmed skills.
- **Interest relevance** is the fraction of that career's distinct interest tags that match confirmed interests.
- The total heuristic score is:

  ```text
  100 × (0.70 × skill relevance + 0.30 × interest relevance)
  ```

The score is a rule-based relevance indicator, not a calibrated probability, model accuracy, or guarantee of career fit. The application does not currently use a trained machine-learning model for career prediction.

Matching ignores capitalization and normalizes whitespace, but it otherwise compares labels directly. The engine does not automatically infer synonyms or equivalent phrases. Inputs without matching tags do not contribute to matches. Profile-only options may therefore result in no strong match if none of the confirmed tags match a career. If required inputs or career metadata are missing, a combined score may be unavailable. Ties are ordered deterministically by career identifier.

## Career roadmaps

Each of the ten curated career examples has four roadmap phases: foundations, core skills, applied projects, and portfolio/applications. The current phase descriptions are illustrative examples, not verified learning plans.

The displayed month ranges are approximate planning examples only. They are not guaranteed completion times, personalized schedules, employer-required timelines, or validated industry estimates. The app does not provide courses or curated external learning resources.

## Testing

Run the existing test suite from the project folder with the virtual environment activated:

```powershell
python -m unittest discover -s tests -q
```

The full verbose form is:

```powershell
python -m unittest discover -s tests -v
```

The tests cover recommendation scoring and matching, catalog and assessment-option consistency, roadmap structure, and saved-career ID behavior. The number of tests can change as the suite evolves; a successful run is not guaranteed by this guide.

## Phase 1.19 verification record

The Phase 1.19 project-root test run reported **46 tests passed, 0 failed**. This was not a fresh-environment setup or a test run from the submission copy.

Browser verification used synthetic test credentials and observed:

- Assessment submission with confirmed Python, Machine Learning, and SQL skills and Data Science and Artificial Intelligence interests.
- Data Scientist ranked first at **72.0/100**, with 3 of 5 required skills and 2 of 2 interest tags matched; matched tags and skills to explore were displayed.
- Profile-only Communication and Gaming inputs produced the no-strong-match warning, with no personalized career cards.
- The Data Scientist roadmap displayed four phases, the confirmed skills, and skills to explore; its content was labeled illustrative.
- A career could be saved, displayed in Saved Careers, removed, and then absent from the saved list.
- Valid registered credentials logged in; wrong and unregistered credentials were rejected. About/Home navigation and logout profile cleanup were observed.
- The captured browser console and page-error collections were empty during the final instrumented pass.

This was focused scenario testing, not exhaustive browser coverage. Direct browser testing of protected-page redirection, every assessment/recommendation combination, session reset, and all role roadmaps was not performed in Phase 1.19. The protected-page redirect is covered by an automated test; session reset was reported as browser-tested in Phase 1.18.

## Phase 1.21 clean-environment verification record

On 2026-10-23, setup was verified in a separate temporary Python 3.12.10 virtual environment on Windows. Installing `requirements.txt` completed successfully; `python -m pip check` reported no broken requirements. The resolved versions were Streamlit 1.66.1, Pandas 3.1.0, and scikit-learn 1.9.1; these are the versions observed in that run, not pinned project versions. The activated environment ran `python -m unittest discover -s tests -q` from both the main project root and `FINAL_PROJECT_SUBMISSION/Source_Code`, with **46 tests passed, 0 failed, 0 skipped** in each run. Streamlit started from `app.py` and returned HTTP 200 locally. Browser verification confirmed the Home page and its student SVG loaded, with no browser console or page errors. The temporary environment was removed after verification; the existing project `.venv` was not used.

## Limitations

- The career catalog and tags are curated, static examples, not live job-market data or verified employer requirements.
- Career ranking uses a deterministic 70/30 skill-and-interest heuristic, not a trained ML model. It does not understand synonyms and its scores are not calibrated probabilities.
- Recommendations are exploratory examples, not career outcomes or fit guarantees.
- Roadmaps and their displayed durations are illustrative and have not been validated as learning plans or industry timelines.
- Authentication is demo-only. The account registry and salted PBKDF2-HMAC-SHA256 password hashes are session-only; there is no persistent account database or production authentication system.
- Assessment data and saved careers are held for the current browser session and are not persistent across session resets.
- Gemini/LLM assistance is not connected to the current recommendation scoring.
- Courses and external learning resources are not curated by the app.

## Future improvements (not implemented)

Possible future work, subject to project decisions, could include reviewing the catalog and tag coverage, providing current learning resources, evaluating the heuristic with students, or designing persistent accounts and storage. These are ideas only and are not current application features.

## Design

The prototype uses a light background, purple/blue accents, rounded cards, a sidebar, and responsive layouts. Browser rendering can vary with viewport, installed fonts, and Streamlit version.
