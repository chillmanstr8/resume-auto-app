"""
analyzer.py
Compare a parsed resume against a job description.

- In basic mode (no API key) it performs keyword extraction and scoring.
- In AI mode (OpenAI API key provided) it uses GPT-4o to rewrite resume
  sections with natural keyword incorporation.

The progress_callback signature is: (percent: float, message: str) -> None
"""

import json
import re
from collections import Counter
from typing import Callable


# ---------------------------------------------------------------------------
# Stop-words (common English words to exclude from keyword extraction)
# ---------------------------------------------------------------------------

_STOP_WORDS: set[str] = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "must", "shall", "can",
    "not", "no", "nor", "so", "yet", "also", "both", "about", "above",
    "after", "before", "during", "except", "into", "like", "near", "off",
    "onto", "out", "over", "past", "since", "through", "under", "until",
    "up", "upon", "while", "within", "without", "it", "its", "this",
    "that", "these", "those", "we", "you", "they", "our", "your", "their",
    "all", "each", "few", "more", "most", "other", "some", "than", "too",
    "very", "just", "able", "new", "good", "high", "large", "well",
    "make", "use", "help", "ensure", "provide", "support", "build",
    "create", "manage", "lead", "drive", "role", "position", "company",
    "opportunity", "join", "looking", "ideal", "candidate", "required",
    "preferred", "year", "years", "day", "days", "work", "working",
    "works", "team", "strong", "will", "time", "responsibilities",
    "requirements", "qualifications", "job", "description",
}

# ---------------------------------------------------------------------------
# Phrase patterns for common tech/role keywords (checked before word-split)
# ---------------------------------------------------------------------------

_PHRASE_PATTERNS: list[str] = [
    r"release management", r"release manager", r"release coordinator",
    r"release engineer", r"release train engineer",
    r"ci[/\s]?cd", r"continuous integration", r"continuous deployment",
    r"continuous delivery",
    r"devops", r"dev ops",
    r"platform engineer(?:ing)?",
    r"site reliability engineer(?:ing)?", r"\bsre\b",
    r"automation specialist",
    r"infrastructure as code", r"\biac\b",
    r"version control", r"source control",
    r"change management", r"change control",
    r"incident management", r"problem management",
    r"on[- ]call", r"on[- ]call rotation",
    r"agile", r"scrum", r"kanban", r"safe", r"scaled agile",
    r"project management", r"program management",
    r"stakeholder management",
    r"technical roadmap", r"product roadmap",
    r"microservices", r"cloud native", r"cloud[- ]native",
    r"kubernetes", r"\bk8s\b",
    r"docker", r"containers?",
    r"terraform", r"ansible", r"puppet", r"chef",
    r"\baws\b", r"\bazure\b", r"\bgcp\b", r"google cloud",
    r"python", r"bash", r"shell scripting", r"powershell",
    r"javascript", r"typescript",
    r"java\b", r"golang", r"\bgo\b",
    r"\bsql\b", r"nosql", r"mongodb", r"postgresql", r"mysql",
    r"jenkins", r"github actions", r"gitlab ci", r"circleci",
    r"\bjira\b", r"confluence", r"servicenow",
    r"monitoring", r"observability", r"alerting",
    r"logging", r"log management",
    r"cross[- ]functional",
    r"technical documentation",
    r"vendor management",
    r"risk management",
    r"sla", r"kpi", r"okr",
]

_COMPILED_PHRASES = [(p, re.compile(p, re.I)) for p in _PHRASE_PATTERNS]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_keywords(text: str, max_keywords: int = 60) -> list[str]:
    """Extract ATS-relevant keywords from *text*, phrases first then words."""
    keywords: list[str] = []
    seen: set[str] = set()
    text_lower = text.lower()

    # 1. Multi-word phrase matches
    for label, pattern in _COMPILED_PHRASES:
        m = pattern.search(text_lower)
        if m:
            phrase = m.group(0).strip()
            if phrase not in seen:
                seen.add(phrase)
                keywords.append(phrase)

    # 2. Single words (min length 3, not stop-words)
    words = re.findall(r"\b[a-zA-Z][a-zA-Z0-9+#.\-]{2,}\b", text)
    word_counts: Counter = Counter()
    for w in words:
        wl = w.lower()
        if wl not in _STOP_WORDS and len(wl) >= 3 and wl not in seen:
            word_counts[wl] += 1

    for word, _ in word_counts.most_common(max_keywords):
        if word not in seen:
            seen.add(word)
            keywords.append(word)
        if len(keywords) >= max_keywords:
            break

    return keywords[:max_keywords]


