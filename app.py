"""Fursi / فرصي — Student-Job Matching Platform"""
import os
import json

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

import database as db
import seed_jobs
import create_demo_pdfs
import parser as pdf_parser
import extractor
import matcher
from utils import score_badge_colour

# ── bootstrap (runs once per process) ────────────────────────────────────────

db.init_db()
seed_jobs.seed_if_empty()
create_demo_pdfs.create_demo_pdfs()


def _ingest_demo_cvs_if_needed():
    if db.get_all_students():
        return
    demo_map = {
        "Nasser_AlDataScience_CV.pdf": {
            "name": "Nasser Al-Example",
            "email": "nasser@demo.com",
            "location": "Saudi Arabia",
            "education": "BSc in Data Science",
        },
        "Sara_Analytics_CV.pdf": {
            "name": "Sara Al-Example",
            "email": "sara@demo.com",
            "location": "Saudi Arabia",
            "education": "BSc in Information Systems",
        },
    }
    paths = create_demo_pdfs.get_demo_pdf_paths()
    for filename, meta in demo_map.items():
        path = paths.get(filename)
        if not path or not os.path.exists(path):
            continue
        text = pdf_parser.extract_text_from_path(path)
        if not text.strip():
            continue
        sid = db.insert_student(
            meta["name"], meta["email"], meta["location"], meta["education"]
        )
        cv_id = db.insert_cv(sid, filename, text)
        feats = extractor.extract_cv_features(text)
        db.insert_cv_features(
            cv_id, sid,
            feats["skills"], feats["keywords"],
            feats["education"], feats["experience"],
            feats["projects"], feats["summary"],
        )


_ingest_demo_cvs_if_needed()

# ── translations ──────────────────────────────────────────────────────────────

