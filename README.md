# AI Career Path Predictor

## Project overview

AI Career Path Predictor is a student-focused Streamlit prototype for exploring a curated set of career examples. Students can confirm skills and interests, compare those selections with career tags, view heuristic relevance scores, save careers to their local account data, and explore illustrative roadmaps.

This project is a decision-support and career-exploration demo. It does not predict a student's future or guarantee that a role is a good fit.

## Problem statement

Students exploring technology careers may want a simple way to compare their interests and skills with example roles. This prototype demonstrates one transparent, rule-based way to make that comparison.

## Proposed solution

The app collects profile details and confirmed skills and interests, then compares those tags with the requirements and interest tags in a small curated career catalog. It displays the comparison and an illustrative learning roadmap for each role.

## Features

- Google sign-in uses Streamlit's native OpenID Connect authentication.
- Authentication state is derived from Streamlit's verified `st.user` identity and can be restored from its signed identity cookie across browser reloads and new Streamlit sessions.
- Google manages account creation and passwords; the app does not collect or store Google passwords.
- Career assessment for profile details, skills, and interests, saved to local SQLite storage for the authenticated account.
- Assessment options include all career skill and interest tags. Some profile-only choices currently have no matching career tag; the assessment identifies these, and they do not contribute to relevance matches.
- Assessment confirmation is required before the Results page ranks careers.
- Career recommendations show a heuristic score, matched skills and interests, skills to explore, and an explanation.
- A local Ollama explanation is available on request for a scored career with a meaningful match. It supplements the deterministic explanation and cannot change scores or ranking; Gemini service code is retained but is not called by this UI action.
- A career catalog can be browsed without personalized ranking when there is no strong match.
- Browse & Compare Careers provides catalog search by title, description, skills, interests, and roadmap text; filters by catalog skills/interests; per-session career comparison; saved-career controls; and direct roadmap access.
- Career details include example skills, a skill comparison, four illustrative roadmap phases, phase completion controls, and a note that roadmaps are not validated learning plans.
- Each of the 10 supported careers has one career-specific curated learning resource, displayed in its associated roadmap phase with its title, provider, resource type, difficulty, relevance, and verification date.
- Roadmap phase completion shows totals, remaining work, a completion percentage, and a progress bar; progress is saved separately per career for the authenticated account.
- Saved careers are stored for the authenticated account.
- Comparison selection and generated career explanations remain session-only.
- The profile page provides a confirmation step to delete the authenticated user's saved profile, saved careers, and roadmap progress.
- Dashboard, assessment, results, career browsing/comparison, profile, saved-career, roadmap, and About pages.

## Technologies used

- **Python** and **Streamlit** power the application.
- `requirements.txt` declares **Streamlit**, **Pandas**, **scikit-learn**, and Google's **google-genai** SDK. Ollama requests use Python's standard library and add no package dependency.
- Career ranking and scores use the deterministic 70/30 heuristic; the local Ollama provider only generates supplementary explanations when requested.

## Project structure

```text
AI_Career_Path_Predictor_UI/
|-- app.py                         # Streamlit application and page flows
|-- auth_utils.py                  # OIDC identity claim helpers and legacy password helpers
|-- user_data_store.py             # Versioned SQLite persistence for authenticated user data
|-- career_data.py                 # Curated career catalog and assessment options
|-- career_exploration.py          # Catalog search, filters, and comparison selection helpers
|-- learning_resources.py          # Typed, validated curated learning-resource catalog
|-- roadmap_progress.py            # Roadmap phase and progress helpers
|-- main_logic.py                  # Main career input processing, matching, scoring, ranking
|-- recommendation_engine.py       # Backward-compatible exports for the recommendation logic
|-- ollama_explanation_service.py  # Local Qwen explanations and deterministic fallback
|-- gemini_service.py              # Retained Gemini service and diagnostics
|-- requirements.txt               # Declared Python package dependencies
|-- run.bat                        # Windows launcher; installs/checks dependencies before launch
|-- .gitignore                     # Excludes local SQLite data and Streamlit secrets
|-- README.md                      # Project and setup guide
|-- assets/
|   `-- career-student.svg          # Home-page illustration
|-- tests/
|   |-- test_recommendation_engine.py # Recommendation and catalog regression tests
|   |-- test_gemini_service.py      # Mocked Gemini service and UI behavior tests
|   |-- test_ollama_explanation_service.py # Mocked local Ollama and fallback tests
|   |-- test_auth_navigation.py    # Authentication, identity, and navigation regression tests
|   |-- test_user_data_store.py    # SQLite ownership and persistence regression tests
|   |-- test_roadmap_progress.py   # Roadmap progress regression tests
|   |-- test_career_browse_compare.py # Catalog browsing and comparison regression tests
|   `-- test_learning_resources.py # Resource validation and rendering regression tests
`-- .streamlit/
    |-- config.toml                # Streamlit theme configuration
    `-- secrets.toml               # Google OIDC and retained Gemini config; never commit
|-- .local_data/                   # Generated local SQLite user data; excluded from Git
```

