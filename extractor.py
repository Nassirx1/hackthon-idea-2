"""NLP feature extraction for CVs and job descriptions."""
import re
from utils import SKILLS_VOCAB, deduplicate_skills, normalise_skill, clean_text

# ── spaCy (optional — graceful fallback) ─────────────────────────────────────

_nlp = None

def _get_nlp():
    global _nlp
    if _nlp is not None:
        return _nlp
    try:
        import spacy
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            from spacy.cli import download
            download("en_core_web_sm")
            _nlp = spacy.load("en_core_web_sm")
    except Exception:
        _nlp = False  # mark as unavailable
    return _nlp


# ── Section splitter ──────────────────────────────────────────────────────────

SECTION_HEADERS = {
    "skills": r"(?i)(technical\s+skills|skills|competencies|technologies)",
    "experience": r"(?i)(work\s+experience|experience|employment|professional\s+background)",
    "education": r"(?i)(education|academic|qualifications|degrees?)",
    "projects": r"(?i)(projects?|key\s+projects?|personal\s+projects?)",
    "summary": r"(?i)(summary|profile|objective|about\s+me|overview)",
}


def _split_sections(text: str) -> dict[str, str]:
    lines = text.split("\n")
    sections: dict[str, list[str]] = {k: [] for k in SECTION_HEADERS}
    sections["other"] = []
    current = "other"

    for line in lines:
        stripped = line.strip()
        matched = False
        for sec, pattern in SECTION_HEADERS.items():
            if re.match(pattern + r"\s*:?\s*$", stripped):
                current = sec
                matched = True
                break
        if not matched:
            sections[current].append(line)

    return {k: "\n".join(v).strip() for k, v in sections.items()}


# ── Skill extraction ──────────────────────────────────────────────────────────

def _extract_skills_vocab(text: str) -> list[str]:
    """Match skills from SKILLS_VOCAB against the text (case-insensitive)."""
    text_lower = text.lower()
    found: list[str] = []
    for skill in SKILLS_VOCAB:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found.append(skill)
    return found


_CV_SKILL_NOISE = {
    "intern", "plus", "a plus", "is a plus", "candidate", "experience",
    "the intern", "the candidate", "ideal candidate", "ambiguous", "strong interest",
    "real business", "business problems", "internal tools", "data handling",
    "business value", "financial curiosity", "model development", "use cases",
    "storytelling", "problem solving", "analytical thinking",  # kept in vocab only
}

_CV_NOISE_WORDS = {
    "intern", "candidate", "ideal", "ambiguous", "real", "business",
    "internal", "curious", "strong", "interest", "exposure", "comfortable",
    "willing", "practical", "supporting", "through", "ability", "understanding",
    "building", "analytical", "technical", "strategic",
}


def _is_valid_cv_skill(phrase: str) -> bool:
    """Return True only if the phrase looks like a genuine skill."""
    p = phrase.lower().strip()
    if len(p) < 2 or len(p) > 35:
        return False
    if p[0].isdigit():
        return False
    words = p.split()
    # reject if any word is a noise word and phrase is not in SKILLS_VOCAB
    if any(w in _CV_NOISE_WORDS for w in words) and p not in SKILLS_VOCAB:
        return False
    # reject pure stopword combos
    if len(words) > 3:
        return False
    return True


def _extract_skills_spacy(text: str) -> list[str]:
    """Use spaCy noun chunks filtered to plausible skill phrases."""
    nlp = _get_nlp()
    if not nlp:
        return []
    doc = nlp(text[:10000])
    chunks = [chunk.text.lower().strip() for chunk in doc.noun_chunks]
    return [c for c in chunks if _is_valid_cv_skill(c)]


def extract_skills(text: str) -> list[str]:
    """Extract skills from CV text — vocab match first, spaCy as supplement."""
    vocab_skills = _extract_skills_vocab(text)
    spacy_skills = _extract_skills_spacy(text)
    # only keep spaCy skills that are also in SKILLS_VOCAB (avoids free-form noise)
    spacy_filtered = [s for s in spacy_skills if s in SKILLS_VOCAB]
    combined = vocab_skills + spacy_filtered
    return deduplicate_skills(combined)


