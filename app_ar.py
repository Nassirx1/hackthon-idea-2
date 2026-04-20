"""فرصي — منصة مطابقة الطلاب بالوظائف (النسخة العربية)"""
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

db.init_db()
seed_jobs.seed_if_empty()
create_demo_pdfs.create_demo_pdfs()


def _ingest_demo_cvs_if_needed():
    if db.get_all_students():
        return
    demo_map = {
        "Nasser_AlDataScience_CV.pdf": {
            "name": "ناصر المثال",
            "email": "nasser@demo.com",
            "location": "المملكة العربية السعودية",
            "education": "بكالوريوس علوم البيانات",
        },
        "Sara_Analytics_CV.pdf": {
            "name": "سارة المثال",
            "email": "sara@demo.com",
            "location": "المملكة العربية السعودية",
            "education": "بكالوريوس نظم المعلومات",
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
            cv_id, sid, feats["skills"], feats["keywords"],
            feats["education"], feats["experience"],
            feats["projects"], feats["summary"],
        )


_ingest_demo_cvs_if_needed()

# ── إعدادات الصفحة ────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="فرصي — مطابقة التوظيف",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS — RTL + ألوان ─────────────────────────────────────────────────────────

st.markdown("""
<style>
/* RTL عام */
.main .block-container {
    direction: rtl !important;
}
.stMarkdown, .stText, p, li, label, span {
    direction: rtl !important;
    text-align: right !important;
}
h1, h2, h3, h4, h5 {
    direction: rtl !important;
    text-align: right !important;
}
/* حقول الإدخال */
.stTextInput input, .stTextArea textarea {
    direction: rtl !important;
    text-align: right !important;
}
/* القائمة المنسدلة */
.stSelectbox > div, .stRadio > label {
    direction: rtl !important;
    text-align: right !important;
}
/* الشريط الجانبي */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #8a3a24 0%, #b5533c 100%) !important;
}
[data-testid="stSidebar"] * { color: #fff !important; }
[data-testid="stSidebar"] .stRadio { direction: rtl !important; }
/* البطاقات */
.metric-card {
    background: #fbf5ee;
    border-right: 4px solid #b5533c;
    border-left: none;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 6px 0;
    direction: rtl;
}
.score-pill {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 15px;
    color: #fff;
}
.tag {
    display: inline-block;
    background: #f3e3d3;
    color: #8a3a24;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 12px;
    margin: 2px;
    direction: ltr;
}
.tag-miss {
    display: inline-block;
    background: #fbe4d8;
    color: #a0421c;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 12px;
    margin: 2px;
    direction: ltr;
}
/* رأس الصفحة */
.section-header {
    color: #8a3a24;
    font-size: 18px;
    font-weight: 700;
    border-bottom: 2px solid #b5533c;
    padding-bottom: 4px;
    margin-top: 16px;
    direction: rtl;
    text-align: right;
}
/* تبويبات */
.stTabs [data-baseweb="tab"] {
    direction: rtl;
}
/* أزرار */
.stButton button {
    direction: rtl;
}
/* جداول البيانات — أبقِ الأرقام LTR */
[data-testid="stDataFrameResizable"] {
    direction: ltr;
}
</style>
""", unsafe_allow_html=True)


# ── دوال مساعدة ───────────────────────────────────────────────────────────────

def score_pill(score: float) -> str:
    colour = score_badge_colour(score)
    return f'<span class="score-pill" style="background:{colour}">{score:.1f}%</span>'


def tags_html(items: list, cls: str = "tag") -> str:
    return " ".join(f'<span class="{cls}">{i}</span>' for i in items)


def gauge_chart(value: float, title: str):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": title, "font": {"size": 13, "family": "Arial"}},
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


# ── الشريط الجانبي ─────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🎯 فرصي")
    st.markdown("*منصة التوظيف الذكية بالذكاء الاصطناعي*")
    st.markdown("---")

    page = st.radio(
        "التنقل",
        [
            "🏠 الرئيسية",
            "📄 رفع السيرة الذاتية",
            "💼 إدارة الوظائف",
            "🎯 الطالب ← أفضل الوظائف",
            "👥 الوظيفة ← أفضل المتقدمين",
            "🔍 تحليل الفجوات",
            "🗄️ عرض قاعدة البيانات",
        ],
        label_visibility="collapsed",
    )
    st.markdown("---")

    students = db.get_all_students()
    jobs = db.get_all_jobs()
    st.markdown(f"**الطلاب:** {len(students)}")
    st.markdown(f"**الوظائف:** {len(jobs)}")

    if st.button("🔄 إعادة حساب المطابقات"):
        with st.spinner("جارٍ الحساب…"):
            matcher.compute_all_matches()
        st.success("تم!")

    st.markdown("---")
    st.markdown("[🌐 English Version](http://localhost:8505)")


# ═══════════════════════════════════════════════════════════════════════════════
# الصفحة: الرئيسية
# ═══════════════════════════════════════════════════════════════════════════════

if page == "🏠 الرئيسية":
    st.title("🎯 فرصي — منصة التوظيف الذكية")
    st.markdown(
        "**فرصي** تستخدم معالجة اللغة الطبيعية والتشابه الدلالي لمطابقة الطلاب بفرص العمل والتدريب، "
        "مع شرح أسباب كل مطابقة وتحديد مواطن التطوير."
    )
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    all_matches = db.get_all_matches()
    if not all_matches and students:
        st.info("📄 لا توجد مطابقات بعد — ارفع سيرة ذاتية من صفحة **رفع السيرة الذاتية** لبدء المطابقة.")

    avg_score = (sum(m["overall_score"] for m in all_matches) / len(all_matches)) if all_matches else 0
    col1.metric("الطلاب", len(students))
    col2.metric("الوظائف", len(jobs))
    col3.metric("سجلات المطابقة", len(all_matches))
    col4.metric("متوسط نسبة المطابقة", f"{avg_score:.1f}%")

    if all_matches:
        st.markdown("### 🏆 أفضل المطابقات")
        df = pd.DataFrame(all_matches)[[
            "student_name", "title", "company_name",
            "overall_score", "semantic_score", "skill_overlap_score"
        ]].rename(columns={
            "student_name": "الطالب",
            "title": "المسمى الوظيفي",
            "company_name": "الشركة",
            "overall_score": "النسبة الكلية %",
            "semantic_score": "التشابه الدلالي %",
            "skill_overlap_score": "تغطية المهارات %",
        }).head(10)
        st.dataframe(
            df.style.background_gradient(subset=["النسبة الكلية %"], cmap="Blues"),
            use_container_width=True,
        )

        st.markdown("### 📊 توزيع نسب المطابقة")
        fig = px.histogram(
            pd.DataFrame(all_matches), x="overall_score", nbins=20,
            labels={"overall_score": "نسبة المطابقة الكلية (%)"},
            color_discrete_sequence=["#b5533c"],
        )
        fig.update_layout(height=280, margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### 🔥 خريطة الحرارة: الطالب مقابل الوظيفة")
        pivot = pd.DataFrame(all_matches).pivot_table(
            index="student_name", columns="title",
            values="overall_score", aggfunc="max"
        ).fillna(0)
        fig2 = px.imshow(
            pivot, text_auto=".1f", color_continuous_scale="Blues",
            labels=dict(color="النسبة %"),
        )
        fig2.update_layout(height=300, margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🚀 البدء السريع")
    st.markdown("""
1. **رفع السيرة الذاتية** — ارفع ملف PDF للطالب لاستخراج المهارات والبيانات.
2. **إدارة الوظائف** — استعرض أو أضف وصف الوظائف.
3. **الطالب ← أفضل الوظائف** — اختر طالباً لرؤية أفضل الوظائف المناسبة له.
4. **الوظيفة ← أفضل المتقدمين** — اختر وظيفة لرؤية أفضل المرشحين.
5. **تحليل الفجوات** — تحليل تفصيلي لأي مطابقة مع اقتراحات التطوير.
""")


# ═══════════════════════════════════════════════════════════════════════════════
# الصفحة: رفع السيرة الذاتية
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "📄 رفع السيرة الذاتية":
    st.title("📄 رفع السيرة الذاتية")

    st.markdown("### بيانات الطالب")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("الاسم الكامل *", placeholder="مثال: أحمد القحطاني")
        email = st.text_input("البريد الإلكتروني", placeholder="student@example.com")
    with col2:
        location = st.text_input("الموقع", placeholder="مثال: الرياض، المملكة العربية السعودية")
        education = st.text_input("المؤهل الدراسي", placeholder="مثال: بكالوريوس علوم الحاسب")

    st.markdown("### رفع ملف PDF للسيرة الذاتية")
    uploaded_file = st.file_uploader(
        "اسحب السيرة الذاتية هنا (PDF)",
        type=["pdf"],
        help="سيستخرج النظام المهارات والكلمات المفتاحية والتعليم والمشاريع والخبرات تلقائياً.",
    )

    if st.button("📥 معالجة وحفظ السيرة الذاتية", type="primary"):
        if not name.strip():
            st.error("يرجى إدخال اسم الطالب.")
        elif not uploaded_file:
            st.error("يرجى رفع ملف PDF.")
        else:
            with st.spinner("جارٍ استخراج النص من الـ PDF…"):
                pdf_bytes = uploaded_file.read()
                raw_text = pdf_parser.extract_text_from_bytes(pdf_bytes)

            if not raw_text.strip():
                st.error("تعذّر استخراج النص من الملف. يرجى تجربة ملف آخر.")
            else:
                with st.spinner("جارٍ تشغيل النماذج اللغوية…"):
                    feats = extractor.extract_cv_features(raw_text)

                sid = db.insert_student(
                    name.strip(), email.strip(), location.strip(), education.strip()
                )
                cv_id = db.insert_cv(sid, uploaded_file.name, raw_text)
                db.insert_cv_features(
                    cv_id, sid, feats["skills"], feats["keywords"],
                    feats["education"], feats["experience"],
                    feats["projects"], feats["summary"],
                )

                with st.spinner("جارٍ حساب نسب المطابقة…"):
                    for job in db.get_all_jobs():
                        if not db.get_job_features(job["id"]):
                            jf = extractor.extract_job_features(
                                job["description"],
                                job["required_skills"],
                                job["preferred_skills"],
                            )
                            db.insert_job_features(job["id"], jf["keywords"], jf["skills"])
                        matcher.compute_match(sid, job["id"])

                st.success(f"✅ تمّت معالجة السيرة الذاتية لـ **{name}** (رقم الطالب: {sid})")
                st.markdown("---")
                st.markdown("#### 📋 الميزات المستخرجة")
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**التعليم:**")
                    st.write(feats["education"] or "—")
                    st.markdown("**المهارات المكتشفة:**")
                    st.markdown(tags_html(feats["skills"][:20]), unsafe_allow_html=True)
                with c2:
                    st.markdown("**الملخص:**")
                    st.write(feats["summary"][:300] or "—")
                    st.markdown("**أبرز الكلمات المفتاحية:**")
                    st.markdown(tags_html(feats["keywords"][:15]), unsafe_allow_html=True)

                if feats["projects"]:
                    st.markdown("**المشاريع:**")
                    for p in feats["projects"]:
                        st.markdown(f"- {p}")
                if feats["experience"]:
                    st.markdown("**الخبرات:**")
                    for e in feats["experience"]:
                        st.markdown(f"- {e}")

                st.markdown("---")
                st.markdown("#### 🎯 أفضل الوظائف المناسبة")
                for m in db.get_matches_for_student(sid, top_n=5):
                    col_a, col_b = st.columns([4, 1])
                    with col_a:
                        st.markdown(f"**{m['title']}** — {m['company_name']} ({m['job_location']})")
                    with col_b:
                        st.markdown(score_pill(m["overall_score"]), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 👥 الطلاب المسجلون")
    if students:
        df_s = pd.DataFrame(students)[
            ["id", "name", "education", "location", "created_at"]
        ].rename(columns={
            "id": "الرقم", "name": "الاسم", "education": "المؤهل",
            "location": "الموقع", "created_at": "تاريخ الرفع",
        })
        st.dataframe(df_s, use_container_width=True)
    else:
        st.info("لا يوجد طلاب مسجلون بعد.")


# ═══════════════════════════════════════════════════════════════════════════════
# الصفحة: إدارة الوظائف
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "💼 إدارة الوظائف":
    st.title("💼 إدارة الوظائف")

    tab1, tab2 = st.tabs(["📋 استعراض الوظائف", "➕ إضافة وظيفة جديدة"])

    with tab1:
        all_jobs = db.get_all_jobs()
        if not all_jobs:
            st.info("لا توجد وظائف في قاعدة البيانات.")
        else:
            for job in all_jobs:
                with st.expander(
                    f"**{job['title']}** — {job['company_name']} ({job['role_type']}) | {job['location']}"
                ):
                    st.markdown(f"**الوصف:**\n{job['description']}")
                    col_r, col_p = st.columns(2)
                    with col_r:
                        st.markdown("**المهارات المطلوبة:**")
                        st.markdown(tags_html(job["required_skills"]), unsafe_allow_html=True)
                    with col_p:
                        st.markdown("**المهارات المفضلة:**")
                        st.markdown(tags_html(job["preferred_skills"]), unsafe_allow_html=True)
                    jf = db.get_job_features(job["id"])
                    if jf:
                        st.markdown("**مهارات الوظيفة (من قاعدة البيانات):**")
                        st.markdown(tags_html(jf["skills"]), unsafe_allow_html=True)

    with tab2:
        st.markdown("### إضافة وظيفة جديدة")
        c1, c2 = st.columns(2)
        with c1:
            j_company = st.text_input("اسم الشركة *")
            j_title = st.text_input("المسمى الوظيفي *")
            j_type = st.selectbox("نوع الدور", ["تدريب", "دوام كامل", "دوام جزئي", "عقد"])
        with c2:
            j_location = st.text_input("الموقع")
            j_required = st.text_input("المهارات المطلوبة (مفصولة بفواصل)")
            j_preferred = st.text_input("المهارات المفضلة (مفصولة بفواصل)")

        j_description = st.text_area("وصف الوظيفة *", height=200)

        if st.button("💾 إضافة الوظيفة", type="primary"):
            if not j_company or not j_title or not j_description:
                st.error("الشركة والمسمى والوصف حقول إلزامية.")
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
                st.success(f"✅ تمّت إضافة وظيفة **{j_title}** في **{j_company}** (رقم: {jid})")
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# الصفحة: الطالب ← أفضل الوظائف
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "🎯 الطالب ← أفضل الوظائف":
    st.title("🎯 أفضل الوظائف للطالب")

    students = db.get_all_students()
    if not students:
        st.warning("لا يوجد طلاب. يرجى رفع سيرة ذاتية أولاً.")
        st.stop()

    options = {f"{s['name']} (#{s['id']})": s["id"] for s in students}
    selected_label = st.selectbox("اختر الطالب", list(options.keys()))
    student_id = options[selected_label]
    top_n = st.slider("عدد النتائج", 1, 20, 10)

    student = db.get_student(student_id)
    cv_feat = db.get_cv_features(student_id)

    col_info, col_skills = st.columns([3, 2])
    with col_info:
        st.markdown(f"### {student['name']}")
        st.markdown(f"**المؤهل:** {student.get('education', '—')}")
        st.markdown(f"**الموقع:** {student.get('location', '—')}")
        if cv_feat:
            st.markdown(f"**الملخص:** {cv_feat.get('summary', '—')[:250]}")
    with col_skills:
        if cv_feat:
            st.markdown("**المهارات المستخرجة:**")
            st.markdown(tags_html(cv_feat.get("skills", [])[:20]), unsafe_allow_html=True)

    st.markdown("---")
    matches = db.get_matches_for_student(student_id, top_n=top_n)

    if not matches:
        st.info("لا توجد مطابقات. انقر على **إعادة حساب المطابقات** في الشريط الجانبي.")
        st.stop()

    st.markdown(f"### الوظائف المقترحة ({len(matches)} نتيجة)")

    for rank, m in enumerate(matches, 1):
        with st.expander(
            f"#{rank} — {m['title']} | {m['company_name']} | النسبة: {m['overall_score']:.1f}%",
            expanded=(rank <= 3),
        ):
            col_gauge, col_detail = st.columns([2, 3])
            with col_gauge:
                st.plotly_chart(gauge_chart(m["overall_score"], "النسبة الكلية"), use_container_width=True)
            with col_detail:
                st.markdown(f"**الوظيفة:** {m['title']} ({m.get('role_type', '—')})")
                st.markdown(f"**الشركة:** {m['company_name']}")
                st.markdown(f"**الموقع:** {m.get('job_location', '—')}")
                st.markdown("---")
                sub_cols = st.columns(4)
                sub_cols[0].metric("دلالي", f"{m['semantic_score']:.1f}%")
                sub_cols[1].metric("مهارات", f"{m['skill_overlap_score']:.1f}%")
                sub_cols[2].metric("كلمات", f"{m['keyword_overlap_score']:.1f}%")
                sub_cols[3].metric("مشاريع", f"{m['project_experience_score']:.1f}%")

            st.markdown("**✅ المهارات المتطابقة:**")
            st.markdown(tags_html(m["matched_skills"][:15]) or "لا يوجد", unsafe_allow_html=True)
            st.markdown("**❌ المهارات المفقودة:**")
            st.markdown(tags_html(m["missing_skills"][:15], "tag-miss") or "لا يوجد", unsafe_allow_html=True)
            st.markdown("**💡 اقتراحات التحسين:**")
            for sug in m["suggestions"]:
                st.markdown(f"- {sug}")
            st.markdown(f"**التحليل:** {m['explanation']}")

    df_m = pd.DataFrame(matches)[["title", "company_name", "overall_score"]].copy()
    df_m["التسمية"] = df_m["title"] + " — " + df_m["company_name"]
    fig = px.bar(
        df_m, x="overall_score", y="التسمية", orientation="h",
        labels={"overall_score": "نسبة المطابقة (%)", "التسمية": ""},
        color="overall_score", color_continuous_scale="Blues",
    )
    fig.update_layout(
        height=max(200, 40 * len(df_m)),
        margin=dict(l=0, r=0, t=20, b=0),
        yaxis={"autorange": "reversed"},
    )
    st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# الصفحة: الوظيفة ← أفضل المتقدمين
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "👥 الوظيفة ← أفضل المتقدمين":
    st.title("👥 أفضل المتقدمين للوظيفة")

    all_jobs = db.get_all_jobs()
    if not all_jobs:
        st.warning("لا توجد وظائف في قاعدة البيانات.")
        st.stop()

    options = {f"{j['title']} — {j['company_name']}": j["id"] for j in all_jobs}
    selected_label = st.selectbox("اختر الوظيفة", list(options.keys()))
    job_id = options[selected_label]
    top_n = st.slider("عدد المرشحين", 1, 20, 10)

    job = db.get_job(job_id)
    jf = db.get_job_features(job_id)

    col_j1, col_j2 = st.columns([3, 2])
    with col_j1:
        st.markdown(f"### {job['title']}")
        st.markdown(f"**الشركة:** {job['company_name']} | **النوع:** {job['role_type']} | **الموقع:** {job['location']}")
        st.markdown(f"**الوصف:** {job['description'][:400]}…")
    with col_j2:
        st.markdown("**المهارات المطلوبة:**")
        st.markdown(tags_html(job["required_skills"]), unsafe_allow_html=True)
        st.markdown("**المهارات المفضلة:**")
        st.markdown(tags_html(job["preferred_skills"]), unsafe_allow_html=True)

    st.markdown("---")
    matches = db.get_matches_for_job(job_id, top_n=top_n)

    if not matches:
        st.info("لا توجد مطابقات. انقر على **إعادة حساب المطابقات** في الشريط الجانبي.")
        st.stop()

    st.markdown(f"### المرشحون ({len(matches)} نتيجة)")

    for rank, m in enumerate(matches, 1):
        with st.expander(
            f"#{rank} — {m['student_name']} | النسبة: {m['overall_score']:.1f}%",
            expanded=(rank <= 3),
        ):
            col_gauge, col_detail = st.columns([2, 3])
            with col_gauge:
                st.plotly_chart(gauge_chart(m["overall_score"], "النسبة الكلية"), use_container_width=True)
            with col_detail:
                st.markdown(f"**الطالب:** {m['student_name']}")
                st.markdown(f"**المؤهل:** {m.get('education', '—')}")
                st.markdown(f"**الموقع:** {m.get('student_location', '—')}")
                st.markdown("---")
                sub_cols = st.columns(4)
                sub_cols[0].metric("دلالي", f"{m['semantic_score']:.1f}%")
                sub_cols[1].metric("مهارات", f"{m['skill_overlap_score']:.1f}%")
                sub_cols[2].metric("كلمات", f"{m['keyword_overlap_score']:.1f}%")
                sub_cols[3].metric("مشاريع", f"{m['project_experience_score']:.1f}%")

            cv_feat = db.get_cv_features(m["student_id"])
            if cv_feat:
                st.markdown("**مهارات السيرة الذاتية:**")
                st.markdown(tags_html(cv_feat.get("skills", [])[:15]), unsafe_allow_html=True)
            st.markdown("**المهارات المتطابقة:**")
            st.markdown(tags_html(m["matched_skills"][:15]) or "لا يوجد", unsafe_allow_html=True)
            st.markdown("**المهارات المفقودة:**")
            st.markdown(tags_html(m["missing_skills"][:10], "tag-miss") or "لا يوجد", unsafe_allow_html=True)
            st.markdown(f"**التحليل:** {m['explanation']}")

    df_m = pd.DataFrame(matches)[["student_name", "overall_score"]].copy()
    fig = px.bar(
        df_m, x="overall_score", y="student_name", orientation="h",
        labels={"overall_score": "نسبة المطابقة (%)", "student_name": "الطالب"},
        color="overall_score", color_continuous_scale="Purples",
    )
    fig.update_layout(
        height=max(200, 40 * len(df_m)),
        margin=dict(l=0, r=0, t=20, b=0),
        yaxis={"autorange": "reversed"},
    )
    st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# الصفحة: تحليل الفجوات
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "🔍 تحليل الفجوات":
    st.title("🔍 تحليل الفجوات والشرح التفصيلي")

    students = db.get_all_students()
    all_jobs = db.get_all_jobs()
    if not students or not all_jobs:
        st.warning("يلزم وجود طالب واحد ووظيفة واحدة على الأقل.")
        st.stop()

    col_s, col_j = st.columns(2)
    with col_s:
        stu_opts = {f"{s['name']} (#{s['id']})": s["id"] for s in students}
        sel_stu = st.selectbox("اختر الطالب", list(stu_opts.keys()))
        student_id = stu_opts[sel_stu]
    with col_j:
        job_opts = {f"{j['title']} — {j['company_name']}": j["id"] for j in all_jobs}
        sel_job = st.selectbox("اختر الوظيفة", list(job_opts.keys()))
        job_id = job_opts[sel_job]

    if st.button("🔎 تحليل", type="primary"):
        with st.spinner("جارٍ التحليل…"):
            result = matcher.compute_match(student_id, job_id)

        if not result:
            st.error("تعذّر إجراء التحليل. تأكد من رفع السيرة الذاتية.")
            st.stop()

        student = db.get_student(student_id)
        job = db.get_job(job_id)
        cv_feat = db.get_cv_features(student_id)

        st.markdown("---")
        st.markdown(f"## {student['name']}  ↔  {job['title']} — {job['company_name']}")

        colour = score_badge_colour(result["overall_score"])
        st.markdown(
            f'<div style="background:{colour};padding:16px;border-radius:12px;text-align:center;direction:rtl;">'
            f'<span style="color:#fff;font-size:32px;font-weight:700;">'
            f'نسبة المطابقة الكلية: {result["overall_score"]:.1f}%</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown("")

        g_cols = st.columns(4)
        gauge_data = [
            ("التشابه الدلالي", result["semantic_score"]),
            ("تغطية المهارات", result["skill_overlap_score"]),
            ("تداخل الكلمات", result["keyword_overlap_score"]),
            ("المشاريع والخبرة", result["project_experience_score"]),
        ]
        for col, (title, val) in zip(g_cols, gauge_data):
            col.plotly_chart(gauge_chart(val, title), use_container_width=True)

        st.markdown("---")

        cats = ["دلالي", "مهارات", "كلمات", "مشاريع"]
        vals = [
            result["semantic_score"],
            result["skill_overlap_score"],
            result["keyword_overlap_score"],
            result["project_experience_score"],
        ]
        fig_radar = go.Figure(go.Scatterpolar(
            r=vals + [vals[0]], theta=cats + [cats[0]],
            fill="toself",
            fillcolor="rgba(26,74,158,0.25)",
            line=dict(color="#b5533c"),
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(range=[0, 100])),
            showlegend=False, height=320,
            margin=dict(l=20, r=20, t=20, b=20),
        )
        st.plotly_chart(fig_radar, use_container_width=True)

        st.markdown("---")
        row1, row2 = st.columns(2)

        with row1:
            st.markdown("### ✅ المهارات المتطابقة")
            st.markdown(tags_html(result["matched_skills"]) or "لا توجد مطابقة مباشرة.", unsafe_allow_html=True)

            st.markdown("### 🔑 الكلمات المفتاحية المتطابقة")
            st.markdown(tags_html(result["matched_keywords"][:20]) or "لا يوجد تداخل.", unsafe_allow_html=True)

        with row2:
            st.markdown("### ❌ المهارات المفقودة")
            st.markdown(
                tags_html(result["missing_skills"], "tag-miss") or "لا توجد مهارات مفقودة — توافق ممتاز!",
                unsafe_allow_html=True,
            )

            st.markdown("### 💡 اقتراحات التحسين")
            for sug in result["suggestions"]:
                st.markdown(f"- {sug}")

        st.markdown("---")
        st.markdown("### 📝 التحليل التفصيلي")
        st.info(result["explanation"])

        if cv_feat:
            with st.expander("📋 تفاصيل السيرة الذاتية الكاملة"):
                st.markdown(f"**التعليم:** {cv_feat.get('education', '—')}")
                st.markdown(f"**الملخص:** {cv_feat.get('summary', '—')}")
                st.markdown("**جميع المهارات:**")
                st.markdown(tags_html(cv_feat.get("skills", [])), unsafe_allow_html=True)
                if cv_feat.get("projects"):
                    st.markdown("**المشاريع:**")
                    for p in cv_feat["projects"]:
                        st.markdown(f"- {p}")
                if cv_feat.get("experience"):
                    st.markdown("**الخبرات:**")
                    for e in cv_feat["experience"]:
                        st.markdown(f"- {e}")

        with st.expander("📋 وصف الوظيفة"):
            st.markdown(job["description"])
            st.markdown("**المطلوبة:** " + ", ".join(job["required_skills"]))
            st.markdown("**المفضلة:** " + ", ".join(job["preferred_skills"]))


# ═══════════════════════════════════════════════════════════════════════════════
# الصفحة: عرض قاعدة البيانات
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "🗄️ عرض قاعدة البيانات":
    st.title("🗄️ عرض قاعدة البيانات")

    tabs = st.tabs(["الطلاب", "مميزات السير الذاتية", "الشركات", "الوظائف", "نتائج المطابقة"])

    with tabs[0]:
        st.subheader("الطلاب")
        st.dataframe(pd.DataFrame(db.get_all_students()), use_container_width=True)

    with tabs[1]:
        st.subheader("مميزات السير الذاتية")
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
            st.info("لا توجد بيانات.")

    with tabs[2]:
        st.subheader("الشركات")
        conn = db.get_connection()
        rows = conn.execute("SELECT * FROM companies").fetchall()
        conn.close()
        st.dataframe(pd.DataFrame([dict(r) for r in rows]), use_container_width=True)

    with tabs[3]:
        st.subheader("الوظائف")
        all_jobs = db.get_all_jobs()
        if all_jobs:
            df_j = pd.DataFrame(all_jobs)
            df_j["required_skills"] = df_j["required_skills"].apply(lambda x: ", ".join(x))
            df_j["preferred_skills"] = df_j["preferred_skills"].apply(lambda x: ", ".join(x))
            st.dataframe(
                df_j[["id", "company_name", "title", "role_type", "location",
                       "required_skills", "preferred_skills"]],
                use_container_width=True,
            )

    with tabs[4]:
        st.subheader("نتائج المطابقة")
        all_matches = db.get_all_matches()
        if all_matches:
            df_m = pd.DataFrame(all_matches)[[
                "student_name", "title", "company_name",
                "overall_score", "semantic_score",
                "skill_overlap_score", "keyword_overlap_score",
                "project_experience_score", "computed_at",
            ]]
            st.dataframe(
                df_m.style.background_gradient(subset=["overall_score"], cmap="Blues"),
                use_container_width=True,
            )
        else:
            st.info("لا توجد نتائج بعد.")