`FINAL_PROJECT_SUBMISSION/` is a separate, existing handover snapshot. Check that its source and documentation match the current project before relying on it as the final submission; see the current source tree above.

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

These instructions describe setting up a fresh project environment. They install the dependencies declared in `requirements.txt`; do not run the install command when you need a no-install review of an existing environment.

## Run the application

For a one-step Windows launch, double-click `run.bat` in the project folder. It creates a local `.venv` if needed, runs `pip install -r requirements.txt` (which may install or update packages), and starts the app. To use an already-prepared environment without installing packages, run the direct command below instead.

Alternatively, from the project folder, explicitly run Streamlit through the project virtual environment:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8502
```

Streamlit normally opens the app in your browser. If it does not, open:

```text
http://localhost:8502
```

To stop the local server, focus its terminal and press `Ctrl+C`.

## Local AI career explanations

Ollama must be installed on Windows, and the `qwen2.5:1.5b-instruct` model must already be available locally in Ollama. The app does not install Ollama or download models. Before launching Streamlit, start the Ollama desktop app, or run `ollama serve` in a separate terminal if the Ollama service is not already running; leave that service running while using the app.

The deterministic recommendation engine remains the only source of career rankings and scores. When **Generate AI Career Explanation** is selected on a scored recommendation with a meaningful match, the app sends only the career name, matched skills, missing skills, matched interests, and deterministic score to the local Ollama API. The default model is `qwen2.5:1.5b-instruct`; it must already be available to Ollama. Successful responses are labeled as locally AI-generated. Model suggestions can be inaccurate and cannot add verified career facts, change recommendation scores, or reorder careers.

Ollama must be running on the local machine. By default, the app calls `http://localhost:11434/api/generate` with a 60-second timeout. To use a different Ollama host, set the non-secret `OLLAMA_HOST` environment variable before starting Streamlit, for example:

```powershell
$env:OLLAMA_HOST = "http://localhost:11434"
.\.venv\Scripts\python.exe -m streamlit run app.py
```

If Ollama is unavailable, times out, or returns an invalid response, the UI displays a rule-based explanation using the same recommendation fields. It is explicitly labeled as not AI-generated. No Gemini API key or billing is required for the active explanation button.

The separate `gemini_service.py` integration and its diagnostics remain in the project for compatibility and testing, but the current recommendation UI does not call Gemini. Its Google SDK dependency remains in `requirements.txt`.

## User data persistence and privacy

Authenticated assessment data is stored in `.local_data/career_predictor.sqlite3`, created automatically on first use. This is a local, project-specific SQLite database; no package installation or database setup is required. Keep the project directory on durable storage and do not share or commit `.local_data/`.

The database stores the OIDC issuer and subject as the account ownership key and persists the assessment name, age, education, field of study, experience, selected and confirmed skills/interests, saved career IDs, and completed roadmap phases. Email, display name as an ownership key, OAuth tokens, Gemini credentials, comparison selections, and generated explanation results are not persisted. SQLite foreign-key cascades scope deletion to the selected account.

To remove an account's stored assessment and career-progress data, sign in, open **My Profile**, check the deletion confirmation, and select **Delete my saved data**. Logout alone does not delete stored information. This local database is not a managed, encrypted, multi-instance service; protect the project directory and any backups, and use an appropriate durable database service if deploying multiple or ephemeral app instances.

For local development, launch the app using the existing Windows instructions above. The database directory is created by the application when an authenticated user's data is accessed. To run persistence tests without touching local user data, run the project's test suite; tests use temporary SQLite files.

Keep secrets private and do not commit the secrets file. The active Ollama explanation flow does not use an API key. On failure, it writes only a sanitized category such as `timeout`, `unavailable`, or `invalid_response` to the terminal running Streamlit; it does not log prompts or recommendation details. Its service uses a bounded timeout and falls back to a rule-based explanation on local-provider failure. AI guidance is not verified career advice, a professional assessment, or a guarantee of outcomes. Automated Ollama tests use mocked responses.

