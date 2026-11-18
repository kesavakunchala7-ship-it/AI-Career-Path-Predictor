"""Curated career metadata used by the deterministic recommendation prototype."""

from collections.abc import Iterable, Mapping

CAREERS = [
    {
        "id": "data-scientist",
        "title": "Data Scientist",
        "icon": "📊",
        "desc": "Analyze data to find insights and help in decision making using AI/ML.",
        "skills": ["Python", "Machine Learning", "Statistics", "SQL", "Data Analysis"],
        "interests": ["Data Science", "Artificial Intelligence"],
        "gap": ["Deep Learning", "Data Visualization"],
        "roadmap": [
            "Review Python fundamentals, statistics, and working with structured data.",
            "Practice data cleaning, exploratory analysis, and introductory machine learning.",
            "Complete an example project that analyzes a dataset and explains its findings.",
            "Document methods, limitations, and results in a clear portfolio example.",
        ],
    },
    {
        "id": "ai-ml-engineer",
        "title": "AI/ML Engineer",
        "icon": "🧠",
        "desc": "Build intelligent systems using machine learning and deep learning.",
        "skills": ["Python", "Machine Learning", "Statistics", "Git"],
        "interests": ["Artificial Intelligence", "Research & Innovation"],
        "gap": ["Deep Learning", "Model Deployment", "Linear Algebra"],
        "roadmap": [
            "Review Python programming, linear algebra, and probability fundamentals.",
            "Practice model training, evaluation, version control, and deployment concepts.",
            "Build an illustrative machine-learning application and evaluate its behavior.",
            "Document experiments, evaluation limits, and reproducible project steps.",
        ],
    },
    {
        "id": "full-stack-developer",
        "title": "Full Stack Developer",
        "icon": "💻",
        "desc": "Develop complete web applications using frontend and backend technologies.",
        "skills": ["JavaScript", "HTML/CSS", "SQL", "React", "Git"],
        "interests": ["Web Development"],
        "gap": ["Backend APIs", "Deployment"],
        "roadmap": [
            "Review HTML, CSS, JavaScript, and browser fundamentals.",
            "Practice component-based interfaces, data handling, and API integration.",
            "Build an illustrative web application with a connected frontend and backend.",
            "Document the application structure, tests, and deployment considerations.",
        ],
    },
    {
        "id": "data-analyst",
        "title": "Data Analyst",
        "icon": "📈",
        "desc": "Work with data to create reports and visualizations that support business decisions.",
        "skills": ["SQL", "Python", "Data Analysis", "Statistics"],
        "interests": ["Data Science", "Business & Management"],
        "gap": ["Power BI", "Advanced Excel", "Data Storytelling"],
        "roadmap": [
            "Review spreadsheet, SQL, and basic statistics fundamentals.",
            "Practice data cleaning, querying, visualization, and communicating findings.",
            "Complete an illustrative analysis that answers a clearly stated question.",
            "Document assumptions, analysis steps, and findings in a portfolio example.",
        ],
    },
    {
        "id": "java-backend-developer",
        "title": "Java Backend Developer",
        "icon": "☕",
        "desc": "Build server-side applications and APIs with Java and backend frameworks.",
        "skills": ["Java", "SQL", "REST APIs", "Spring Boot", "Git"],
        "interests": ["Backend Development", "Software Development"],
        "gap": ["Microservices", "API Security"],
        "roadmap": [
            "Review Java fundamentals and object-oriented programming.",
            "Practice SQL, REST API design, and building services with Spring Boot.",
            "Build an illustrative Java backend service with persistence and API tests.",
            "Document the service design, test coverage, and security considerations.",
        ],
    },
    {
        "id": "python-developer",
        "title": "Python Developer",
        "icon": "🐍",
        "desc": "Develop Python applications, services, and data-driven tools.",
        "skills": ["Python", "Git", "REST APIs", "SQL"],
        "interests": ["Python Development", "Software Development"],
        "gap": ["Unit Testing", "Application Packaging"],
        "roadmap": [
            "Review Python syntax, data structures, and object-oriented programming.",
            "Practice packaging, SQL access, API development, and unit testing.",
            "Build an illustrative Python application or service with automated tests.",
            "Document setup, design choices, test coverage, and packaging steps.",
        ],
    },
    {
        "id": "cloud-devops-engineer",
        "title": "Cloud/DevOps Engineer",
        "icon": "☁️",
        "desc": "Automate software delivery and operate reliable cloud infrastructure.",
        "skills": ["Cloud Computing", "Linux", "Docker", "Git"],
        "interests": ["Cloud & DevOps"],
        "gap": ["CI/CD", "Infrastructure as Code"],
        "roadmap": [
            "Review Linux command-line, networking, and cloud-computing fundamentals.",
            "Practice containers, CI/CD concepts, and infrastructure automation.",
            "Create an illustrative deployment workflow for a sample application.",
            "Document operational assumptions, monitoring needs, and recovery steps.",
        ],
    },
    {
        "id": "cybersecurity-analyst",
        "title": "Cybersecurity Analyst",
        "icon": "🛡️",
        "desc": "Monitor systems for security risks and help investigate potential incidents.",
        "skills": ["Networking", "Linux", "Cyber Security", "Security Fundamentals"],
        "interests": ["Cyber Security"],
        "gap": ["Incident Response", "Threat Analysis"],
        "roadmap": [
            "Review networking, Linux, and core security concepts.",
            "Practice log review, threat identification, and incident-response procedures.",
            "Work through an illustrative defensive analysis using authorized sample data.",
            "Document observations, escalation steps, and defensive recommendations.",
        ],
    },
    {
        "id": "software-tester-qa-engineer",
        "title": "Software Tester/QA Engineer",
        "icon": "🧪",
        "desc": "Validate software behavior with structured testing and test automation.",
        "skills": ["Software Testing", "Test Automation", "Java", "Git"],
        "interests": ["Software Quality Assurance", "Software Development"],
        "gap": ["API Testing", "CI/CD"],
        "roadmap": [
            "Review software testing principles, test cases, and defect reporting.",
            "Practice Java-based automation, API testing, and continuous-integration concepts.",
            "Create an illustrative automated test suite for a sample application.",
            "Document test coverage, reproducibility, and defect triage decisions.",
        ],
    },
    {
        "id": "mobile-app-developer",
        "title": "Mobile App Developer",
        "icon": "📱",
        "desc": "Develop and maintain mobile applications for Android and related platforms.",
        "skills": ["Java", "Kotlin", "Android Development", "Git"],
        "interests": ["Mobile App Development"],
        "gap": ["Mobile UI Design", "App Deployment"],
        "roadmap": [
            "Review Java or Kotlin fundamentals and mobile application concepts.",
            "Practice Android UI, application lifecycle, and local data handling.",
            "Build an illustrative Android application and test common user flows.",
            "Document accessibility, testing, and app-release considerations.",
        ],
    },
]

