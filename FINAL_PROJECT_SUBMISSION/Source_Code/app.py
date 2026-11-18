import base64
from pathlib import Path

import streamlit as st

from auth_utils import authenticate_account, is_valid_email, register_account
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

st.set_page_config(page_title="AI Career Path Predictor", page_icon="🎓", layout="wide", initial_sidebar_state="collapsed")

# ---------- Theme / CSS ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root {
    --ink: #171b32;
    --muted: #65708a;
    --line: #e4e8f4;
    --purple: #5b3cf4;
    --blue: #3977ef;
    --surface: #ffffff;
}
html, body, [class*="css"] { font-family: Inter, sans-serif; }
.stApp { background: #f6f7fc; color: var(--ink); }
[data-testid="stHeader"], [data-testid="stToolbar"] { display:none; }
[data-testid="stMainBlockContainer"] { max-width: 1400px; padding: 1.6rem 2rem 3rem; }
[data-testid="stApp"]:has([data-testid="stSidebar"][data-collapsed="true"]) [data-testid="stHeader"],
[data-testid="stApp"]:has([data-testid="stSidebar"][data-collapsed="true"]) [data-testid="stToolbar"] { display:flex; }
[data-testid="stApp"]:has([data-testid="stSidebar"][data-collapsed="true"]) [data-testid="stMainBlockContainer"] { padding-top:4.5rem; }
[data-testid="stAppDeployButton"], [data-testid="stMainMenu"] { display:none; }
[data-testid="stSidebar"] { background: linear-gradient(180deg,#eef1ff 0%,#f8f9ff 100%); border-right: 1px solid #e3e7f4; }
[data-testid="stSidebar"] > div { padding: 1.35rem 1rem 1.5rem; }
[data-testid="stSidebar"] [data-testid="stButton"] button { text-align: left; }
.st-key-public-navigation { padding:.15rem 0 1rem; border-bottom:1px solid var(--line); margin-bottom:1.15rem; }
.st-key-public-navigation [data-testid="stHorizontalBlock"] { flex-wrap:nowrap; align-items:center; gap:.65rem; }
.st-key-public-navigation [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child { flex:1 1 auto !important; min-width:0; }
.st-key-public-navigation [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:not(:first-child) { flex:0 0 6.25rem !important; min-width:6.25rem; }
.st-key-public-navigation .brand small { color:var(--muted); }
.st-key-public-navigation button[kind="secondary"] { min-height:2.35rem; border-color:transparent; background:transparent; color:#343953; }
.st-key-public-navigation button { white-space:nowrap; }
.st-key-public-navigation button[kind="secondary"]:hover { color:var(--purple); background:#eeebff; }
.public-nav-login { display:block; width:100%; box-sizing:border-box; padding:.62rem 1.15rem; border-radius:10px; background:linear-gradient(100deg,var(--purple),#4a32d8); color:#fff; text-align:center; text-decoration:none; white-space:nowrap; font-size:.88rem; font-weight:700; }
.public-nav-login, .public-nav-login:link, .public-nav-login:visited { color:#fff !important; text-decoration:none !important; }
.public-nav-login:hover { color:#fff !important; box-shadow:0 5px 14px rgba(77,57,200,.18); }
.brand { font-weight: 800; font-size: 1.12rem; color:var(--ink); line-height:1.1; }
.brand small { display:block; font-weight:500; font-size:.68rem; color:#596579; margin-top:5px; }
.hero { padding: 1.55rem .2rem 1rem; }
.hero h1 { font-size: clamp(2.35rem,3.35vw,3.35rem); letter-spacing:-1.5px; line-height:1.08; margin-bottom:1rem; color:#101323; }
.hero h1 span { color:var(--purple); }
.hero p { color:#4c5870; font-size:1.08rem; line-height:1.7; max-width: 660px; }
.st-key-home-login-card h3 { font-size:1.55rem; }
.st-key-home-login-card [data-testid="stForm"] { padding:24px; }
.home-illustration { width:min(100%, 480px); margin:.6rem auto 0 0; line-height:0; }
.home-illustration img { display:block; width:100%; height:auto; object-fit:contain; object-position:left center; }
.kicker { text-transform:uppercase; letter-spacing:2px; color:var(--purple); font-size:.75rem; font-weight:800; }
.panel, div[data-testid="stVerticalBlockBorderWrapper"] { background:var(--surface); border:1px solid var(--line); border-radius:18px; box-shadow:0 8px 28px rgba(37,46,89,.045); }
.panel { padding:1.2rem 1.25rem; }
.feature { background:var(--surface); border:1px solid #e8e9f8; border-radius:14px; padding:15px 17px; margin:8px 0; color:#26314a; font-size:1rem; font-weight:600; box-shadow:0 3px 12px rgba(37,46,89,.025); }
.feature b { color:var(--purple); margin-right:10px; }
.metric { background:var(--surface); border:1px solid var(--line); border-radius:16px; padding:18px; box-shadow:0 5px 18px rgba(37,46,89,.035); min-height:116px; height:100%; box-sizing:border-box; display:flex; flex-direction:column; justify-content:center; }
.metric .value { font-size:1.75rem; font-weight:800; color:var(--purple); }
.metric .label { color:var(--muted); font-size:.85rem; line-height:1.4; min-height:2.8em; }
.role-card { background:var(--surface); border:1px solid var(--line); border-radius:17px; padding:16px; height:250px; margin-bottom:.5rem; box-sizing:border-box; display:flex; flex-direction:column; overflow:hidden; box-shadow:0 5px 20px rgba(37,46,89,.04); transition:transform .18s ease, box-shadow .18s ease; }
.role-card:hover { transform:translateY(-2px); box-shadow:0 10px 25px rgba(37,46,89,.09); }
.recommendation-role-card { min-height:28rem; height:auto; padding:20px; gap:7px; }
.recommendation-role-card .role-title { min-height:2.6em; margin:0; font-size:1.12rem; }
.recommendation-description { display:-webkit-box; -webkit-box-orient:vertical; -webkit-line-clamp:3; line-clamp:3; overflow:hidden; min-height:4.5em; color:var(--muted); font-size:.92rem; line-height:1.5; }
.recommendation-skills-label { margin-top:0; color:#5140bf; font-size:.75rem; font-weight:800; letter-spacing:.04em; text-transform:uppercase; }
.recommendation-skill-list { display:flex; flex-wrap:wrap; align-content:flex-start; gap:7px; min-height:3rem; box-sizing:border-box; }
.recommendation-skill { display:inline-flex; align-items:center; border:1px solid #e1def8; border-radius:999px; background:#f5f3ff; color:#4930c8; padding:5px 10px; font-size:.78rem; font-weight:600; line-height:1.2; }
.st-key-recommendation-grid > [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { min-width:min(100%, 340px); }
.st-key-recommendation-grid .recommendation-role-card { height:100%; }
@media (max-width: 760px) {
    .recommendation-role-card { min-height:0; }
}
.role-icon { font-size:1.7rem; line-height:2rem; min-height:2rem; }
.role-title { font-weight:800; font-size:1rem; line-height:1.3; color:#18213b; margin-top:6px; min-height:2.6em; }
.match { display:inline-flex; align-items:center; align-self:flex-start; background:#eeebff; color:#4930c8; border-radius:18px; padding:5px 10px; min-height:1.8rem; box-sizing:border-box; font-size:.76rem; font-weight:800; line-height:1.2; margin:7px 0 9px; }
.muted { color:var(--muted); font-size:.88rem; line-height:1.6; }
.role-card > .muted { display:-webkit-box; -webkit-box-orient:vertical; -webkit-line-clamp:4; line-clamp:4; overflow:hidden; line-height:1.4; min-height:5.6em; max-height:5.6em; margin-top:auto; }
.recommendation-role-card > .muted { display:block; min-height:0; max-height:none; margin:0; overflow:visible; }
.recommendation-summary-card, .recommendation-skills-card { min-height:220px; box-sizing:border-box; }
.st-key-dashboard-assessment-card, .st-key-dashboard-recommendations-card { min-height:260px; display:flex; flex-direction:column; }
.st-key-dashboard-assessment-card > [data-testid="stElementContainer"]:has([data-testid="stButton"]), .st-key-dashboard-recommendations-card > [data-testid="stElementContainer"]:has([data-testid="stButton"]) { margin-top:auto; }
.phase { position:relative; border-left:2px solid #c9c0ff; padding:0 0 17px 18px; margin-left:9px; }
.phase::before { content:""; position:absolute; width:12px; height:12px; border:3px solid #fff; border-radius:50%; background:var(--purple); left:-8px; top:1px; box-shadow:0 0 0 1px #d8d1ff; }
.phase h4 { margin:0; font-size:.96rem; color:#252b45; }
.phase p { margin:5px 0 0; color:#667085; font-size:.86rem; line-height:1.55; }
.roadmap-overview { margin-bottom:1.1rem; }
.roadmap-overview h3, .roadmap-panel h3 { margin:0 0 .55rem; font-size:1.12rem; }
.roadmap-overview p, .roadmap-panel p { margin:0; }
.roadmap-panel { margin-bottom:1rem; }
.roadmap-skill-list { display:flex; flex-wrap:wrap; gap:7px; margin:.6rem 0 1rem; }
.roadmap-skill { display:inline-flex; align-items:center; border:1px solid #e1def8; border-radius:999px; background:#f5f3ff; color:#4930c8; padding:5px 10px; font-size:.8rem; font-weight:600; line-height:1.2; }
.roadmap-skill.is-aligned { border-color:#cde9df; background:#eff9f4; color:#236b50; }
.roadmap-skill.is-to-explore { border-color:#e2dcfb; background:#f5f3ff; color:#4930c8; }
.roadmap-resources { margin:.5rem 0 0; padding-left:1.15rem; color:var(--muted); line-height:1.8; }
.roadmap-resources li + li { margin-top:.2rem; }
.roadmap-demo-note { margin-top:1rem; }
.section-label { color:#5140bf; text-transform:uppercase; font-size:.72rem; letter-spacing:1.2px; font-weight:800; }
.empty-state { background:#fff; border:1px dashed #c9cdec; border-radius:16px; padding:1.5rem; text-align:center; }
div.stButton > button, div[data-testid="stFormSubmitButton"] button { border-radius:11px; min-height:2.7rem; font-weight:700; border:1px solid #d3cefa; transition:transform .15s ease, box-shadow .15s ease; }
div.stButton > button[kind="secondary"], div[data-testid="stFormSubmitButton"] button[kind="secondaryFormSubmit"] { background:#fff; background-image:none; color:#343953; }
div.stButton > button[kind^="primary"], div[data-testid="stFormSubmitButton"] button[kind^="primary"] { background-color:var(--purple); background-image:linear-gradient(100deg,var(--purple),#4a32d8); border:0; color:#fff; }
div.stButton > button:hover, div[data-testid="stFormSubmitButton"] button:hover { transform:translateY(-1px); box-shadow:0 5px 14px rgba(77,57,200,.13); border-color:#9d91f4; }
h1,h2,h3 { letter-spacing:-.5px; color:var(--ink); }
div[data-testid="stForm"] { background:var(--surface); padding:20px; border:1px solid var(--line); border-radius:17px; box-shadow:0 6px 20px rgba(37,46,89,.035); }
div[data-testid="stTextInputRootElement"], div[data-testid="stNumberInputContainer"], div[data-testid="stSelectbox"] [data-baseweb="select"], div[data-testid="stMultiSelect"] [data-baseweb="select"] { background:#fff; border-color:var(--line); border-radius:10px; }
div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input { background:transparent; color:var(--ink); }
hr { border-color:var(--line); }
.small-note { color:#8a93a8; font-size:.78rem; line-height:1.5; }
.assessment-section-heading { display:flex; align-items:flex-start; gap:.85rem; margin:.35rem 0 1rem; }
.assessment-section-number { display:grid; place-items:center; flex:0 0 2.25rem; height:2.25rem; border-radius:11px; background:#eeebff; color:var(--purple); font-size:.82rem; font-weight:800; }
.assessment-section-heading h3 { margin:0; font-size:1.15rem; }
.assessment-section-heading p { margin:.2rem 0 0; color:var(--muted); font-size:.88rem; line-height:1.5; }
.st-key-assessment_form [data-testid="stMultiSelect"] [data-baseweb="tag"] { background:#eeebff; border:1px solid #d9d2ff; border-radius:999px; color:#4930c8; }
.st-key-assessment_form [data-testid="stMultiSelect"] [data-baseweb="tag"] span { color:#4930c8; }
.st-key-assessment_form [data-testid="stFormSubmitButton"] button { min-height:3.15rem; font-size:1rem; }
@media (max-width: 1024px) {
    [data-testid="stMainBlockContainer"] { padding:1.25rem 1rem 2rem; }
    [data-testid="stHorizontalBlock"] { flex-wrap:wrap; gap:1rem; }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { min-width:min(100%, 265px); flex:1 1 265px; }
    .hero { padding-top:1rem; }
    .hero h1 { letter-spacing:-1px; }
    .st-key-public-navigation [data-testid="stHorizontalBlock"] { flex-wrap:nowrap; gap:.5rem; }
    .st-key-public-navigation [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:not(:first-child) { flex:0 0 6rem !important; min-width:6rem; }
    .st-key-home-layout [data-testid="stHorizontalBlock"] { flex-wrap:nowrap; gap:1.5rem; }
    .st-key-home-layout [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child { min-width:0; flex:1.08 1 0; }
    .st-key-home-layout [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child { min-width:0; flex:.92 1 0; }
}
@media (max-width: 900px) {
    .st-key-home-layout [data-testid="stHorizontalBlock"] { flex-wrap:wrap; }
    .st-key-home-layout [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child,
    .st-key-home-layout [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child { flex:1 1 100%; min-width:100%; }
}
@media (max-width: 760px) {
    .st-key-public-navigation [data-testid="stHorizontalBlock"] { flex-wrap:wrap; }
    .st-key-public-navigation [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child { flex:1 0 100% !important; min-height:3rem; }
    .st-key-public-navigation [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child [data-testid="stElementContainer"] { min-height:2.2rem; }
    .st-key-public-navigation [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:not(:first-child) { flex:1 1 0 !important; min-width:0 !important; }
    .st-key-public-navigation .brand { font-size:.98rem; }
    .home-illustration { margin-top:.35rem; }
    .home-illustration img { object-position:center; }
}
@media (max-width: 430px) {
    [data-testid="stMainBlockContainer"] { padding-left:.75rem; padding-right:.75rem; }
    div[data-testid="stForm"] { padding:15px; }
}
</style>
""", unsafe_allow_html=True)

def new_profile():
    return {
        "name": "",
        "education": "B.Tech",
        "field": "Computer Science",
        "skills": ["Python", "JavaScript", "HTML/CSS", "SQL", "Machine Learning", "Data Analysis", "Problem Solving"],
        "interests": ["Artificial Intelligence", "Web Development", "Data Science"],
        "confirmed_skills": [],
        "confirmed_interests": [],
    }


if "page" not in st.session_state: st.session_state.page = "Home"
if "profile" not in st.session_state: st.session_state.profile = new_profile()
st.session_state.profile.setdefault("confirmed_skills", [])
st.session_state.profile.setdefault("confirmed_interests", [])
if "signed_in" not in st.session_state: st.session_state.signed_in = False
if "accounts" not in st.session_state: st.session_state.accounts = {}
if "saved_careers" not in st.session_state: st.session_state.saved_careers = []
st.session_state.saved_careers = normalize_saved_career_ids(st.session_state.saved_careers)

def go(page):
    st.session_state.page = page

def toggle_saved_career(career_id):
    st.session_state.saved_careers = toggle_saved_career_id(
        st.session_state.saved_careers,
        career_id,
    )

def brand():
    st.markdown('<div class="brand">🎓 AI Career Path Predictor<small>Career exploration interface prototype</small></div>', unsafe_allow_html=True)

def public_navigation(show_login=None):
    if show_login is None:
        show_login = not st.session_state.signed_in
    with st.container(key="public-navigation"):
        columns=st.columns(
            [3.5,.55,.55,.65] if show_login else [3.5,.55,.55],
            vertical_alignment="center",
        )
        logo,home_link,about_link=columns[:3]
        with logo:
            brand()
        with home_link:
            if st.button("Home",key="public_home",width="stretch"):
                go("Dashboard" if st.session_state.signed_in else "Home"); st.rerun()
        with about_link:
            if st.button("About",key="public_about",width="stretch"):
                go("About"); st.rerun()
        if show_login:
            with columns[3]:
                st.markdown('<a class="public-nav-login" href="#login-panel">Login</a>',unsafe_allow_html=True)

def sidebar():
    with st.sidebar:
        brand()
        st.markdown("---")
        pages = [
            ("🏠","Dashboard"),("🧭","Career Assessment"),("✨","Results"),
            ("👤","My Profile"),("🗺️","Learning Roadmap"),("🔖","Saved Careers"),("ℹ️","About")
        ] if st.session_state.signed_in else [("ℹ️","About")]
        for icon,label in pages:
            if st.button(f"{icon}  {label}", key=f"nav_{label}", width="stretch",
                         type="primary" if st.session_state.page == label else "secondary"):
                go(label); st.rerun()
        st.markdown("---")
        if st.session_state.signed_in:
            st.caption(f"Signed in as {st.session_state.profile.get('name') or 'Student'}")
            if st.button("↪ Logout", width="stretch"):
                st.session_state.signed_in = False
                st.session_state.profile = new_profile()
                go("Home")
                st.rerun()

def page_title(title, subtitle=None):
    st.title(title)
    if subtitle: st.caption(subtitle)

def home():
    public_navigation()
    with st.container(key="home-layout"):
        c1,c2 = st.columns([1.08, .92], gap="large")
        with c1:
            st.markdown('<div class="hero"><div class="kicker">Your future, made clearer</div><h1>Explore Career Paths That <span>Match Your Skills</span> and Interests</h1><p>Explore career paths using your confirmed skills and interests. Recommendations use a deterministic heuristic (70% skills, 30% interests), not a trained ML model. Scores are relevance indicators, not probabilities.</p></div>', unsafe_allow_html=True)
            for icon,txt in [("✦","Example Career Suggestions"),("◈","Compare Role Skills"),("♧","Sample Learning Roadmap"),("✧","Multiple Career Options"),("✓","Clear role information")]:
                st.markdown(f'<div class="feature"><b>{icon}</b>{txt}</div>', unsafe_allow_html=True)
            if st.button("Get Started →", type="primary", width="stretch"):
                go("Sign Up"); st.rerun()
            illustration = base64.b64encode(
                (Path(__file__).resolve().parent / "assets" / "career-student.svg").read_bytes()
            ).decode("ascii")
            st.markdown(
                f'<div class="home-illustration"><img src="data:image/svg+xml;base64,{illustration}" '
                'alt="A student in purple clothing working on a laptop, with floating career and analytics icons."></div>',
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown('<span id="login-panel"></span>',unsafe_allow_html=True)
            with st.container(border=True,key="home-login-card"):
                st.subheader("Welcome Back 👋")
                st.write("Login to continue")
                with st.form("login_form"):
                    email=st.text_input("Email", placeholder="Enter your email")
                    password=st.text_input("Password", type="password", placeholder="Enter your password")
                    submitted=st.form_submit_button("Login", type="primary", width="stretch")
                if submitted:
                    if not email.strip():
                        st.error("Enter your email address.")
                    elif not is_valid_email(email):
                        st.error("Enter a valid email address.")
                    elif not password:
                        st.error("Enter your password.")
                    else:
                        account = authenticate_account(
                            st.session_state.accounts,
                            email,
                            password,
                        )
                        if account is None:
                            st.error("Email or password is incorrect. Register first if you do not have an account.")
                        else:
                            st.session_state.profile = new_profile()
                            st.session_state.profile["name"] = account["name"]
                            st.session_state.signed_in = True
                            go("Dashboard")
                            st.success("Demo sign-in successful.")
                            st.rerun()
                st.markdown("Don't have an account?")
                if st.button("Sign Up", width="stretch"):
                    go("Sign Up"); st.rerun()
            st.markdown('<p class="small-note">UI prototype: authentication is currently a demo only.</p>', unsafe_allow_html=True)

def signup():
    public_navigation()
    page_title("Create your account","Start exploring career paths tailored to your strengths.")
    with st.form("signup"):
        name=st.text_input("Full name")
        email=st.text_input("Email")
        password=st.text_input("Create password", type="password")
        confirm=st.text_input("Confirm password", type="password")
        ok=st.form_submit_button("Create Account", type="primary")
    if ok:
        if not name.strip(): st.error("Enter your full name.")
        elif not email.strip(): st.error("Enter your email address.")
        elif not is_valid_email(email): st.error("Enter a valid email address.")
        elif not password: st.error("Enter a password.")
        elif password != confirm: st.error("Passwords do not match.")
        else:
            error = register_account(
                st.session_state.accounts,
                name,
                email,
                password,
            )
            if error:
                st.error(error)
            else:
                st.session_state.profile = new_profile()
                st.session_state.profile["name"] = name.strip()
                st.session_state.signed_in=True
                go("Career Assessment"); st.success("Demo account created."); st.rerun()
    if st.button("← Back to Home"): go("Home"); st.rerun()

def assessment():
    page_title("Career Assessment","Tell us about your background, skills, and interests to explore example career paths.")
    p=st.session_state.profile
    education_options=["Intermediate","Diploma","B.Tech","B.Sc","BCA","MCA","M.Tech","Other"]
    field_options=["Computer Science","Information Technology","Electronics","Mechanical","Commerce","Arts & Humanities","Other"]
    experience_options=["Beginner","Academic projects","Internship experience","Working professional"]
    skill_options=assessment_skill_options()
    interest_options=assessment_interest_options()
    profile_only_skills=unmatched_assessment_skill_options()
    profile_only_interests=unmatched_assessment_interest_options()
    age_value=max(15,min(80,int(p.get("age",22))))
    with st.form("assessment_form"):
        st.markdown('<div class="assessment-section-heading"><span class="assessment-section-number">01</span><div><h3>Your profile</h3><p>Share a few details to keep your career exploration relevant to you.</p></div></div>',unsafe_allow_html=True)
        c1,c2=st.columns(2)
        name=c1.text_input("Name *",value=p.get("name",""),placeholder="Enter your name")
        age=c2.number_input("Age *",min_value=15,max_value=80,value=age_value)
        c3,c4=st.columns(2)
        education=c3.selectbox("Education level *",education_options,index=education_options.index(p.get("education")) if p.get("education") in education_options else education_options.index("B.Tech"))
        field=c4.selectbox("Field of study *",field_options,index=field_options.index(p.get("field")) if p.get("field") in field_options else field_options.index("Computer Science"))
        experience=st.selectbox("Experience level *",experience_options,index=experience_options.index(p.get("experience")) if p.get("experience") in experience_options else 0)
        st.markdown('<div class="assessment-section-heading"><span class="assessment-section-number">02</span><div><h3>Skills</h3><p>Review the suggested profile skills and select the ones you confirm. Selected options appear as chips.</p></div></div>',unsafe_allow_html=True)
        skills=st.multiselect("Your skills *",skill_options,default=[x for x in p.get("skills",[]) if x in skill_options],placeholder="Choose one or more skills")
        st.caption(
            "Career-tagged skills can affect recommendation scores. "
            "Profile-only options currently have no matching career skill tag: "
            f"{', '.join(profile_only_skills)}."
        )
        st.markdown('<div class="assessment-section-heading"><span class="assessment-section-number">03</span><div><h3>Career interests</h3><p>Choose the fields you would like to explore.</p></div></div>',unsafe_allow_html=True)
        interests=st.multiselect("Areas of interest *",interest_options,default=[x for x in p.get("interests",[]) if x in interest_options],placeholder="Choose one or more interests")
        st.caption(
            "Career-tagged interests can affect recommendation scores. "
            "Profile-only options currently have no matching career interest tag: "
            f"{', '.join(profile_only_interests)}."
        )
        confirmed=st.checkbox("I reviewed and confirm the selected skills and career interests.")
        submitted=st.form_submit_button("Generate Career Recommendations",type="primary",width="stretch")
    if submitted:
        missing=[]
        if not name.strip(): missing.append("name")
        if not skills: missing.append("at least one skill")
        if not interests: missing.append("at least one career interest")
        if not confirmed: missing.append("confirmation that you reviewed your skills and interests")
        if missing:
            st.error(f"Please provide your {'; '.join(missing)} before continuing.")
        else:
            st.session_state.profile.update({
                "name":name.strip(),"age":age,"education":education,"field":field,
                "skills":skills,"interests":interests,"experience":experience,
                "confirmed_skills":skills,"confirmed_interests":interests,
            })
            st.session_state.pop("show_career_catalog", None)
            go("Results"); st.rerun()

def recommendations():
    page_title("Career Recommendations","Review a transparent, rules-based comparison of your confirmed skills and interests with curated career examples.")
    st.info("These results use a deterministic heuristic, not an AI/ML prediction, probability, or guaranteed career fit. The score combines skill relevance (70%) and interest relevance (30%).")
    profile_data=st.session_state.profile
    confirmed_skills=profile_data.get("confirmed_skills",[])
    confirmed_interests=profile_data.get("confirmed_interests",[])
    if not confirmed_skills or not confirmed_interests:
        st.markdown(
            '<div class="empty-state"><h3>Confirm your assessment inputs first</h3>'
            '<p class="muted">Preselected profile values are suggestions only. Review and confirm at least one skill and one career interest to see ranked examples.</p></div>',
            unsafe_allow_html=True,
        )
        if st.button("Review Career Assessment",type="primary"):
            go("Career Assessment"); st.rerun()
        return

    ranked_careers=rank_careers(CAREERS,confirmed_skills,confirmed_interests)
    st.caption("Heuristic relevance is calculated from matched required skills and interest tags. Incomplete inputs or missing career metadata are shown without a combined score.")
    if not has_meaningful_career_match(ranked_careers):
        st.warning(
            "No strong match can be identified from these confirmed inputs and the current career catalog. "
            "The catalog below is not a personalized ranking."
        )
        review_col, catalog_col = st.columns(2)
        with review_col:
            if st.button("Review Assessment", type="primary", key="review_assessment_no_match"):
                go("Career Assessment"); st.rerun()
        with catalog_col:
            if st.button("Explore Career Catalog", key="explore_catalog_no_match"):
                st.session_state.show_career_catalog = True
        if st.session_state.get("show_career_catalog"):
            st.subheader("Career catalog")
            st.caption("Curated examples, shown without a personalized ranking.")
            for role in CAREERS:
                with st.container(border=True):
                    st.markdown(f"**{role['icon']} {role['title']}**")
                    st.write(role["desc"])
                    st.caption(
                        f"Skills: {', '.join(role['skills'])} · "
                        f"Interests: {', '.join(role['interests'])}"
                    )
                    if st.button("View Learning Roadmap", key=f"catalog_details_{role['id']}"):
                        st.session_state.selected_career_id = role["id"]
                        st.session_state.selected_career = role["title"]
                        go("Learning Roadmap"); st.rerun()
        return

    with st.container(key="recommendation-grid"):
        for row_start in range(0,len(ranked_careers),2):
            cols=st.columns(2,gap="medium")
            for col,recommendation in zip(cols,ranked_careers[row_start:row_start + 2]):
                role=next((career for career in CAREERS if career["id"]==recommendation.career_id),None)
                if role is None:
                    st.error(f"Career metadata is unavailable for {recommendation.title}; this result cannot be opened.")
                    continue
                with col:
                    skills_html="".join(f'<span class="recommendation-skill">{skill}</span>' for skill in recommendation.matched_skills) or '<span class="muted">No matched required skills</span>'
                    interests_html="".join(f'<span class="recommendation-skill">{interest}</span>' for interest in recommendation.matched_interests) or '<span class="muted">No matched interest tags</span>'
                    recommended_html="".join(f'<span class="recommendation-skill">{skill}</span>' for skill in recommendation.recommended_skills) or '<span class="muted">No additional listed skills</span>'
                    score_html=(
                        f'<div class="match">Heuristic relevance: {recommendation.score:.1f}/100</div>'
                        if recommendation.score is not None
                        else '<div class="match">Score unavailable</div>'
                    )
                    st.markdown(
                        f'<div class="role-card recommendation-role-card">'
                        f'<div class="role-icon">{recommendation.icon}</div>'
                        f'<div class="role-title">{recommendation.title}</div>'
                        f'{score_html}'
                        f'<div class="recommendation-description">{recommendation.description}</div>'
                        f'<div class="recommendation-skills-label">Matched skills</div>'
                        f'<div class="recommendation-skill-list">{skills_html}</div>'
                        f'<div class="recommendation-skills-label">Matched interests</div>'
                        f'<div class="recommendation-skill-list">{interests_html}</div>'
                        f'<div class="recommendation-skills-label">Skills to explore</div>'
                        f'<div class="recommendation-skill-list">{recommended_html}</div>'
                        f'<p class="muted">{recommendation.explanation}</p></div>',
                        unsafe_allow_html=True,
                    )
                    if st.button("View Details",key=f"details_{role['id']}",width="stretch"):
                        st.session_state.selected_career_id=role["id"]
                        st.session_state.selected_career=role["title"]
                        go("Learning Roadmap"); st.rerun()
                    saved = role["id"] in st.session_state.saved_careers
                    if st.button("Remove Saved" if saved else "Save Career",key=f"save_{role['id']}",width="stretch"):
                        toggle_saved_career(role["id"]); st.rerun()

def dashboard():
    p=st.session_state.profile
    page_title(f"Welcome, {p.get('name') or 'Student'} 👋","Your career exploration dashboard.")
    a,b,c=st.columns(3, gap="medium")
    for col,val,label in [(a,str(len(CAREERS)),"Example career paths"),(b,str(len(p.get("skills",[]))),"Skills in your profile"),(c,"4","Sample roadmap phases")]:
        with col: st.markdown(f'<div class="metric"><div class="value">{val}</div><div class="label">{label}</div></div>',unsafe_allow_html=True)
    st.write("")
    st.subheader("Continue your journey")
    x,y=st.columns(2, gap="medium")
    with x:
        with st.container(border=True, key="dashboard-assessment-card"):
            st.markdown("### 🧭 Career Assessment")
            st.write("Update your skills and interests to refresh the information shown in this demo.")
            if st.button("Start Assessment",type="primary"): go("Career Assessment"); st.rerun()
    with y:
        with st.container(border=True, key="dashboard-recommendations-card"):
            st.markdown("### ✨ Career Recommendations")
            st.write("Compare potential roles and review skill requirements.")
            if st.button("View Recommendations",type="primary"): go("Results"); st.rerun()
    st.subheader("Example career paths")
    for role in CAREERS[:3]:
        st.markdown(f"**{role['icon']} {role['title']}**")

def roadmap():
    p=st.session_state.profile
    selected_id=st.session_state.get("selected_career_id")
    selected=st.session_state.get("selected_career","Data Scientist")
    role=next((r for r in CAREERS if r["id"]==selected_id),None)
    if role is None:
        role=next((r for r in CAREERS if r["title"]==selected),CAREERS[0])
    if st.button("← Back to Results"):
        go("Results"); st.rerun()
    page_title(role["title"],"Career overview, skill comparison, and a sample learning roadmap.")
    required=role.get("skills",[])
    aligned,missing_required=compare_required_skills(p.get("confirmed_skills",[]),required)
    current={
        normalize_label(skill)
        for skill in p.get("confirmed_skills",[])
        if isinstance(skill, str) and normalize_label(skill)
    }
    to_explore_by_key={}
    for skill in (*missing_required,*role.get("gap",[])):
        if isinstance(skill,str) and skill.strip():
            label=" ".join(skill.split())
            key=normalize_label(label)
            if key not in current:
                to_explore_by_key.setdefault(key,label)
    to_explore=list(to_explore_by_key.values())
    left,right=st.columns([1.15,.85],gap="large")
    with left:
        st.markdown(f'<div class="panel roadmap-overview"><h3>Career Overview</h3><p class="muted">{role["desc"]} Review current role descriptions to understand requirements in your area.</p></div>',unsafe_allow_html=True)
        st.markdown(f"#### Illustrative learning roadmap for {role['title']}")
        st.caption(
            "Phase month ranges are approximate illustrative planning examples, "
            "not guaranteed completion times, personalized schedules, employer-required "
            "timelines, or validated industry estimates."
        )
        stages=[
            ("Phase 1: Foundations (1–2 months)",role["roadmap"][0]),
            ("Phase 2: Core Skills (2–4 months)",role["roadmap"][1]),
            ("Phase 3: Applied Projects (4–6 months)",role["roadmap"][2]),
            ("Phase 4: Portfolio & Applications",role["roadmap"][3]),
        ]
        for title,desc in stages:
            st.markdown(f'<div class="phase"><h4>{title}</h4><p>{desc}</p></div>',unsafe_allow_html=True)
    with right:
        required_html="".join(f'<span class="roadmap-skill">{skill}</span>' for skill in required)
        st.markdown(f'<div class="panel roadmap-panel"><h3>Required skills</h3><p class="muted">Example skills associated with this role.</p><div class="roadmap-skill-list">{required_html}</div></div>',unsafe_allow_html=True)
        aligned_html="".join(f'<span class="roadmap-skill is-aligned">{skill}</span>' for skill in aligned) or '<p class="muted">No matching skills are listed in your profile yet.</p>'
        explore_html="".join(f'<span class="roadmap-skill is-to-explore">{skill}</span>' for skill in to_explore) or '<p class="muted">No additional example skills to explore.</p>'
        st.markdown(
            f'<div class="panel roadmap-panel"><h3>Skill comparison</h3>'
            f'<p class="muted">A simple comparison with skills confirmed in your assessment; not a score.</p>'
            f'<p><strong>Confirmed skills</strong></p><div class="roadmap-skill-list">{aligned_html}</div>'
            f'<p><strong>Example skills to explore</strong></p><div class="roadmap-skill-list">{explore_html}</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="panel roadmap-panel"><h3>Learning resources</h3>'
            '<p class="muted">No courses or external resources are curated for this demo. '
            'Validate learning materials against current official documentation and your goals.</p></div>',
            unsafe_allow_html=True,
        )
    st.info("This roadmap sequence and skill comparison are illustrative demo content, not a validated learning plan or generated assessment.")

def profile():
    page_title("My Profile","Your current assessment details.")
    p=st.session_state.profile
    with st.container(border=True):
        st.write(f"**Name:** {p.get('name') or 'Not provided'}")
        st.write(f"**Education:** {p.get('education','Not provided')}")
        st.write(f"**Field:** {p.get('field','Not provided')}")
        st.write(f"**Age:** {p.get('age','Not provided')}")
        st.write(f"**Experience:** {p.get('experience','Not provided')}")
        st.write("**Skills:** " + (", ".join(p.get("skills",[])) or "Not selected"))
        st.write("**Interests:** " + (", ".join(p.get("interests",[])) or "Not selected"))
    if st.button("Edit Assessment",type="primary"): go("Career Assessment"); st.rerun()

def saved():
    page_title("Saved Careers","Keep track of the roles you want to explore.")
    st.caption("Saved careers are kept for this browser session only.")
    saved_roles=[role for role in CAREERS if role["id"] in st.session_state.saved_careers]
    if not saved_roles:
        st.markdown('<div class="empty-state"><h3>No saved careers yet</h3><p class="muted">Save a role from Career Recommendations to keep it handy during this session.</p></div>',unsafe_allow_html=True)
        if st.button("Explore Career Recommendations",type="primary"):
            go("Results"); st.rerun()
        return
    cols=st.columns(2, gap="medium")
    for index,role in enumerate(saved_roles):
        with cols[index % 2]:
            st.markdown(f'<div class="role-card"><div class="role-icon">{role["icon"]}</div><div class="role-title">{role["title"]}</div><div class="muted">{role["desc"]}</div></div>',unsafe_allow_html=True)
            if st.button("View Details",key=f"saved_details_{role['title']}",width="stretch"):
                st.session_state.selected_career_id=role["id"]
                st.session_state.selected_career=role["title"]
                go("Learning Roadmap"); st.rerun()
            if st.button("Remove from Saved",key=f"unsave_{role['id']}",width="stretch"):
                toggle_saved_career(role["id"]); st.rerun()

def about():
    public_navigation(show_login=False)
    page_title("About the Project")
    if st.session_state.signed_in:
        st.caption(f"Current demo profile: {st.session_state.profile.get('name') or 'Student'}")
    st.markdown("""
    <div class="panel">
    <h3>AI Career Path Predictor</h3>
    <p class="muted">A student-focused decision-support application designed to connect a profile assessment with career exploration, skill-gap analysis and a staged learning roadmap.</p>
    <b>Planned technology</b><p class="muted">Python · Streamlit · Pandas · Scikit-learn · Gemini API (optional)</p>
    <b>Current stage</b><p class="muted">Interface prototype. Authentication is demo-only; predictive modelling, persistent user storage and live AI assistance are not connected.</p>
    </div>
    """,unsafe_allow_html=True)

page=st.session_state.page
if not st.session_state.signed_in and page not in ("Home","Sign Up","About"):
    go("Home")
    st.rerun()
if st.session_state.signed_in and page not in ("Home","Sign Up"):
    sidebar()
if page=="Home": home()
elif page=="Sign Up": signup()
elif page=="Dashboard": dashboard()
elif page=="Career Assessment": assessment()
elif page=="Results": recommendations()
elif page=="Learning Roadmap": roadmap()
elif page=="My Profile": profile()
elif page=="Saved Careers": saved()
elif page=="About": about()
else: home()
