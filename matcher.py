"""Matching engine: compute similarity scores between students and jobs."""
import re
import numpy as np
import database as db
import extractor


# ── Sentence-transformer model (cached) ──────────────────────────────────────

_model = None

def _get_model():
    global _model
    if _model is not None:
        return _model
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        _model = False
    return _model


def _semantic_similarity(text_a: str, text_b: str) -> float:
    model = _get_model()
    if not model:
        return _tfidf_similarity(text_a, text_b)
    from sentence_transformers import util
    emb_a = model.encode(text_a[:512], convert_to_tensor=True)
    emb_b = model.encode(text_b[:512], convert_to_tensor=True)
    score = float(util.cos_sim(emb_a, emb_b)[0][0])
    return max(0.0, min(1.0, score))


def _tfidf_similarity(text_a: str, text_b: str) -> float:
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        vec = TfidfVectorizer(stop_words="english")
        tfidf = vec.fit_transform([text_a, text_b])
        return float(cosine_similarity(tfidf[0], tfidf[1])[0][0])
    except Exception:
        return 0.0


# ── Overlap scores ────────────────────────────────────────────────────────────
# Coverage ratio: matched / total_job_items
# Answers "what fraction of the job's requirements does the CV cover?"
# e.g. 7 matched out of 10 job skills → 70%, not 30% (Jaccard penalised broad CVs)

def _coverage(matched: int, job_total: int) -> float:
    if job_total == 0:
        return 0.0
    return matched / job_total


def _skill_overlap(cv_skills: list[str], job_skills: list[str]) -> tuple[float, list[str], list[str]]:
    cv_set = {s.lower() for s in cv_skills}
    job_set = {s.lower() for s in job_skills}
    matched = sorted(cv_set & job_set)
    missing = sorted(job_set - cv_set)
    score = _coverage(len(matched), len(job_set))
    return score, matched, missing


def _keyword_overlap(cv_kw: list[str], job_kw: list[str]) -> tuple[float, list[str]]:
    cv_set = {k.lower() for k in cv_kw}
    job_set = {k.lower() for k in job_kw}
    matched = sorted(cv_set & job_set)
    score = _coverage(len(matched), len(job_set))
    return score, matched


def _project_experience_alignment(cv_text: str, job_description: str) -> float:
    """Check how many job keywords appear in cv project/experience sections."""
    job_keywords = extractor.extract_keywords(job_description, top_n=20)
    cv_lower = cv_text.lower()
    hits = sum(1 for kw in job_keywords if kw.lower() in cv_lower)
    return min(1.0, hits / max(len(job_keywords), 1))


# ── Suggestion generation ─────────────────────────────────────────────────────

def _generate_suggestions(
    missing_skills: list[str],
    missing_kw: list[str],
    job: dict,
) -> list[str]:
    suggestions: list[str] = []
    required = {s.lower() for s in job.get("required_skills", [])}
    preferred = {s.lower() for s in job.get("preferred_skills", [])}

    for skill in missing_skills[:5]:
        if skill in required:
            suggestions.append(f"Add explicit evidence of '{skill}' — it is a required skill for this role.")
        elif skill in preferred:
            suggestions.append(f"Mentioning '{skill}' would strengthen your application for this role.")
        else:
            suggestions.append(f"Consider highlighting experience with '{skill}'.")

    # generic suggestions based on missing keywords
    tech_kw = [kw for kw in missing_kw[:3] if len(kw) > 3]
    for kw in tech_kw:
        suggestions.append(f"Use language aligned to '{kw}' from the job description.")

    if not suggestions:
        suggestions.append("Your profile already aligns well — tailor your summary to the specific role title.")

    return suggestions[:6]


# ── Explanation generation ────────────────────────────────────────────────────