EDUCATION_OPTIONS = (
    "Intermediate",
    "Diploma",
    "B.Tech",
    "B.Sc",
    "BCA",
    "MCA",
    "M.Tech",
    "Other",
)

FIELD_OPTIONS = (
    "Computer Science",
    "Information Technology",
    "Electronics",
    "Mechanical",
    "Commerce",
    "Arts & Humanities",
    "Other",
)

EXPERIENCE_OPTIONS = (
    "Beginner",
    "Academic projects",
    "Internship experience",
    "Working professional",
)


ASSESSMENT_SKILL_BASE_OPTIONS = (
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
)

ASSESSMENT_INTEREST_BASE_OPTIONS = (
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
)


def _option_key(value: str) -> str:
    return " ".join(value.split()).casefold()


def _unique_options(values: Iterable[object]) -> list[str]:
    options: dict[str, str] = {}
    for value in values:
        if isinstance(value, str) and value.strip():
            options.setdefault(_option_key(value), value)
    return list(options.values())


def _career_tag_keys(
    careers: Iterable[Mapping[str, object]],
    tag_name: str,
) -> set[str]:
    keys: set[str] = set()
    for career in careers:
        tags = career.get(tag_name, ())
        if isinstance(tags, (list, tuple)):
            keys.update(
                _option_key(tag)
                for tag in tags
                if isinstance(tag, str) and tag.strip()
            )
    return keys