# ── Keyword extraction (TF-IDF-style simple approach) ────────────────────────

def extract_keywords(text: str, top_n: int = 30) -> list[str]:
    """Extract top keywords using simple frequency + stopword removal."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        import numpy as np
        vec = TfidfVectorizer(
            max_features=200,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=1,
        )
        tfidf = vec.fit_transform([text])
        scores = tfidf.toarray()[0]
        feature_names = vec.get_feature_names_out()
        top_idx = np.argsort(scores)[::-1][:top_n]
        keywords = [feature_names[i] for i in top_idx if scores[i] > 0]
        return keywords
    except Exception:
        words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
        stopwords = {
            "that", "with", "have", "this", "will", "your", "from", "they",
            "know", "want", "been", "good", "much", "some", "time", "very",
            "when", "come", "here", "just", "like", "long", "make", "many",
            "over", "such", "take", "than", "them", "well", "were",
        }
        freq: dict[str, int] = {}
        for w in words:
            if w not in stopwords:
                freq[w] = freq.get(w, 0) + 1
        sorted_words = sorted(freq, key=freq.get, reverse=True)
        return sorted_words[:top_n]


# ── Section text extractors ───────────────────────────────────────────────────

def _extract_bullets(section_text: str) -> list[str]:
    """Split section text into bullet points / sentences."""
    lines = [l.strip() for l in section_text.split("\n") if l.strip()]
    bullets: list[str] = []
    for line in lines:
        # strip common bullet chars
        clean = re.sub(r"^[-•*◦▪→]\s*", "", line)
        if clean:
            bullets.append(clean)
    return bullets


def extract_education(text: str) -> str:
    sections = _split_sections(text)
    edu_text = sections.get("education", "")
    if not edu_text:
        # fallback: look for degree patterns
        match = re.search(
            r"(BSc|B\.Sc|B\.S\.|BA|BEng|MSc|M\.Sc|MBA|PhD|Bachelor|Master|Doctor)[^.\n]{0,120}",
            text, re.IGNORECASE,
        )
        if match:
            return match.group(0).strip()
    return edu_text[:500] if edu_text else ""


def extract_experience(text: str) -> list[str]:
    sections = _split_sections(text)
    return _extract_bullets(sections.get("experience", ""))[:10]


def extract_projects(text: str) -> list[str]:
    sections = _split_sections(text)
    return _extract_bullets(sections.get("projects", ""))[:10]


def extract_summary(text: str) -> str:
    sections = _split_sections(text)
    summary = sections.get("summary", "")
    if not summary:
        # use first non-empty paragraph
        for para in text.split("\n\n"):
            para = para.strip()
            if len(para) > 30:
                return para[:500]
    return summary[:500]


# ── High-level CV feature extraction ─────────────────────────────────────────

def extract_cv_features(raw_text: str) -> dict:
    text = clean_text(raw_text)
    return {
        "skills": extract_skills(text),
        "keywords": extract_keywords(text),
        "education": extract_education(text),
        "experience": extract_experience(text),
        "projects": extract_projects(text),
        "summary": extract_summary(text),
    }


# ── Job description feature extraction ───────────────────────────────────────

def extract_job_features(description: str, required_skills: list[str] = None, preferred_skills: list[str] = None) -> dict:
    """
    Job skills come ONLY from the explicitly defined required/preferred skill lists.
    NLP extraction is NOT run on the description to avoid false positives like
    'intern', 'a plus', etc. Keywords are still extracted from the description
    for the keyword-overlap scoring component.
    """
    text = clean_text(description)

    # Skills = strictly the predefined lists, normalised
    all_skills: list[str] = []
    for s in (required_skills or []):
        ns = normalise_skill(s)
        if ns and ns not in all_skills:
            all_skills.append(ns)
    for s in (preferred_skills or []):
        ns = normalise_skill(s)
        if ns and ns not in all_skills:
            all_skills.append(ns)

    return {
        "skills": all_skills,
        "keywords": extract_keywords(text),
    }
