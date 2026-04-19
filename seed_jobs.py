"""Seed sample job postings into the database."""
import database as db
import extractor


SAMPLE_JOBS = [
    {
        "company": "NexaCore AI",
        "company_location": "Riyadh",
        "title": "AI Automation Engineering Intern",
        "role_type": "Internship",
        "location": "Riyadh",
        "description": (
            "We are looking for an intern to help build internal AI agents and workflow automations. "
            "The ideal candidate has experience or strong interest in Python, APIs, LLM applications, "
            "workflow automation, prompt engineering, and internal tools. Exposure to NLP, SQL, and "
            "data handling is a plus. The intern should be comfortable in ambiguous environments and "
            "willing to build practical systems that solve real business problems."
        ),
        "required_skills": ["Python", "APIs", "workflow automation", "prompt engineering", "data handling"],
        "preferred_skills": ["NLP", "SQL", "LLMs", "Streamlit", "agent systems"],
    },
    {
        "company": "Veridian Capital",
        "company_location": "Riyadh / Abu Dhabi",
        "title": "Client & Product Summer Intern",
        "role_type": "Internship",
        "location": "Riyadh / Abu Dhabi",
        "description": (
            "This internship supports product and client teams through market research, product "
            "understanding, communication, presentation building, analytical thinking, and strategic "
            "problem solving. Candidates should have strong communication, business thinking, "
            "presentation skills, and the ability to connect technical insights to business value. "
            "Data analysis and financial curiosity are a plus."
        ),
        "required_skills": ["communication", "analytical thinking", "presentation skills", "business understanding"],
        "preferred_skills": ["market research", "data analysis", "strategy", "stakeholder communication"],
    },
    {
        "company": "Stratos Analytics",
        "company_location": "Riyadh",
        "title": "Data Science Intern",
        "role_type": "Internship",
        "location": "Riyadh",
        "description": (
            "The intern will support data science use cases such as machine learning, analytics, "
            "experimentation, Python-based analysis, and model development. Candidates should "
            "understand statistics, data preprocessing, machine learning fundamentals, and data "
            "storytelling."
        ),
        "required_skills": ["Python", "statistics", "machine learning", "data preprocessing"],
        "preferred_skills": ["experimentation", "SQL", "visualization", "storytelling"],
    },
]


def seed_if_empty():
    """Insert sample jobs only if no jobs exist yet."""
    if db.jobs_exist():
        return
    seed()


def seed(force: bool = False):
    """Unconditionally seed sample jobs (use force=True to re-seed)."""
    if force:
        conn = db.get_connection()
        conn.execute("DELETE FROM job_features")
        conn.execute("DELETE FROM jobs")
        conn.execute("DELETE FROM companies")
        conn.commit()
        conn.close()

    for job_data in SAMPLE_JOBS:
        company_id = db.get_or_create_company(
            job_data["company"], job_data.get("company_location", "")
        )
        job_id = db.insert_job(
            company_id=company_id,
            title=job_data["title"],
            role_type=job_data["role_type"],
            location=job_data["location"],
            description=job_data["description"],
            required_skills=job_data["required_skills"],
            preferred_skills=job_data["preferred_skills"],
        )
        # extract and store job features
        jf = extractor.extract_job_features(
            job_data["description"],
            job_data["required_skills"],
            job_data["preferred_skills"],
        )
        db.insert_job_features(job_id, jf["keywords"], jf["skills"])

    print(f"[seed_jobs] Seeded {len(SAMPLE_JOBS)} sample jobs.")


if __name__ == "__main__":
    db.init_db()
    seed()
