import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "fursi.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT DEFAULT '',
        location TEXT DEFAULT '',
        education TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS cvs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        filename TEXT,
        raw_text TEXT,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(id)
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS extracted_cv_features (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cv_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        skills TEXT DEFAULT '[]',
        keywords TEXT DEFAULT '[]',
        education TEXT DEFAULT '',
        experience TEXT DEFAULT '[]',
        projects TEXT DEFAULT '[]',
        summary TEXT DEFAULT '',
        extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (cv_id) REFERENCES cvs(id),
        FOREIGN KEY (student_id) REFERENCES students(id)
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        location TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        role_type TEXT DEFAULT '',
        location TEXT DEFAULT '',
        description TEXT DEFAULT '',
        required_skills TEXT DEFAULT '[]',
        preferred_skills TEXT DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES companies(id)
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS job_features (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        keywords TEXT DEFAULT '[]',
        skills TEXT DEFAULT '[]',
        extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (job_id) REFERENCES jobs(id)
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS match_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        job_id INTEGER NOT NULL,
        overall_score REAL DEFAULT 0,
        semantic_score REAL DEFAULT 0,
        skill_overlap_score REAL DEFAULT 0,
        keyword_overlap_score REAL DEFAULT 0,
        project_experience_score REAL DEFAULT 0,
        matched_skills TEXT DEFAULT '[]',
        missing_skills TEXT DEFAULT '[]',
        matched_keywords TEXT DEFAULT '[]',
        suggestions TEXT DEFAULT '[]',
        explanation TEXT DEFAULT '',
        computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(id),
        FOREIGN KEY (job_id) REFERENCES jobs(id)
    )""")

    conn.commit()
    conn.close()


# ── Students ─────────────────────────────────────────────────────────────────

def insert_student(name, email="", location="", education=""):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO students (name, email, location, education) VALUES (?,?,?,?)",
        (name, email, location, education),
    )
    conn.commit()
    sid = c.lastrowid
    conn.close()
    return sid


def get_all_students():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM students ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_student(student_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ── CVs ───────────────────────────────────────────────────────────────────────

def insert_cv(student_id, filename, raw_text):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO cvs (student_id, filename, raw_text) VALUES (?,?,?)",
        (student_id, filename, raw_text),
    )
    conn.commit()
    cv_id = c.lastrowid
    conn.close()
    return cv_id


def get_cv_by_student(student_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM cvs WHERE student_id=? ORDER BY id DESC LIMIT 1", (student_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ── CV Features ───────────────────────────────────────────────────────────────

def insert_cv_features(cv_id, student_id, skills, keywords, education, experience, projects, summary):
    conn = get_connection()
    # replace any existing
    conn.execute("DELETE FROM extracted_cv_features WHERE student_id=?", (student_id,))
    conn.execute(
        """INSERT INTO extracted_cv_features
           (cv_id, student_id, skills, keywords, education, experience, projects, summary)
           VALUES (?,?,?,?,?,?,?,?)""",
        (
            cv_id, student_id,
            json.dumps(skills), json.dumps(keywords),
            education,
            json.dumps(experience), json.dumps(projects),
            summary,
        ),
    )
    conn.commit()
    conn.close()


def get_cv_features(student_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM extracted_cv_features WHERE student_id=? ORDER BY id DESC LIMIT 1",
        (student_id,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    for key in ("skills", "keywords", "experience", "projects"):
        d[key] = json.loads(d[key] or "[]")
    return d


# ── Companies & Jobs ──────────────────────────────────────────────────────────

def get_or_create_company(name, location=""):
    conn = get_connection()
    row = conn.execute("SELECT id FROM companies WHERE name=?", (name,)).fetchone()
    if row:
        conn.close()
        return row["id"]
    c = conn.cursor()
    c.execute("INSERT INTO companies (name, location) VALUES (?,?)", (name, location))
    conn.commit()
    cid = c.lastrowid
    conn.close()
    return cid


def insert_job(company_id, title, role_type, location, description, required_skills, preferred_skills):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """INSERT INTO jobs
           (company_id, title, role_type, location, description, required_skills, preferred_skills)
           VALUES (?,?,?,?,?,?,?)""",
        (
            company_id, title, role_type, location, description,
            json.dumps(required_skills), json.dumps(preferred_skills),
        ),
    )
    conn.commit()
    jid = c.lastrowid
    conn.close()
    return jid


def get_all_jobs():
    conn = get_connection()
    rows = conn.execute(
        """SELECT j.*, c.name AS company_name, c.location AS company_location
           FROM jobs j JOIN companies c ON j.company_id=c.id
           ORDER BY j.id"""
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["required_skills"] = json.loads(d["required_skills"] or "[]")
        d["preferred_skills"] = json.loads(d["preferred_skills"] or "[]")
        result.append(d)
    return result


def get_job(job_id):
    conn = get_connection()
    row = conn.execute(
        """SELECT j.*, c.name AS company_name FROM jobs j
           JOIN companies c ON j.company_id=c.id WHERE j.id=?""",
        (job_id,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["required_skills"] = json.loads(d["required_skills"] or "[]")
    d["preferred_skills"] = json.loads(d["preferred_skills"] or "[]")
    return d


def jobs_exist():
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    conn.close()
    return count > 0


# ── Job Features ─────────────────────────────────────────────────────────────

def insert_job_features(job_id, keywords, skills):
    conn = get_connection()
    conn.execute("DELETE FROM job_features WHERE job_id=?", (job_id,))
    conn.execute(
        "INSERT INTO job_features (job_id, keywords, skills) VALUES (?,?,?)",
        (job_id, json.dumps(keywords), json.dumps(skills)),
    )
    conn.commit()
    conn.close()


def get_job_features(job_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM job_features WHERE job_id=? ORDER BY id DESC LIMIT 1", (job_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["keywords"] = json.loads(d["keywords"] or "[]")
    d["skills"] = json.loads(d["skills"] or "[]")
    return d


# ── Match Results ────────────────────────────────────────────────────────────

def upsert_match(
    student_id, job_id, overall_score, semantic_score, skill_overlap_score,
    keyword_overlap_score, project_experience_score,
    matched_skills, missing_skills, matched_keywords, suggestions, explanation,
):
    conn = get_connection()
    conn.execute(
        "DELETE FROM match_results WHERE student_id=? AND job_id=?", (student_id, job_id)
    )
    conn.execute(
        """INSERT INTO match_results
           (student_id, job_id, overall_score, semantic_score, skill_overlap_score,
            keyword_overlap_score, project_experience_score,
            matched_skills, missing_skills, matched_keywords, suggestions, explanation)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            student_id, job_id, overall_score, semantic_score, skill_overlap_score,
            keyword_overlap_score, project_experience_score,
            json.dumps(matched_skills), json.dumps(missing_skills),
            json.dumps(matched_keywords), json.dumps(suggestions), explanation,
        ),
    )
    conn.commit()
    conn.close()


