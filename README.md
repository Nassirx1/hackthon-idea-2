# Fursi — AI-Powered Student-to-Job Matching Platform

Fursi matches students to job and internship opportunities using NLP on CV PDFs and job descriptions.

---

## Features

- Upload PDF CVs → text extraction (pdfplumber + PyMuPDF)
- Keyword & skill extraction via spaCy + TF-IDF + curated vocabulary
- Semantic similarity via `sentence-transformers` (`all-MiniLM-L6-v2`)
- Weighted scoring: semantic × 35% + skill overlap × 30% + keyword overlap × 20% + project/exp × 15%
- Explainable results: matched/missing skills, improvement suggestions, radar charts
- Recruiter view: rank students per job
- Student view: rank jobs per student
- Gap analysis page with full visual breakdown
- SQLite storage — no external DB needed

---

## Installation

### 1. Create a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Download the spaCy English model

```bash
python -m spacy download en_core_web_sm
```

### 4. Run the app

```bash
streamlit run app.py
```

The app opens at **http://localhost:8501**

---

## First-Run Demo

On the very first run, Fursi automatically:

1. Creates `demo_cvs/Nasser_AlDataScience_CV.pdf` and `demo_cvs/Sara_Analytics_CV.pdf`
2. Seeds 3 sample jobs (Tabby, BlackRock, Mozn)
3. Parses both CVs and extracts features
4. Computes all student × job match scores

Expected outcomes:
- **Nasser** → highest match with Tabby AI Automation Intern & Mozn Data Science Intern
- **Sara** → highest match with BlackRock Client & Product Summer Intern

No manual setup is needed for the demo.

---

## Uploading Real CVs

1. Go to **📄 Upload Student CV**
2. Fill in the student's name, email, location, education
3. Upload a PDF CV
4. The system extracts text, runs NLP, stores results, and computes job matches instantly

---

## Adding New Jobs

### Via the UI

1. Go to **💼 Manage Jobs → Add New Job**
2. Fill in company, title, type, location, skills, description
3. Click **Add Job** — matches are computed for all existing students automatically

### Via seed_jobs.py

Edit the `SAMPLE_JOBS` list in `seed_jobs.py` and run:

```bash
python seed_jobs.py
```

---

## Project Structure

```
fursi/
├── app.py               # Streamlit UI (7 pages)
├── database.py          # SQLite schema + CRUD helpers
├── extractor.py         # NLP feature extraction (skills, keywords, sections)
├── matcher.py           # Scoring engine (semantic + skill + keyword + proj/exp)
├── parser.py            # PDF text extraction (pdfplumber + PyMuPDF fallback)
├── seed_jobs.py         # Sample job seeding
├── create_demo_pdfs.py  # Demo PDF CV generation
├── utils.py             # Skill aliases, normalisation, helpers
├── requirements.txt
├── README.md
├── fursi.db             # SQLite database (auto-created)
└── demo_cvs/            # Generated demo CV PDFs
    ├── Nasser_AlDataScience_CV.pdf
    └── Sara_Analytics_CV.pdf
```

---

## Scoring Formula

```
overall_score = (
    0.35 × semantic_similarity   # sentence-transformers cosine similarity
  + 0.30 × skill_overlap         # Jaccard: CV skills ∩ job skills / union
  + 0.20 × keyword_overlap       # TF-IDF keyword Jaccard
  + 0.15 × project_experience    # job keywords present in CV proj/exp sections
) × 100
```

---

## Resetting the Database

Delete `fursi.db` and re-run the app — it will re-seed automatically.