def assessment_skill_options(
    careers: Iterable[Mapping[str, object]] = CAREERS,
) -> list[str]:
    """Return existing assessment skills plus every career-required skill."""
    career_list = list(careers)
    catalog_options = (
        skill
        for career in career_list
        for skill in career.get("skills", ())
        if isinstance(skill, str)
    )
    return _unique_options((*ASSESSMENT_SKILL_BASE_OPTIONS, *catalog_options))


def assessment_interest_options(
    careers: Iterable[Mapping[str, object]] = CAREERS,
) -> list[str]:
    """Return the existing assessment interests plus every catalog interest."""
    career_list = list(careers)
    catalog_options = (
        interest
        for career in career_list
        for interest in career.get("interests", [])
        if isinstance(interest, str)
    )
    return _unique_options((*ASSESSMENT_INTEREST_BASE_OPTIONS, *catalog_options))


def unmatched_assessment_skill_options(
    careers: Iterable[Mapping[str, object]] = CAREERS,
) -> list[str]:
    """Return selectable skills without an exact normalized career skill tag."""
    career_list = list(careers)
    tag_keys = _career_tag_keys(career_list, "skills")
    return [
        option for option in assessment_skill_options(career_list)
        if _option_key(option) not in tag_keys
    ]


def unmatched_assessment_interest_options(
    careers: Iterable[Mapping[str, object]] = CAREERS,
) -> list[str]:
    """Return selectable interests without an exact normalized career tag."""
    career_list = list(careers)
    tag_keys = _career_tag_keys(career_list, "interests")
    return [
        option for option in assessment_interest_options(career_list)
        if _option_key(option) not in tag_keys
    ]


def normalize_saved_career_ids(
    saved_values: Iterable[object],
    careers: Iterable[Mapping[str, object]] = CAREERS,
) -> list[str]:
    """Convert saved career IDs and legacy titles to unique stable IDs."""
    if isinstance(saved_values, str):
        saved_values = (saved_values,)

    career_list = list(careers)
    career_by_id: dict[str, str] = {}
    career_by_title: dict[str, str] = {}
    for career in career_list:
        raw_id = career.get("id")
        raw_title = career.get("title")
        if not isinstance(raw_id, str) or not raw_id.strip():
            continue
        career_id = raw_id.strip()
        career_by_id[career_id.casefold()] = career_id
        if isinstance(raw_title, str) and raw_title.strip():
            career_by_title[" ".join(raw_title.split()).casefold()] = career_id

    normalized: list[str] = []
    for value in saved_values:
        if not isinstance(value, str):
            continue
        key = " ".join(value.split()).casefold()
        career_id = career_by_id.get(key) or career_by_title.get(key)
        if career_id and career_id not in normalized:
            normalized.append(career_id)
    return normalized


def toggle_saved_career_id(
    saved_values: Iterable[object],
    career_id: str,
    careers: Iterable[Mapping[str, object]] = CAREERS,
) -> list[str]:
    """Toggle a career by stable ID while migrating any legacy title values."""
    career_list = list(careers)
    known_ids = set()
    for career in career_list:
        raw_id = career.get("id")
        if isinstance(raw_id, str) and raw_id.strip():
            known_ids.add(raw_id.strip())
    if career_id not in known_ids:
        raise ValueError(f"Unknown career ID: {career_id}")

    saved_ids = normalize_saved_career_ids(saved_values, career_list)
    if career_id in saved_ids:
        saved_ids.remove(career_id)
    else:
        saved_ids.append(career_id)
    return saved_ids