def _generate_explanation(
    matched_skills: list[str],
    missing_skills: list[str],
    semantic_score: float,
    skill_overlap_score: float,
    job: dict,
    student: dict,
) -> str:
    parts: list[str] = []
    job_title = job.get("title", "this role")
    company = job.get("company_name", "the company")
    student_name = student.get("name", "The candidate")

    if matched_skills:
        top = ", ".join(matched_skills[:5])
        parts.append(f"{student_name} has strong alignment in: {top}.")

    if semantic_score >= 0.7:
        parts.append("The overall profile semantically matches the job description very well.")
    elif semantic_score >= 0.45:
        parts.append("There is moderate semantic alignment between the CV and job description.")
    else:
        parts.append("Semantic alignment is limited — the CV language could be better tailored to this role.")

    if skill_overlap_score >= 0.6:
        parts.append(f"Skill coverage is strong for {job_title} at {company}.")
    elif skill_overlap_score >= 0.3:
        parts.append(f"Skill coverage is partial — key gaps include: {', '.join(missing_skills[:3])}.")
    else:
        parts.append(f"Significant skill gaps exist: {', '.join(missing_skills[:5])}.")

    return " ".join(parts)


# ── Main scoring function ─────────────────────────────────────────────────────

def compute_match(student_id: int, job_id: int) -> dict:
    student = db.get_student(student_id)
    cv_features = db.get_cv_features(student_id)
    cv_data = db.get_cv_by_student(student_id)
    job = db.get_job(job_id)
    job_features = db.get_job_features(job_id)

    if not student or not cv_features or not job:
        return {}

    cv_text = cv_data.get("raw_text", "") if cv_data else ""

    # ── sub-scores ────────────────────────────────────────────────────────────
    job_text = job.get("description", "")
    sem_score = _semantic_similarity(cv_text, job_text)

    skill_score, matched_skills, missing_skills = _skill_overlap(
        cv_features.get("skills", []),
        job_features.get("skills", []) if job_features else
        job.get("required_skills", []) + job.get("preferred_skills", []),
    )

    kw_score, matched_kw = _keyword_overlap(
        cv_features.get("keywords", []),
        job_features.get("keywords", []) if job_features else [],
    )

    proj_score = _project_experience_alignment(cv_text, job_text)

    # ── weighted overall ──────────────────────────────────────────────────────
    overall = (
        0.35 * sem_score
        + 0.30 * skill_score
        + 0.20 * kw_score
        + 0.15 * proj_score
    ) * 100  # normalise to 0-100

    overall = round(min(100.0, max(0.0, overall)), 2)

    suggestions = _generate_suggestions(missing_skills, list(set(
        job_features.get("keywords", []) if job_features else []
    ) - set(cv_features.get("keywords", []))), job)

    explanation = _generate_explanation(
        matched_skills, missing_skills, sem_score, skill_score, job, student
    )

    result = {
        "student_id": student_id,
        "job_id": job_id,
        "overall_score": overall,
        "semantic_score": round(sem_score * 100, 2),
        "skill_overlap_score": round(skill_score * 100, 2),
        "keyword_overlap_score": round(kw_score * 100, 2),
        "project_experience_score": round(proj_score * 100, 2),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "matched_keywords": matched_kw,
        "suggestions": suggestions,
        "explanation": explanation,
    }

    # persist
    db.upsert_match(
        student_id, job_id, overall,
        round(sem_score * 100, 2),
        round(skill_score * 100, 2),
        round(kw_score * 100, 2),
        round(proj_score * 100, 2),
        matched_skills, missing_skills,
        matched_kw, suggestions, explanation,
    )

    return result


# ── Batch computation ─────────────────────────────────────────────────────────

def compute_all_matches(progress_callback=None):
    """Recompute all student × job matches."""
    students = db.get_all_students()
    jobs = db.get_all_jobs()
    total = len(students) * len(jobs)
    done = 0

    for student in students:
        if not db.get_cv_features(student["id"]):
            continue
        for job in jobs:
            if not db.get_job_features(job["id"]):
                # extract job features on the fly
                from extractor import extract_job_features
                jf = extract_job_features(
                    job["description"],
                    job["required_skills"],
                    job["preferred_skills"],
                )
                db.insert_job_features(job["id"], jf["keywords"], jf["skills"])

            compute_match(student["id"], job["id"])
            done += 1
            if progress_callback:
                progress_callback(done, total)