### Retained Gemini request diagnostics

The separate Gemini service writes a sanitized completion log per request attempt to the terminal running Streamlit when invoked. It includes UTC start and completion timestamps, duration in milliseconds, attempt number, configured model, outcome, sanitized error category, and HTTP status when available. A provider response/request ID is included only when the SDK response or exception supplies one in a recognized field/header. Logs do not include the prompt, assessment details, API key, or authorization headers.

For Gemini request comparison with Google AI Studio, record the UTC `started_at` time and final attempt status/outcome from the same terminal session. Compare that time and model with the dashboard's date range and model filter; usage data may be delayed, and aggregate counts cannot identify an individual request. Request IDs are not generated by the app. Do not share API keys, OAuth credentials, callback URLs, or unreviewed full logs; share only sanitized error category/status and a suitably redacted time if requesting help.

## How to use the application

1. Open the Home page and select **Continue with Google** to authenticate with the configured Google OIDC provider.
2. After sign-in, the app opens **Dashboard**. Use the sidebar to navigate to **Career Assessment**.
3. Enter the requested profile details and choose the skills you have reviewed and confirm.
4. Choose career interests. The notes below the selectors identify profile-only options that do not currently match career tags.
5. Check the confirmation box and submit the assessment. A skill, an interest, and confirmation are required to continue.
6. On **Career Recommendations**, review each role's score, matched skills and interests, skills to explore, and deterministic score explanation. For a scored role with a meaningful match, optionally select **Generate AI Career Explanation** to request separate supplementary suggestions. The request is not automatic.
7. If the app reports no strong match, select **Review Assessment** to revise your inputs or **Explore Career Catalog** to browse the example roles without a personalized ranking.
8. On a ranked recommendation, use **Save Career** to add a role to **Saved Careers**. Remove it from the recommendation or saved-career page when you no longer want it saved. Saved careers remain associated with the authenticated account across sessions.
9. Select **View Details** or **View Learning Roadmap** where available to open a role's overview and roadmap. Use **Back to Results** to return to the Results page. Use **Edit Assessment** on My Profile or the sidebar to revisit the assessment.

## Google authentication setup

Install dependencies from `requirements.txt` so Streamlit's `auth` extra is available. Configure the Google OAuth client in `.streamlit/secrets.toml` using Streamlit's `[auth]` settings (`redirect_uri`, `cookie_secret`, `client_id`, `client_secret`, and `server_metadata_url`). Keep that file private and out of version control; the repository `.gitignore` excludes it. Do not paste secret values into source files, documentation, screenshots, or issue reports. The Windows launcher uses port 8502 to match the configured local callback: register `http://localhost:8502` as an authorized origin and `http://localhost:8502/oauth2callback` as the redirect URI in Google Cloud. If you deliberately run the app on another port or hostname, configure the matching origin and redirect URI in both Google and Streamlit.

The app derives protected-page access from `st.user.is_logged_in`; a value in `st.session_state` alone cannot authenticate a user. User-data ownership uses the verified OIDC issuer and subject claims, not email or display name. Use **Logout** to clear Streamlit's identity cookie and end the provider session where supported. Google OIDC authentication persists across browser reloads and new Streamlit sessions. Assessment details, saved careers, and roadmap progress are stored in the local SQLite database described above.

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

The displayed month ranges are approximate planning examples only. They are not guaranteed completion times, personalized schedules, employer-required timelines, or validated industry estimates.

### Curated learning resources

`learning_resources.py` defines the typed resource records, validated catalog, career-specific matching, roadmap phase grouping, and rendering. The current catalog contains **10 career-specific learning resources for the 10 supported careers: one resource per career**. Users open a career's **Learning Roadmap** from a recommendation, catalog entry, or saved-career details; its resource is displayed under the associated roadmap phase.

Resource fields describe the **title**, **provider/source**, **resource type**, **difficulty**, **career association**, and **roadmap phase**. Entries also carry skill and/or skill-gap tags, a relevance note, and verification metadata: `verification_status`, `verification_date`, and an HTTPS `verification_source_url` supporting the manual check. The learner-facing HTTPS `url` is separate from the evidence URL; an optional `access_note` is only for conditions directly observed.