def get_matches_for_student(student_id, top_n=None):
    conn = get_connection()
    q = """
        SELECT mr.*, j.title, j.role_type, j.location AS job_location,
               c.name AS company_name
        FROM match_results mr
        JOIN jobs j ON mr.job_id=j.id
        JOIN companies c ON j.company_id=c.id
        WHERE mr.student_id=?
        ORDER BY mr.overall_score DESC
    """
    if top_n:
        q += f" LIMIT {int(top_n)}"
    rows = conn.execute(q, (student_id,)).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        for k in ("matched_skills", "missing_skills", "matched_keywords", "suggestions"):
            d[k] = json.loads(d[k] or "[]")
        result.append(d)
    return result


def get_matches_for_job(job_id, top_n=None):
    conn = get_connection()
    q = """
        SELECT mr.*, s.name AS student_name, s.education, s.location AS student_location
        FROM match_results mr
        JOIN students s ON mr.student_id=s.id
        WHERE mr.job_id=?
        ORDER BY mr.overall_score DESC
    """
    if top_n:
        q += f" LIMIT {int(top_n)}"
    rows = conn.execute(q, (job_id,)).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        for k in ("matched_skills", "missing_skills", "matched_keywords", "suggestions"):
            d[k] = json.loads(d[k] or "[]")
        result.append(d)
    return result


def get_match(student_id, job_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM match_results WHERE student_id=? AND job_id=?", (student_id, job_id)
    ).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    for k in ("matched_skills", "missing_skills", "matched_keywords", "suggestions"):
        d[k] = json.loads(d[k] or "[]")
    return d


def get_all_matches():
    conn = get_connection()
    rows = conn.execute(
        """SELECT mr.*, s.name AS student_name, j.title, c.name AS company_name
           FROM match_results mr
           JOIN students s ON mr.student_id=s.id
           JOIN jobs j ON mr.job_id=j.id
           JOIN companies c ON j.company_id=c.id
           ORDER BY mr.overall_score DESC"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