def analyze_resume(
    resume_data: dict,
    job_description: str,
    api_key: str | None = None,
    progress_callback: Callable[[float, str], None] | None = None,
) -> dict:
    """Main entry point: compare resume to job description and return results.

    Returns a dict with keys:
        match_score, missing_keywords, present_keywords,
        changes_summary, optimized_sections, ai_used,
        job_description, resume_data
    """

    def _progress(pct: float, msg: str) -> None:
        if progress_callback:
            progress_callback(pct, msg)

    resume_text = resume_data["full_text"]

    _progress(50, "🔍 Extracting keywords from job description…")
    job_keywords = extract_keywords(job_description)

    _progress(55, "📊 Comparing resume against job requirements…")
    resume_lower = resume_text.lower()

    missing: list[str] = []
    present: list[str] = []
    for kw in job_keywords:
        (present if kw.lower() in resume_lower else missing).append(kw)

    match_score = (len(present) / len(job_keywords) * 100) if job_keywords else 0.0

    results: dict = {
        "match_score": match_score,
        "missing_keywords": missing,
        "present_keywords": present,
        "job_description": job_description,
        "resume_data": resume_data,
        "ai_used": False,
        "changes_summary": [],
        "optimized_sections": None,
    }

    if api_key:
        _progress(60, "🤖 Sending to GPT-4o for AI-powered optimisation…")
        try:
            ai = _optimize_with_ai(
                resume_text=resume_text,
                job_description=job_description,
                missing_keywords=missing,
                api_key=api_key,
            )
            results.update(ai)
            results["ai_used"] = True
            _progress(72, "✅ AI optimisation complete")
        except Exception as exc:  # noqa: BLE001
            _progress(65, f"⚠️  AI optimisation failed ({exc}); using basic mode…")
            results["changes_summary"] = _basic_changes(missing, present)
    else:
        _progress(65, "📝 Building keyword recommendations (basic mode)…")
        results["changes_summary"] = _basic_changes(missing, present)

    return results


# ---------------------------------------------------------------------------
# AI optimisation (requires openai package + valid API key)
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are an expert resume writer and ATS optimisation specialist.
Your task is to optimise a resume so it scores well against an ATS system for a specific job.

STRICT RULES:
1. Never fabricate experience, skills, or qualifications.
2. Only incorporate keywords where they truthfully apply to the candidate's existing background.
3. Keep total body content concise – target two pages maximum (~700 words).
4. Use strong action verbs and specific metrics where present in the original.
5. Maintain a professional yet approachable tone.
"""

_USER_PROMPT_TEMPLATE = """Please optimise the resume below for the job description provided.

=== ORIGINAL RESUME ===
{resume_text}

=== JOB DESCRIPTION ===
{job_description}

=== KEYWORDS FOUND MISSING (incorporate only where truthful) ===
{missing_keywords}

Return a JSON object with EXACTLY these keys:
- "summary"          : string – optimised professional summary (2-4 sentences)
- "skills"           : list of strings – skills to list in the Skills section
- "experience"       : list of strings – bullet points for experience (preserve employer names/dates; optimise descriptions)
- "education"        : string – education section (preserve original; add relevant coursework if applicable)
- "changes_summary"  : list of strings – human-readable descriptions of each change made
- "removed_keywords" : list of strings – keywords removed because they were irrelevant
"""


def _optimize_with_ai(
    resume_text: str,
    job_description: str,
    missing_keywords: list[str],
    api_key: str,
) -> dict:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    user_prompt = _USER_PROMPT_TEMPLATE.format(
        resume_text=resume_text[:4500],
        job_description=job_description[:3000],
        missing_keywords=", ".join(missing_keywords[:25]),
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )

    data = json.loads(response.choices[0].message.content)

    return {
        "optimized_sections": {
            "summary": data.get("summary", ""),
            "skills": data.get("skills", []),
            "experience": data.get("experience", []),
            "education": data.get("education", ""),
        },
        "changes_summary": data.get("changes_summary", []),
        "removed_keywords": data.get("removed_keywords", []),
    }


# ---------------------------------------------------------------------------
# Basic (non-AI) change summary
# ---------------------------------------------------------------------------

def _basic_changes(missing: list[str], present: list[str]) -> list[str]:
    changes: list[str] = []
    if missing:
        changes.append(
            f"Identified {len(missing)} ATS keyword(s) missing from your resume."
        )
        for kw in missing[:8]:
            changes.append(f"  → Consider adding: '{kw}'")
        if len(missing) > 8:
            changes.append(f"  → …and {len(missing) - 8} more (see full list above).")
    if present:
        changes.append(
            f"Confirmed {len(present)} matching keyword(s) already in your resume."
        )
    changes.append(
        "💡 Tip: Add an OpenAI API key in Step 3 for full AI-powered rewriting."
    )
    return changes