T = {
    "en": {
        "brand": "Fursi",
        "tagline": "*AI-Powered Recruitment Matching*",
        "nav_home": "🏠 Home",
        "nav_upload": "📄 Upload CV",
        "nav_jobs": "💼 Manage Jobs",
        "nav_s2j": "🎯 Student → Best Jobs",
        "nav_j2s": "👥 Job → Best Students",
        "nav_gap": "🔍 Gap Analysis",
        "nav_db": "🗄️ Database Viewer",
        "sidebar_students": "Students",
        "sidebar_jobs": "Jobs",
        "btn_recompute": "🔄 Recompute All Matches",
        "recompute_done": "Done!",
        "computing": "Computing…",
        # home
        "home_title": "🎯 Fursi — AI Recruitment Matching Platform",
        "home_desc": "**Fursi** uses NLP and semantic similarity to match students with job and internship opportunities — explaining why each match works and where gaps exist.",
        "metric_students": "Students",
        "metric_jobs": "Job Postings",
        "metric_matches": "Match Records",
        "metric_avg": "Avg Match Score",
        "no_matches_msg": "📄 No matches yet — upload a CV on the **Upload CV** page to compute matches.",
        "top_matches": "### 🏆 Top Matches",
        "col_student": "Student",
        "col_role": "Role",
        "col_company": "Company",
        "col_overall": "Overall %",
        "col_semantic": "Semantic %",
        "col_skill": "Skill Overlap %",
        "score_dist": "### 📊 Score Distribution",
        "heatmap": "### 🔥 Student × Job Heatmap",
        "quickstart": "### 🚀 Quick Start",
        "qs_items": [
            "**Upload CV** — Upload a student's PDF CV for parsing.",
            "**Manage Jobs** — View or add job descriptions.",
            "**Student → Best Jobs** — Select a student and see ranked matches.",
            "**Job → Best Students** — Select a job and see best-fit candidates.",
            "**Gap Analysis** — Deep-dive into any student × job match.",
        ],
        # upload
        "upload_title": "📄 Upload Student CV",
        "upload_info": "Student Information",
        "lbl_name": "Full Name *",
        "lbl_email": "Email",
        "lbl_location": "Location",
        "lbl_education": "Education",
        "ph_name": "e.g. Ahmed Al-Qahtani",
        "ph_email": "student@example.com",
        "ph_location": "e.g. Riyadh, Saudi Arabia",
        "ph_education": "e.g. BSc Computer Science",
        "upload_label": "Drop your CV here (PDF)",
        "btn_process": "📥 Process & Store CV",
        "err_name": "Please enter the student's name.",
        "err_file": "Please upload a PDF CV.",
        "err_extract": "Could not extract text from the PDF. Please try a different file.",
        "spin_extract": "Extracting text from PDF…",
        "spin_nlp": "Running NLP extraction…",
        "spin_match": "Computing job matches…",
        "ok_cv": "✅ CV processed for **{name}** (Student ID: {sid})",
        "extracted_feat": "#### 📋 Extracted Features",
        "lbl_edu": "Education:",
        "lbl_skills_det": "Skills detected:",
        "lbl_summary": "Summary:",
        "lbl_keywords": "Top Keywords:",
        "lbl_projects": "Projects:",
        "lbl_experience": "Experience:",
        "instant_matches": "#### 🎯 Instant Job Matches",
        "existing_students": "### 👥 Existing Students",
        "no_students": "No students yet.",
        # jobs
        "jobs_title": "💼 Manage Job Descriptions",
        "tab_view": "📋 View Jobs",
        "tab_add": "➕ Add New Job",
        "lbl_desc": "Description:",
        "lbl_req": "Required Skills:",
        "lbl_pref": "Preferred Skills:",
        "lbl_nlp_skills": "NLP-Extracted Skills:",
        "add_job_title": "### Add a New Job Posting",
        "lbl_company": "Company Name *",
        "lbl_job_title": "Job Title *",
        "lbl_type": "Role Type",
        "type_opts": ["Internship", "Full-time", "Part-time", "Contract"],
        "lbl_req_in": "Required Skills (comma-separated)",
        "lbl_pref_in": "Preferred Skills (comma-separated)",
        "lbl_jd": "Job Description *",
        "btn_add_job": "💾 Add Job",
        "err_job": "Company, title and description are required.",
        "ok_job": "✅ Job **{title}** at **{company}** added (ID: {jid})",
        "no_jobs": "No jobs in database.",
        # s2j
        "s2j_title": "🎯 Best Jobs for a Student",
        "lbl_sel_student": "Select Student",
        "lbl_top_n": "Show top N matches",
        "lbl_edu2": "Education:",
        "lbl_loc": "Location:",
        "lbl_sum": "Summary:",
        "lbl_cv_skills": "Extracted Skills:",
        "ranked_jobs": "### Ranked Job Matches",
        "lbl_overall": "Overall Match",
        "lbl_sem": "Semantic",
        "lbl_skill_ov": "Skill Overlap",
        "lbl_kw": "Keyword Overlap",
        "lbl_proj": "Proj/Exp",
        "matched_skills": "**✅ Matched Skills:**",
        "missing_skills": "**❌ Missing Skills:**",
        "suggestions": "**💡 Suggestions:**",
        "explanation": "**Explanation:**",
        "none": "None",
        "no_match_data": "No match data. Click 'Recompute All Matches' in the sidebar.",
        "no_students_warn": "No students in database. Please upload a CV first.",
        # j2s
        "j2s_title": "👥 Best Students for a Job",
        "lbl_sel_job": "Select Job",
        "lbl_top_n2": "Show top N candidates",
        "ranked_cands": "### Ranked Candidates",
        "lbl_student": "Student:",
        "lbl_edu3": "Education:",
        "cv_skills_lbl": "CV Skills:",
        "no_jobs_warn": "No jobs in database.",
        # gap
        "gap_title": "🔍 Gap Analysis & Explainability",
        "btn_analyse": "🔎 Analyse",
        "err_no_cv": "Could not compute match. Ensure CV has been uploaded.",
        "overall_banner": "Overall Match: {score:.1f}%",
        "lbl_sem2": "Semantic Similarity",
        "lbl_skill2": "Skill Coverage",
        "lbl_kw2": "Keyword Overlap",
        "lbl_proj2": "Proj/Exp Alignment",
        "matched_s": "### ✅ Matched Skills",
        "matched_kw": "### 🔑 Matched Keywords",
        "missing_s": "### ❌ Missing Skills",
        "no_missing": "*No missing skills — great fit!*",
        "no_match_kw": "*No keyword overlap.*",
        "no_match_s": "*No direct skill matches.*",
        "sug_title": "### 💡 Improvement Suggestions",
        "explanation_title": "### 📝 Explanation",
        "cv_breakdown": "📋 Full CV Feature Breakdown",
        "job_desc_exp": "📋 Job Description",
        "lbl_required": "**Required:** ",
        "lbl_preferred": "**Preferred:** ",
        "need_both": "Need at least one student and one job.",
        # db
        "db_title": "🗄️ Database Viewer",
        "tab_students": "Students",
        "tab_cv_feat": "CVs & Features",
        "tab_companies": "Companies",
        "tab_jobs_tab": "Jobs",
        "tab_matches": "Match Results",
        "no_cv_feat": "No CV features yet.",
        "no_matches_db": "No match results yet.",
        # chart labels
        "chart_score_x": "Overall Match Score (%)",
        "chart_score_label": "Score %",
        "chart_bar_x": "Match Score (%)",
        "radar_cats": ["Semantic", "Skill", "Keyword", "Proj/Exp"],
        "dir": "ltr",
    },
    "ar": {
        "brand": "فرصي",
        "tagline": "*منصة التوظيف الذكية بالذكاء الاصطناعي*",
        "nav_home": "🏠 الرئيسية",
        "nav_upload": "📄 رفع السيرة الذاتية",
        "nav_jobs": "💼 إدارة الوظائف",
        "nav_s2j": "🎯 الطالب ← أفضل الوظائف",
        "nav_j2s": "👥 الوظيفة ← أفضل المتقدمين",
        "nav_gap": "🔍 تحليل الفجوات",
        "nav_db": "🗄️ عرض قاعدة البيانات",
        "sidebar_students": "الطلاب",
        "sidebar_jobs": "الوظائف",
        "btn_recompute": "🔄 إعادة حساب المطابقات",
        "recompute_done": "تم!",
        "computing": "جارٍ الحساب…",
        # home
        "home_title": "🎯 فرصي — منصة التوظيف الذكية",
        "home_desc": "**فرصي** تستخدم معالجة اللغة الطبيعية والتشابه الدلالي لمطابقة الطلاب بفرص العمل والتدريب، مع شرح أسباب كل مطابقة وتحديد مواطن التطوير.",
        "metric_students": "الطلاب",
        "metric_jobs": "الوظائف",
        "metric_matches": "سجلات المطابقة",
        "metric_avg": "متوسط نسبة المطابقة",
        "no_matches_msg": "📄 لا توجد مطابقات بعد — ارفع سيرة ذاتية من صفحة **رفع السيرة الذاتية** لبدء المطابقة.",
        "top_matches": "### 🏆 أفضل المطابقات",
        "col_student": "الطالب",
        "col_role": "المسمى الوظيفي",
        "col_company": "الشركة",
        "col_overall": "النسبة الكلية %",
        "col_semantic": "التشابه الدلالي %",
        "col_skill": "تغطية المهارات %",
        "score_dist": "### 📊 توزيع نسب المطابقة",
        "heatmap": "### 🔥 خريطة الحرارة: الطالب مقابل الوظيفة",
        "quickstart": "### 🚀 البدء السريع",
        "qs_items": [
            "**رفع السيرة الذاتية** — ارفع ملف PDF للطالب لاستخراج المهارات والبيانات.",
            "**إدارة الوظائف** — استعرض أو أضف وصف الوظائف.",
            "**الطالب ← أفضل الوظائف** — اختر طالباً لرؤية أفضل الوظائف المناسبة له.",
            "**الوظيفة ← أفضل المتقدمين** — اختر وظيفة لرؤية أفضل المرشحين.",
            "**تحليل الفجوات** — تحليل تفصيلي لأي مطابقة مع اقتراحات التطوير.",
        ],
        # upload
        "upload_title": "📄 رفع السيرة الذاتية",
        "upload_info": "بيانات الطالب",
        "lbl_name": "الاسم الكامل *",
        "lbl_email": "البريد الإلكتروني",
        "lbl_location": "الموقع",
        "lbl_education": "المؤهل الدراسي",
        "ph_name": "مثال: أحمد القحطاني",
        "ph_email": "student@example.com",
        "ph_location": "مثال: الرياض، المملكة العربية السعودية",
        "ph_education": "مثال: بكالوريوس علوم الحاسب",
        "upload_label": "اسحب السيرة الذاتية هنا (PDF)",
        "btn_process": "📥 معالجة وحفظ السيرة الذاتية",
        "err_name": "يرجى إدخال اسم الطالب.",
        "err_file": "يرجى رفع ملف PDF.",
        "err_extract": "تعذّر استخراج النص من الملف. يرجى تجربة ملف آخر.",
        "spin_extract": "جارٍ استخراج النص من الـ PDF…",
        "spin_nlp": "جارٍ تشغيل النماذج اللغوية…",
        "spin_match": "جارٍ حساب نسب المطابقة…",
        "ok_cv": "✅ تمّت معالجة السيرة الذاتية لـ **{name}** (رقم الطالب: {sid})",
        "extracted_feat": "#### 📋 الميزات المستخرجة",
        "lbl_edu": "التعليم:",
        "lbl_skills_det": "المهارات المكتشفة:",
        "lbl_summary": "الملخص:",
        "lbl_keywords": "أبرز الكلمات المفتاحية:",
        "lbl_projects": "المشاريع:",
        "lbl_experience": "الخبرات:",
        "instant_matches": "#### 🎯 أفضل الوظائف المناسبة",
        "existing_students": "### 👥 الطلاب المسجلون",
        "no_students": "لا يوجد طلاب مسجلون بعد.",
        # jobs
        "jobs_title": "💼 إدارة الوظائف",
        "tab_view": "📋 استعراض الوظائف",
        "tab_add": "➕ إضافة وظيفة جديدة",
        "lbl_desc": "الوصف:",
        "lbl_req": "المهارات المطلوبة:",
        "lbl_pref": "المهارات المفضلة:",
        "lbl_nlp_skills": "مهارات الوظيفة (من قاعدة البيانات):",
        "add_job_title": "### إضافة وظيفة جديدة",
        "lbl_company": "اسم الشركة *",
        "lbl_job_title": "المسمى الوظيفي *",
        "lbl_type": "نوع الدور",
        "type_opts": ["تدريب", "دوام كامل", "دوام جزئي", "عقد"],
        "lbl_req_in": "المهارات المطلوبة (مفصولة بفواصل)",
        "lbl_pref_in": "المهارات المفضلة (مفصولة بفواصل)",
        "lbl_jd": "وصف الوظيفة *",
        "btn_add_job": "💾 إضافة الوظيفة",
        "err_job": "الشركة والمسمى والوصف حقول إلزامية.",
        "ok_job": "✅ تمّت إضافة وظيفة **{title}** في **{company}** (رقم: {jid})",
        "no_jobs": "لا توجد وظائف في قاعدة البيانات.",
        # s2j
        "s2j_title": "🎯 أفضل الوظائف للطالب",
        "lbl_sel_student": "اختر الطالب",
        "lbl_top_n": "عدد النتائج",
        "lbl_edu2": "المؤهل:",
        "lbl_loc": "الموقع:",
        "lbl_sum": "الملخص:",
        "lbl_cv_skills": "المهارات المستخرجة:",
        "ranked_jobs": "### الوظائف المقترحة",
        "lbl_overall": "النسبة الكلية",
        "lbl_sem": "دلالي",
        "lbl_skill_ov": "مهارات",
        "lbl_kw": "كلمات",
        "lbl_proj": "مشاريع",
        "matched_skills": "**✅ المهارات المتطابقة:**",
        "missing_skills": "**❌ المهارات المفقودة:**",
        "suggestions": "**💡 اقتراحات التحسين:**",
        "explanation": "**التحليل:**",
        "none": "لا يوجد",
        "no_match_data": "لا توجد مطابقات. انقر على إعادة حساب المطابقات.",
        "no_students_warn": "لا يوجد طلاب. يرجى رفع سيرة ذاتية أولاً.",
        # j2s
        "j2s_title": "👥 أفضل المتقدمين للوظيفة",
        "lbl_sel_job": "اختر الوظيفة",
        "lbl_top_n2": "عدد المرشحين",
        "ranked_cands": "### المرشحون",
        "lbl_student": "الطالب:",
        "lbl_edu3": "المؤهل:",
        "cv_skills_lbl": "مهارات السيرة الذاتية:",
        "no_jobs_warn": "لا توجد وظائف في قاعدة البيانات.",
        # gap
        "gap_title": "🔍 تحليل الفجوات والشرح التفصيلي",
        "btn_analyse": "🔎 تحليل",
        "err_no_cv": "تعذّر إجراء التحليل. تأكد من رفع السيرة الذاتية.",
        "overall_banner": "نسبة المطابقة الكلية: {score:.1f}%",
        "lbl_sem2": "التشابه الدلالي",
        "lbl_skill2": "تغطية المهارات",
        "lbl_kw2": "تداخل الكلمات",
        "lbl_proj2": "المشاريع والخبرة",
        "matched_s": "### ✅ المهارات المتطابقة",
        "matched_kw": "### 🔑 الكلمات المفتاحية المتطابقة",
        "missing_s": "### ❌ المهارات المفقودة",
        "no_missing": "*لا توجد مهارات مفقودة — توافق ممتاز!*",
        "no_match_kw": "*لا يوجد تداخل في الكلمات.*",
        "no_match_s": "*لا توجد مطابقة مباشرة.*",
        "sug_title": "### 💡 اقتراحات التحسين",
        "explanation_title": "### 📝 التحليل التفصيلي",
        "cv_breakdown": "📋 تفاصيل السيرة الذاتية الكاملة",
        "job_desc_exp": "📋 وصف الوظيفة",
        "lbl_required": "**المطلوبة:** ",
        "lbl_preferred": "**المفضلة:** ",
        "need_both": "يلزم وجود طالب واحد ووظيفة واحدة على الأقل.",
        # db
        "db_title": "🗄️ عرض قاعدة البيانات",
        "tab_students": "الطلاب",
        "tab_cv_feat": "مميزات السير الذاتية",
        "tab_companies": "الشركات",
        "tab_jobs_tab": "الوظائف",
        "tab_matches": "نتائج المطابقة",
        "no_cv_feat": "لا توجد بيانات.",
        "no_matches_db": "لا توجد نتائج بعد.",
        # chart labels
        "chart_score_x": "نسبة المطابقة الكلية (%)",
        "chart_score_label": "النسبة %",
        "chart_bar_x": "نسبة المطابقة (%)",
        "radar_cats": ["دلالي", "مهارات", "كلمات", "مشاريع"],
        "dir": "rtl",
    },
}