| Resource title (learner destination) | Provider/source | Type | Difficulty | Career | Roadmap phase | Verification |
|---|---|---|---|---|---|---|
| [The Python Tutorial](https://docs.python.org/3/tutorial/) | Python documentation (`docs.python.org`) | Documentation | Beginner | Python Developer | `phase-1` | Verified, 2026-10-24 |
| [scikit-learn User Guide](https://scikit-learn.org/stable/user_guide.html) | scikit-learn documentation (`scikit-learn.org`) | Documentation | Intermediate | Data Scientist | `phase-2` | Verified, 2026-10-24 |
| [Learn web development](https://developer.mozilla.org/en-US/docs/Learn_web_development) | MDN Web Docs (`developer.mozilla.org`) | Documentation | Beginner | Full Stack Developer | `phase-1` | Verified, 2026-10-24 |
| [Developing with Spring Boot](https://docs.spring.io/spring-boot/reference/using/index.html) | Spring Boot documentation (`docs.spring.io`) | Documentation | Intermediate | Java Backend Developer | `phase-2` | Verified, 2026-10-24 |
| [Learn the Basics](https://docs.pytorch.org/tutorials/beginner/basics/intro.html) | PyTorch documentation (`pytorch.org`) | Tutorial | Intermediate | AI/ML Engineer | `phase-2` | Verified, 2026-10-24 |
| [What kind of data does pandas handle?](https://pandas.pydata.org/docs/getting_started/intro_tutorials/01_table_oriented.html) | pandas documentation (`pandas.pydata.org`) | Tutorial | Beginner | Data Analyst | `phase-2` | Verified, 2026-10-24 |
| [Build and share a containerized application](https://docs.docker.com/get-started/tutorials/run-an-app/) | Docker documentation (`docs.docker.com`) | Tutorial | Beginner | Cloud/DevOps Engineer | `phase-2` | Verified, 2026-10-24 |
| [Incident Response Recommendations and Considerations for Cybersecurity Risk Management](https://csrc.nist.gov/pubs/sp/800/61/r3/final) | National Institute of Standards and Technology (NIST) | Reference | Advanced | Cybersecurity Analyst | `phase-2` | Verified, 2026-10-24 |
| [API testing](https://playwright.dev/docs/api-testing) | Playwright documentation (`playwright.dev`) | Documentation | Intermediate | Software Tester/QA Engineer | `phase-2` | Verified, 2026-10-24 |
| [Android Basics with Compose](https://developer.android.com/courses/android-basics-compose/course) | Android Developers (`developer.android.com`) | Course | Beginner | Mobile App Developer | `phase-1` | Verified, 2026-10-24 |

The four original entries were checked against their official documentation destinations on **2026-10-24**. The six added entries were also checked against their official publisher pages on **2026-10-24**; the checks confirmed the destination and the stated relevance at a page-content level. Each destination is recorded as its HTTPS verification evidence URL in the resource entry. These checks did not establish access conditions, pricing, sign-in requirements, or future availability. Accordingly, no access notes or free/paid claims are recorded.

In this project, **verified** means a maintainer checked the resource identity, provider/publisher, learner-facing destination, relevance, and evidence source, and recorded that check in the resource entry. It does not mean the application automatically verifies availability, guarantees future access, or endorses the resource. A verified entry requires a provider/source identity (`provider_source`), an HTTPS verification-evidence URL (`verification_source_url`), a non-empty relevance explanation (`relevance_note`), a canonical `YYYY-MM-DD` verification date that is not in the future, and one supported difficulty (`Beginner`, `Intermediate`, or `Advanced`). The learner-facing `url`, when present, must also be a valid HTTPS URL. A verification date by itself is not evidence. The existing `provider_source` field is retained for compatibility and represents the provider or publisher identity; `url` is the learner-facing destination.

Before adding or updating a verified entry, maintainers should:

1. Confirm the exact resource title and provider/publisher from a source that identifies them.
2. Open and check the learner-facing destination and record its HTTPS URL.
3. Record a separate HTTPS evidence URL supporting the resource identity and destination.
4. Explain the relevance and map the entry only to existing career IDs, skills, skill gaps, and roadmap phase IDs.
5. Record access conditions only when directly observed; do not infer that a resource is free, paid, available, accessible without sign-in, current, or endorsed.
6. Record the date of the manual check. Re-check resources when maintainers have reason to do so; no automatic review interval or expiry is defined.
7. Leave entries unverified or omit them if identity, evidence, destination, or relevance cannot be established.

The current status values are `verified` and `unverified`. Only valid `verified` entries can match careers or produce clickable learner-facing links. Unverified entries cannot match or produce clickable links. No separate unavailable/needs-review status or automatic expiry policy is implemented. Do not encode unsupported access claims in `access_note`.

Resources with explicit career or roadmap-phase associations are confined to those careers; shared skills or gaps do not make them appear under unrelated careers. Resources without explicit career/phase scope may be reused by matching existing career skill or skill-gap tags and are grouped as unassigned to a phase. Phase-associated resources are grouped under their existing career-specific roadmap phases. Only valid verified resources can match careers or render clickable learner-facing links; unverified entries do not match and do not expose clickable links. Resource definitions are static project data; roadmap completion is saved as user data, while resource definitions themselves are not user-persisted. AI-generated suggestions remain separate and are not curated or verified resources.

## Testing

Run the existing test suite from the project folder with the virtual environment activated:

```powershell
python -m unittest discover -s tests -q
```

The full verbose form is:

```powershell
python -m unittest discover -s tests -v
```

The suite uses Python's built-in `unittest` framework and Streamlit's `AppTest`; run it from the project directory with the project's Python environment. It covers authentication/navigation, career browsing and comparison, Gemini service behavior with mocked responses, Ollama service behavior with mocked HTTP responses, learning-resource validation and rendering, recommendation scoring, roadmap progress, and SQLite persistence. Test counts may change as the suite evolves.

### Earlier verification records

The records below document earlier project checks and are not a report of the current test total or current browser verification.

On 2026-10-23, setup was verified in a separate temporary Python 3.12.10 virtual environment on Windows. Installing `requirements.txt` completed successfully; `python -m pip check` reported no broken requirements. The resolved versions were Streamlit 1.66.1, Pandas 3.1.0, and scikit-learn 1.9.1; these are the versions observed in that run, not pinned project versions. The activated environment ran the test command above with **46 tests passed, 0 failed, 0 skipped**. Streamlit started from `app.py` and returned HTTP 200 locally. Browser verification confirmed the Home page and its student SVG loaded, with no browser console or page errors. The existing project `.venv` was not used.

Phase 1.24.1 verification used the existing project `.venv` with Python 3.12.10. `google-genai` 2.33.0 was installed; its import succeeded and `pip check` reported no broken requirements. The full suite reported **60 tests passed, 0 failed**. Streamlit started and the local homepage returned HTTP 200. Effective configuration inspection found no API key in the process environment or Streamlit secrets, so no live Gemini request was made; live API verification remains pending until the user configures a key locally. The official model page listed the default model as stable when checked on 2026-10-23. These checks did not include a live Gemini response or browser-based review.

## Limitations

- The career catalog and tags are curated, static examples, not live job-market data or verified employer requirements.
- Career ranking uses a deterministic 70/30 skill-and-interest heuristic, not a trained ML model. It does not understand synonyms and its scores are not calibrated probabilities.
- Recommendations are exploratory examples, not career outcomes or fit guarantees.
- Roadmaps and their displayed durations are illustrative and have not been validated as learning plans or industry timelines.
- Google authentication requires a configured OIDC client and Streamlit's `auth` extra; no local password or authentication-account database is used.
- Assessment data, saved careers, and roadmap progress persist in the local SQLite database for the authenticated OIDC issuer/subject. Comparison selections and career-explanation results remain session-only.
- The active explanation provider is local Ollama using `qwen2.5:1.5b-instruct`; the model must be present and the Ollama service running. On failure, a rule-based explanation is shown. These explanations do not affect deterministic scoring and may be incomplete or incorrect.
- Earlier Gemini API retests returned HTTP 504 `DEADLINE_EXCEEDED`, HTTP 503 `UNAVAILABLE`, and HTTP 404 `NOT_FOUND` for an alternate model. Gemini provider access and those historical provider-side causes remain unverified. The current UI explanation action uses Ollama, not Gemini.
- The curated resource catalog contains ten manually checked resources, currently one per career; it is not a complete curriculum, and destinations and access conditions may change and are not automatically re-verified.

## Future improvements (not implemented)

Possible future work, subject to project decisions, could include reviewing the catalog and tag coverage, providing current learning resources, evaluating the heuristic with students, or replacing local SQLite with a managed durable database for multi-instance deployment. These are ideas only and are not current application features.

## Design

The prototype uses a light background, purple/blue accents, rounded cards, a sidebar, and responsive layouts. Browser rendering can vary with viewport, installed fonts, and Streamlit version.
