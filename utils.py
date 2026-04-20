import re
from rapidfuzz import fuzz

# ── Skill alias normalisation ────────────────────────────────────────────────

SKILL_ALIASES: dict[str, str] = {
    # Programming
    "py": "python",
    "js": "javascript",
    "javascript": "javascript",
    "typescript": "typescript",
    "ts": "typescript",
    "cpp": "c++",
    "c plus plus": "c++",
    # ML / AI
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "nlp": "natural language processing",
    "natural language processing": "nlp",
    "dl": "deep learning",
    "cv": "computer vision",
    "llm": "large language model",
    "llms": "large language model",
    "genai": "generative ai",
    "gen ai": "generative ai",
    # Data
    "ds": "data science",
    "da": "data analysis",
    "bi": "business intelligence",
    "powerbi": "power bi",
    "power-bi": "power bi",
    "structured query language": "sql",
    "msbi": "power bi",
    # Workflow / agents
    "workflow automation": "workflow automation",
    "agent systems": "agent systems",
    "prompt eng": "prompt engineering",
    # Web
    "reactjs": "react",
    "vuejs": "vue.js",
    "nodejs": "node.js",
    "node": "node.js",
    # Office
    "ppt": "presentation skills",
    "powerpoint": "presentation skills",
    "ms office": "microsoft office",
    "excel": "excel",
    # Cloud
    "k8s": "kubernetes",
    "gcp": "google cloud",
}

# Master skill vocabulary — used for extraction matching
SKILLS_VOCAB: list[str] = [
    # Programming languages
    "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust",
    "ruby", "php", "swift", "kotlin", "r", "matlab", "scala", "bash",
    "shell scripting",
    # ML / AI
    "machine learning", "deep learning", "artificial intelligence",
    "natural language processing", "nlp", "computer vision",
    "reinforcement learning", "neural networks", "transformers", "bert", "gpt",
    "large language model", "generative ai", "prompt engineering", "fine-tuning",
    "scikit-learn", "tensorflow", "pytorch", "keras", "hugging face",
    "langchain", "llamaindex", "agent systems", "workflow automation",
    "llm applications", "rag", "vector databases", "embeddings",
    "time series", "forecasting",
    # Data
    "data science", "data analysis", "data engineering", "data preprocessing",
    "feature engineering", "statistics", "probability", "experimentation",
    "a/b testing", "hypothesis testing",
    "pandas", "numpy", "scipy", "matplotlib", "seaborn", "plotly",
    "sql", "nosql", "mongodb", "postgresql", "mysql", "sqlite",
    "power bi", "tableau", "excel", "google sheets",
    "etl", "data pipeline", "apache spark", "hadoop",
    "data storytelling", "reporting", "dashboards",
    # APIs / Web
    "apis", "rest api", "graphql", "fastapi", "flask", "django",
    "streamlit", "gradio", "html", "css", "react", "vue.js", "angular",
    "node.js",
    # Cloud / DevOps
    "aws", "azure", "google cloud", "docker", "kubernetes",
    "ci/cd", "git", "github", "linux",
    # Business / soft skills
    "communication", "presentation skills", "analytical thinking",
    "problem solving", "project management", "team leadership",
    "stakeholder management", "business analysis", "market research",
    "strategy", "financial modeling", "microsoft office",
    "business understanding", "data storytelling",
]


def normalise_skill(skill: str) -> str:
    """Lowercase + strip + apply alias map."""
    s = skill.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return SKILL_ALIASES.get(s, s)


def deduplicate_skills(skills: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for s in skills:
        n = normalise_skill(s)
        if n and n not in seen:
            seen.add(n)
            out.append(n)
    return out


def fuzzy_skill_match(skill: str, vocab: list[str], threshold: int = 80) -> str | None:
    """Return best vocab match above threshold, or None."""
    best_score = 0
    best_match = None
    s = normalise_skill(skill)
    for v in vocab:
        score = fuzz.token_sort_ratio(s, v)
        if score > best_score:
            best_score = score
            best_match = v
    return best_match if best_score >= threshold else None


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\x00-\x7F]+", " ", text)
    return text.strip()


def score_badge_colour(score: float) -> str:
    """Return a CSS colour string for a 0-100 score."""
    if score >= 75:
        return "#7a9e7e"
    if score >= 50:
        return "#e8a855"
    return "#c45a3a"