# ── page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Fursi / فرصي",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── language state ────────────────────────────────────────────────────────────

if "lang" not in st.session_state:
    st.session_state.lang = "en"

# ── CSS (applied before any render) ──────────────────────────────────────────

is_ar = st.session_state.lang == "ar"

st.markdown(f"""
<style>
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg,#b5533c 0%,#d98c5f 100%);
}}
[data-testid="stSidebar"] * {{ color: #fff !important; }}
.score-pill {{
    display:inline-block; padding:4px 12px; border-radius:20px;
    font-weight:700; font-size:15px; color:#fff;
}}
.tag {{
    display:inline-block; background:#f3e3d3; color:#8a3a24;
    padding:2px 8px; border-radius:12px; font-size:12px; margin:2px;
}}
.tag-miss {{
    display:inline-block; background:#fbe4d8; color:#a0421c;
    padding:2px 8px; border-radius:12px; font-size:12px; margin:2px;
}}
{"/* RTL mode */.main .block-container{direction:rtl!important;}.stMarkdown,.stText,p,li,label{direction:rtl!important;text-align:right!important;}h1,h2,h3,h4,h5{direction:rtl!important;text-align:right!important;}.stTextInput input,.stTextArea textarea{direction:rtl!important;text-align:right!important;}.stSelectbox>div,.stRadio>label{direction:rtl!important;text-align:right!important;}[data-testid='stSidebar'] .stRadio{{direction:rtl!important;}}" if is_ar else ""}
</style>
""", unsafe_allow_html=True)

t = T[st.session_state.lang]


# ── helpers ───────────────────────────────────────────────────────────────────

def score_pill(score: float) -> str:
    c = score_badge_colour(score)
    return f'<span class="score-pill" style="background:{c}">{score:.1f}%</span>'


def tags_html(items: list, cls: str = "tag") -> str:
    return " ".join(f'<span class="{cls}">{i}</span>' for i in items)


def gauge_chart(value: float, title: str):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": title, "font": {"size": 13}},
        number={"suffix": "%", "font": {"size": 18}},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#b5533c"},
            "steps": [
                {"range": [0, 40], "color": "#fbe4d8"},
                {"range": [40, 70], "color": "#faeccb"},
                {"range": [70, 100], "color": "#dfead0"},
            ],
        },
    ))
    fig.update_layout(height=200, margin=dict(l=10, r=10, t=30, b=10))
    return fig


# ── sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(f"## 🎯 {t['brand']}")
    st.markdown(t["tagline"])

    # Language toggle
    col_en, col_ar = st.columns(2)
    with col_en:
        if st.button("🇬🇧 EN", use_container_width=True,
                     type="primary" if st.session_state.lang == "en" else "secondary"):
            st.session_state.lang = "en"
            st.rerun()
    with col_ar:
        if st.button("🇸🇦 AR", use_container_width=True,
                     type="primary" if st.session_state.lang == "ar" else "secondary"):
            st.session_state.lang = "ar"
            st.rerun()

    st.markdown("---")

    page = st.radio(
        "nav",
        [t["nav_home"], t["nav_upload"], t["nav_jobs"],
         t["nav_s2j"], t["nav_j2s"], t["nav_gap"], t["nav_db"]],
        label_visibility="collapsed",
    )

    st.markdown("---")
    students = db.get_all_students()
    jobs = db.get_all_jobs()
    st.markdown(f"**{t['sidebar_students']}:** {len(students)}")
    st.markdown(f"**{t['sidebar_jobs']}:** {len(jobs)}")

    if st.button(t["btn_recompute"]):
        with st.spinner(t["computing"]):
            matcher.compute_all_matches()
        st.success(t["recompute_done"])


# ═══════════════════════════════════════════════════════════════════════════════
# HOME
# ═══════════════════════════════════════════════════════════════════════════════

if page == t["nav_home"]:
    st.title(t["home_title"])
    st.markdown(t["home_desc"])
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    all_matches = db.get_all_matches()
    avg_score = (sum(m["overall_score"] for m in all_matches) / len(all_matches)) if all_matches else 0

    col1.metric(t["metric_students"], len(students))
    col2.metric(t["metric_jobs"], len(jobs))
    col3.metric(t["metric_matches"], len(all_matches))
    col4.metric(t["metric_avg"], f"{avg_score:.1f}%")

    if not all_matches and students:
        st.info(t["no_matches_msg"])

    if all_matches:
        st.markdown(t["top_matches"])
        df = pd.DataFrame(all_matches)[[
            "student_name", "title", "company_name",
            "overall_score", "semantic_score", "skill_overlap_score"
        ]].rename(columns={
            "student_name": t["col_student"],
            "title": t["col_role"],
            "company_name": t["col_company"],
            "overall_score": t["col_overall"],
            "semantic_score": t["col_semantic"],
            "skill_overlap_score": t["col_skill"],
        }).head(10)
        st.dataframe(
            df.style.background_gradient(subset=[t["col_overall"]], cmap="Blues"),
            use_container_width=True,
        )

        st.markdown(t["score_dist"])
        fig = px.histogram(
            pd.DataFrame(all_matches), x="overall_score", nbins=20,
            labels={"overall_score": t["chart_score_x"]},
            color_discrete_sequence=["#b5533c"],
        )
        fig.update_layout(height=260, margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(t["heatmap"])
        pivot = pd.DataFrame(all_matches).pivot_table(
            index="student_name", columns="title",
            values="overall_score", aggfunc="max"
        ).fillna(0)
        fig2 = px.imshow(
            pivot, text_auto=".1f", color_continuous_scale="Blues",
            labels=dict(color=t["chart_score_label"]),
        )
        fig2.update_layout(height=280, margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.markdown(t["quickstart"])
    for item in t["qs_items"]:
        st.markdown(f"- {item}")


# ═══════════════════════════════════════════════════════════════════════════════
# UPLOAD CV
# ═══════════════════════════════════════════════════════════════════════════════

elif page == t["nav_upload"]:
    st.title(t["upload_title"])
    st.markdown(f"### {t['upload_info']}")

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input(t["lbl_name"], placeholder=t["ph_name"])
        email = st.text_input(t["lbl_email"], placeholder=t["ph_email"])
    with col2:
        location = st.text_input(t["lbl_location"], placeholder=t["ph_location"])
        education = st.text_input(t["lbl_education"], placeholder=t["ph_education"])

    uploaded_file = st.file_uploader(t["upload_label"], type=["pdf"])

    if st.button(t["btn_process"], type="primary"):
        if not name.strip():
            st.error(t["err_name"])
        elif not uploaded_file:
            st.error(t["err_file"])
        else:
            with st.spinner(t["spin_extract"]):
                raw_text = pdf_parser.extract_text_from_bytes(uploaded_file.read())
            if not raw_text.strip():
                st.error(t["err_extract"])
            else:
                with st.spinner(t["spin_nlp"]):
                    feats = extractor.extract_cv_features(raw_text)

                sid = db.insert_student(name.strip(), email.strip(), location.strip(), education.strip())
                cv_id = db.insert_cv(sid, uploaded_file.name, raw_text)
                db.insert_cv_features(
                    cv_id, sid, feats["skills"], feats["keywords"],
                    feats["education"], feats["experience"],
                    feats["projects"], feats["summary"],
                )

                with st.spinner(t["spin_match"]):
                    for job in db.get_all_jobs():
                        if not db.get_job_features(job["id"]):
                            jf = extractor.extract_job_features(
                                job["description"], job["required_skills"], job["preferred_skills"]
                            )
                            db.insert_job_features(job["id"], jf["keywords"], jf["skills"])
                        matcher.compute_match(sid, job["id"])

                st.success(t["ok_cv"].format(name=name, sid=sid))
                st.markdown("---")
                st.markdown(t["extracted_feat"])
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**{t['lbl_edu']}**"); st.write(feats["education"] or "—")
                    st.markdown(f"**{t['lbl_skills_det']}**")
                    st.markdown(tags_html(feats["skills"][:20]), unsafe_allow_html=True)
                with c2:
                    st.markdown(f"**{t['lbl_summary']}**"); st.write(feats["summary"][:300] or "—")
                    st.markdown(f"**{t['lbl_keywords']}**")
                    st.markdown(tags_html(feats["keywords"][:15]), unsafe_allow_html=True)
                if feats["projects"]:
                    st.markdown(f"**{t['lbl_projects']}**")
                    for p in feats["projects"]: st.markdown(f"- {p}")
                if feats["experience"]:
                    st.markdown(f"**{t['lbl_experience']}**")
                    for e in feats["experience"]: st.markdown(f"- {e}")

                st.markdown("---")
                st.markdown(t["instant_matches"])
                for m in db.get_matches_for_student(sid, top_n=5):
                    ca, cb = st.columns([4, 1])
                    with ca:
                        st.markdown(f"**{m['title']}** @ {m['company_name']} — {m['job_location']}")
                    with cb:
                        st.markdown(score_pill(m["overall_score"]), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(t["existing_students"])
    if students:
        df_s = pd.DataFrame(students)[["id", "name", "education", "location", "created_at"]].rename(
            columns={"id": "ID", "name": t["col_student"], "education": t["lbl_education"],
                     "location": t["lbl_location"], "created_at": "Date"})
        st.dataframe(df_s, use_container_width=True)
    else:
        st.info(t["no_students"])


# ═══════════════════════════════════════════════════════════════════════════════
# MANAGE JOBS
# ═══════════════════════════════════════════════════════════════════════════════

elif page == t["nav_jobs"]:
    st.title(t["jobs_title"])
    tab1, tab2 = st.tabs([t["tab_view"], t["tab_add"]])

    with tab1:
        all_jobs = db.get_all_jobs()
        if not all_jobs:
            st.info(t["no_jobs"])
        else:
            for job in all_jobs:
                with st.expander(f"**{job['title']}** @ {job['company_name']} ({job['role_type']}) — {job['location']}"):
                    st.markdown(f"**{t['lbl_desc']}**\n{job['description']}")
                    cr, cp = st.columns(2)
                    with cr:
                        st.markdown(f"**{t['lbl_req']}**")
                        st.markdown(tags_html(job["required_skills"]), unsafe_allow_html=True)
                    with cp:
                        st.markdown(f"**{t['lbl_pref']}**")
                        st.markdown(tags_html(job["preferred_skills"]), unsafe_allow_html=True)
                    jf = db.get_job_features(job["id"])
                    if jf:
                        st.markdown(f"**{t['lbl_nlp_skills']}**")
                        st.markdown(tags_html(jf["skills"][:15]), unsafe_allow_html=True)

    with tab2:
        st.markdown(t["add_job_title"])
        c1, c2 = st.columns(2)
        with c1:
            j_company = st.text_input(t["lbl_company"])
            j_title = st.text_input(t["lbl_job_title"])
            j_type = st.selectbox(t["lbl_type"], t["type_opts"])
        with c2:
            j_location = st.text_input(t["lbl_location"])
            j_required = st.text_input(t["lbl_req_in"])
            j_preferred = st.text_input(t["lbl_pref_in"])

        j_description = st.text_area(t["lbl_jd"], height=200)

        if st.button(t["btn_add_job"], type="primary"):
            if not j_company or not j_title or not j_description:
                st.error(t["err_job"])
            else:
                req = [s.strip() for s in j_required.split(",") if s.strip()]
                pref = [s.strip() for s in j_preferred.split(",") if s.strip()]
                cid = db.get_or_create_company(j_company, j_location)
                jid = db.insert_job(cid, j_title, j_type, j_location, j_description, req, pref)
                jf = extractor.extract_job_features(j_description, req, pref)
                db.insert_job_features(jid, jf["keywords"], jf["skills"])
                for stu in db.get_all_students():
                    if db.get_cv_features(stu["id"]):
                        matcher.compute_match(stu["id"], jid)
                st.success(t["ok_job"].format(title=j_title, company=j_company, jid=jid))
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# STUDENT → BEST JOBS
# ═══════════════════════════════════════════════════════════════════════════════

elif page == t["nav_s2j"]:
    st.title(t["s2j_title"])
    students = db.get_all_students()
    if not students:
        st.warning(t["no_students_warn"]); st.stop()

    opts = {f"{s['name']} (#{s['id']})": s["id"] for s in students}
    sel = st.selectbox(t["lbl_sel_student"], list(opts.keys()))
    student_id = opts[sel]
    top_n = st.slider(t["lbl_top_n"], 1, 20, 10)

    student = db.get_student(student_id)
    cv_feat = db.get_cv_features(student_id)

    ci, cs = st.columns([3, 2])
    with ci:
        st.markdown(f"### {student['name']}")
        st.markdown(f"**{t['lbl_edu2']}** {student.get('education', '—')}")
        st.markdown(f"**{t['lbl_loc']}** {student.get('location', '—')}")
        if cv_feat:
            st.markdown(f"**{t['lbl_sum']}** {cv_feat.get('summary', '—')[:250]}")
    with cs:
        if cv_feat:
            st.markdown(f"**{t['lbl_cv_skills']}**")
            st.markdown(tags_html(cv_feat.get("skills", [])[:20]), unsafe_allow_html=True)

    st.markdown("---")
    matches = db.get_matches_for_student(student_id, top_n=top_n)
    if not matches:
        st.info(t["no_match_data"]); st.stop()

    st.markdown(f"{t['ranked_jobs']} ({len(matches)})")

    for rank, m in enumerate(matches, 1):
        with st.expander(
            f"#{rank} — {m['title']} @ {m['company_name']} | {m['overall_score']:.1f}%",
            expanded=(rank <= 3),
        ):
            cg, cd = st.columns([2, 3])
            with cg:
                st.plotly_chart(gauge_chart(m["overall_score"], t["lbl_overall"]), use_container_width=True)
            with cd:
                st.markdown(f"**{t['col_role']}:** {m['title']}")
                st.markdown(f"**{t['col_company']}:** {m['company_name']}")
                st.markdown(f"**{t['lbl_loc']}** {m.get('job_location', '—')}")
                st.markdown("---")
                sc = st.columns(4)
                sc[0].metric(t["lbl_sem"], f"{m['semantic_score']:.1f}%")
                sc[1].metric(t["lbl_skill_ov"], f"{m['skill_overlap_score']:.1f}%")
                sc[2].metric(t["lbl_kw"], f"{m['keyword_overlap_score']:.1f}%")
                sc[3].metric(t["lbl_proj"], f"{m['project_experience_score']:.1f}%")

            st.markdown(t["matched_skills"])
            st.markdown(tags_html(m["matched_skills"][:15]) or t["none"], unsafe_allow_html=True)
            st.markdown(t["missing_skills"])
            st.markdown(tags_html(m["missing_skills"][:15], "tag-miss") or t["none"], unsafe_allow_html=True)
            st.markdown(t["suggestions"])
            for sug in m["suggestions"]: st.markdown(f"- {sug}")
            st.markdown(f"{t['explanation']} {m['explanation']}")

    df_m = pd.DataFrame(matches)[["title", "company_name", "overall_score"]].copy()
    df_m["Label"] = df_m["title"] + " @ " + df_m["company_name"]
    fig = px.bar(df_m, x="overall_score", y="Label", orientation="h",
                 labels={"overall_score": t["chart_bar_x"], "Label": ""},
                 color="overall_score", color_continuous_scale="Blues")
    fig.update_layout(height=max(200, 40*len(df_m)), margin=dict(l=0,r=0,t=20,b=0),
                      yaxis={"autorange": "reversed"})
    st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# JOB → BEST STUDENTS
# ═══════════════════════════════════════════════════════════════════════════════

elif page == t["nav_j2s"]:
    st.title(t["j2s_title"])
    all_jobs = db.get_all_jobs()
    if not all_jobs:
        st.warning(t["no_jobs_warn"]); st.stop()

    opts = {f"{j['title']} @ {j['company_name']}": j["id"] for j in all_jobs}
    sel = st.selectbox(t["lbl_sel_job"], list(opts.keys()))
    job_id = opts[sel]
    top_n = st.slider(t["lbl_top_n2"], 1, 20, 10)

    job = db.get_job(job_id)
    cj1, cj2 = st.columns([3, 2])
    with cj1:
        st.markdown(f"### {job['title']}")
        st.markdown(f"**{t['col_company']}:** {job['company_name']} | **{t['lbl_type']}:** {job['role_type']} | **{t['lbl_loc']}** {job['location']}")
        st.markdown(f"**{t['lbl_desc']}** {job['description'][:400]}…")
    with cj2:
        st.markdown(f"**{t['lbl_req']}**")
        st.markdown(tags_html(job["required_skills"]), unsafe_allow_html=True)
        st.markdown(f"**{t['lbl_pref']}**")
        st.markdown(tags_html(job["preferred_skills"]), unsafe_allow_html=True)

    st.markdown("---")
    matches = db.get_matches_for_job(job_id, top_n=top_n)
    if not matches:
        st.info(t["no_match_data"]); st.stop()

    st.markdown(f"{t['ranked_cands']} ({len(matches)})")

    for rank, m in enumerate(matches, 1):
        with st.expander(
            f"#{rank} — {m['student_name']} | {m['overall_score']:.1f}%",
            expanded=(rank <= 3),
        ):
            cg, cd = st.columns([2, 3])
            with cg:
                st.plotly_chart(gauge_chart(m["overall_score"], t["lbl_overall"]), use_container_width=True)
            with cd:
                st.markdown(f"**{t['lbl_student']}** {m['student_name']}")
                st.markdown(f"**{t['lbl_edu3']}** {m.get('education', '—')}")
                st.markdown(f"**{t['lbl_loc']}** {m.get('student_location', '—')}")
                st.markdown("---")
                sc = st.columns(4)
                sc[0].metric(t["lbl_sem"], f"{m['semantic_score']:.1f}%")
                sc[1].metric(t["lbl_skill_ov"], f"{m['skill_overlap_score']:.1f}%")
                sc[2].metric(t["lbl_kw"], f"{m['keyword_overlap_score']:.1f}%")
                sc[3].metric(t["lbl_proj"], f"{m['project_experience_score']:.1f}%")

            cv_feat = db.get_cv_features(m["student_id"])
            if cv_feat:
                st.markdown(f"**{t['cv_skills_lbl']}**")
                st.markdown(tags_html(cv_feat.get("skills", [])[:15]), unsafe_allow_html=True)
            st.markdown(t["matched_skills"])
            st.markdown(tags_html(m["matched_skills"][:15]) or t["none"], unsafe_allow_html=True)
            st.markdown(t["missing_skills"])
            st.markdown(tags_html(m["missing_skills"][:10], "tag-miss") or t["none"], unsafe_allow_html=True)
            st.markdown(f"{t['explanation']} {m['explanation']}")

    df_m = pd.DataFrame(matches)[["student_name", "overall_score"]].copy()
    fig = px.bar(df_m, x="overall_score", y="student_name", orientation="h",
                 labels={"overall_score": t["chart_bar_x"], "student_name": t["col_student"]},
                 color="overall_score", color_continuous_scale="Purples")
    fig.update_layout(height=max(200, 40*len(df_m)), margin=dict(l=0,r=0,t=20,b=0),
                      yaxis={"autorange": "reversed"})
    st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# GAP ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

elif page == t["nav_gap"]:
    st.title(t["gap_title"])
    students = db.get_all_students()
    all_jobs = db.get_all_jobs()
    if not students or not all_jobs:
        st.warning(t["need_both"]); st.stop()

    cs, cj = st.columns(2)
    with cs:
        sopts = {f"{s['name']} (#{s['id']})": s["id"] for s in students}
        ssel = st.selectbox(t["lbl_sel_student"], list(sopts.keys()))
        student_id = sopts[ssel]
    with cj:
        jopts = {f"{j['title']} @ {j['company_name']}": j["id"] for j in all_jobs}
        jsel = st.selectbox(t["lbl_sel_job"], list(jopts.keys()))
        job_id = jopts[jsel]

    if st.button(t["btn_analyse"], type="primary"):
        with st.spinner(t["computing"]):
            result = matcher.compute_match(student_id, job_id)
        if not result:
            st.error(t["err_no_cv"]); st.stop()

        student = db.get_student(student_id)
        job = db.get_job(job_id)
        cv_feat = db.get_cv_features(student_id)

        st.markdown("---")
        st.markdown(f"## {student['name']}  ↔  {job['title']} @ {job['company_name']}")

        colour = score_badge_colour(result["overall_score"])
        st.markdown(
            f'<div style="background:{colour};padding:16px;border-radius:12px;text-align:center;">'
            f'<span style="color:#fff;font-size:32px;font-weight:700;">'
            f'{t["overall_banner"].format(score=result["overall_score"])}</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown("")

        gcols = st.columns(4)
        for col, (lbl, val) in zip(gcols, [
            (t["lbl_sem2"], result["semantic_score"]),
            (t["lbl_skill2"], result["skill_overlap_score"]),
            (t["lbl_kw2"], result["keyword_overlap_score"]),
            (t["lbl_proj2"], result["project_experience_score"]),
        ]):
            col.plotly_chart(gauge_chart(val, lbl), use_container_width=True)

        cats = t["radar_cats"]
        vals = [result["semantic_score"], result["skill_overlap_score"],
                result["keyword_overlap_score"], result["project_experience_score"]]
        fig_r = go.Figure(go.Scatterpolar(
            r=vals+[vals[0]], theta=cats+[cats[0]],
            fill="toself", fillcolor="rgba(42,82,152,0.25)",
            line=dict(color="#b5533c"),
        ))
        fig_r.update_layout(polar=dict(radialaxis=dict(range=[0,100])),
                            showlegend=False, height=300,
                            margin=dict(l=20,r=20,t=20,b=20))
        st.plotly_chart(fig_r, use_container_width=True)

        st.markdown("---")
        r1, r2 = st.columns(2)
        with r1:
            st.markdown(t["matched_s"])
            st.markdown(tags_html(result["matched_skills"]) or t["no_match_s"], unsafe_allow_html=True)
            st.markdown(t["matched_kw"])
            st.markdown(tags_html(result["matched_keywords"][:20]) or t["no_match_kw"], unsafe_allow_html=True)
        with r2:
            st.markdown(t["missing_s"])
            st.markdown(
                tags_html(result["missing_skills"], "tag-miss") or t["no_missing"],
                unsafe_allow_html=True,
            )
            st.markdown(t["sug_title"])
            for sug in result["suggestions"]: st.markdown(f"- {sug}")

        st.markdown("---")
        st.markdown(t["explanation_title"])
        st.info(result["explanation"])

        if cv_feat:
            with st.expander(t["cv_breakdown"]):
                st.markdown(f"**{t['lbl_edu']}** {cv_feat.get('education','—')}")
                st.markdown(f"**{t['lbl_summary']}** {cv_feat.get('summary','—')}")
                st.markdown(tags_html(cv_feat.get("skills",[])), unsafe_allow_html=True)
                if cv_feat.get("projects"):
                    st.markdown(f"**{t['lbl_projects']}**")
                    for p in cv_feat["projects"]: st.markdown(f"- {p}")
                if cv_feat.get("experience"):
                    st.markdown(f"**{t['lbl_experience']}**")
                    for e in cv_feat["experience"]: st.markdown(f"- {e}")

        with st.expander(t["job_desc_exp"]):
            st.markdown(job["description"])
            st.markdown(t["lbl_required"] + ", ".join(job["required_skills"]))
            st.markdown(t["lbl_preferred"] + ", ".join(job["preferred_skills"]))


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE VIEWER
# ═══════════════════════════════════════════════════════════════════════════════

elif page == t["nav_db"]:
    st.title(t["db_title"])
    tabs = st.tabs([t["tab_students"], t["tab_cv_feat"],
                    t["tab_companies"], t["tab_jobs_tab"], t["tab_matches"]])

    with tabs[0]:
        st.dataframe(pd.DataFrame(db.get_all_students()), use_container_width=True)

    with tabs[1]:
        conn = db.get_connection()
        rows = conn.execute(
            "SELECT s.name, e.education, e.skills, e.keywords, e.summary "
            "FROM extracted_cv_features e JOIN students s ON e.student_id=s.id"
        ).fetchall()
        conn.close()
        if rows:
            df_cv = pd.DataFrame([dict(r) for r in rows])
            df_cv["skills"] = df_cv["skills"].apply(lambda x: ", ".join(json.loads(x)) if x else "")
            df_cv["keywords"] = df_cv["keywords"].apply(lambda x: ", ".join(json.loads(x)[:10]) if x else "")
            st.dataframe(df_cv, use_container_width=True)
        else:
            st.info(t["no_cv_feat"])

    with tabs[2]:
        conn = db.get_connection()
        rows = conn.execute("SELECT * FROM companies").fetchall()
        conn.close()
        st.dataframe(pd.DataFrame([dict(r) for r in rows]), use_container_width=True)

    with tabs[3]:
        all_jobs = db.get_all_jobs()
        if all_jobs:
            df_j = pd.DataFrame(all_jobs)
            df_j["required_skills"] = df_j["required_skills"].apply(", ".join)
            df_j["preferred_skills"] = df_j["preferred_skills"].apply(", ".join)
            st.dataframe(df_j[["id","company_name","title","role_type","location",
                               "required_skills","preferred_skills"]], use_container_width=True)

    with tabs[4]:
        all_matches = db.get_all_matches()
        if all_matches:
            df_m = pd.DataFrame(all_matches)[[
                "student_name","title","company_name","overall_score",
                "semantic_score","skill_overlap_score","keyword_overlap_score",
                "project_experience_score","computed_at"
            ]]
            st.dataframe(
                df_m.style.background_gradient(subset=["overall_score"], cmap="Blues"),
                use_container_width=True,
            )
        else:
            st.info(t["no_matches_db"])
