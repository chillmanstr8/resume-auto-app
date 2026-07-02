"""
resume_parser.py
Parse resume files in .docx, .pdf, and .txt formats.
Returns a dict with 'full_text', 'sections', 'paragraphs', and 'format'.
"""

import os
import re


def parse_resume(filepath: str) -> dict:
    """Parse a resume file and return structured data.

    Supported extensions: .docx, .pdf, .txt

    Returns:
        {
            "full_text": str,
            "sections": dict[str, list[str]],
            "paragraphs": list[str],
            "format": str,
        }
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Resume file not found: {filepath}")

    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".docx":
        return _parse_docx(filepath)
    elif ext == ".pdf":
        return _parse_pdf(filepath)
    elif ext == ".txt":
        return _parse_txt(filepath)
    else:
        raise ValueError(
            f"Unsupported file type '{ext}'. "
            "Please provide a .docx, .pdf, or .txt file."
        )


# ---------------------------------------------------------------------------
# Format-specific parsers
# ---------------------------------------------------------------------------

def _parse_docx(filepath: str) -> dict:
    from docx import Document  # python-docx

    doc = Document(filepath)
    full_lines: list[str] = []
    current_section = "header"
    sections: dict[str, list[str]] = {}

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        full_lines.append(text)

        # Detect section heading by style name or short ALL-CAPS/title line
        detected = _detect_section_name(text, para.style.name)
        if detected:
            current_section = detected

        sections.setdefault(current_section, []).append(text)

    return {
        "full_text": "\n".join(full_lines),
        "sections": sections,
        "paragraphs": full_lines,
        "format": "docx",
    }


def _parse_pdf(filepath: str) -> dict:
    import pdfplumber

    full_lines: list[str] = []
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_lines.extend(
                    line.strip() for line in text.splitlines() if line.strip()
                )

    combined = "\n".join(full_lines)
    return {
        "full_text": combined,
        "sections": _detect_sections_from_text(combined),
        "paragraphs": full_lines,
        "format": "pdf",
    }


def _parse_txt(filepath: str) -> dict:
    with open(filepath, encoding="utf-8", errors="ignore") as fh:
        content = fh.read()

    lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
    return {
        "full_text": "\n".join(lines),
        "sections": _detect_sections_from_text("\n".join(lines)),
        "paragraphs": lines,
        "format": "txt",
    }


# ---------------------------------------------------------------------------
# Section detection helpers
# ---------------------------------------------------------------------------

_SECTION_MAP: dict[str, list[str]] = {
    "summary": ["summary", "objective", "profile", "about me", "overview"],
    "experience": [
        "experience", "employment", "work history", "career history",
        "professional experience", "work experience",
    ],
    "skills": [
        "skills", "technical skills", "core competencies",
        "competencies", "expertise", "technologies",
    ],
    "education": ["education", "academic", "degrees", "university", "college"],
    "certifications": [
        "certifications", "certificates", "credentials", "licenses",
    ],
    "projects": ["projects", "portfolio", "key projects"],
    "awards": ["awards", "honors", "achievements", "accomplishments"],
    "publications": ["publications", "papers", "research"],
    "volunteer": ["volunteer", "community", "civic"],
}


def _detect_section_name(text: str, style_name: str = "") -> str | None:
    """Return a normalised section key if *text* looks like a heading, else None."""
    # Only check short lines (section headings are rarely more than 6 words)
    if len(text.split()) > 6:
        return None

    is_heading_style = style_name.lower().startswith("heading")
    text_lower = text.lower()

    for section, keywords in _SECTION_MAP.items():
        if any(kw in text_lower for kw in keywords):
            if is_heading_style or text.isupper() or _is_title_line(text):
                return section
    return None


def _is_title_line(text: str) -> bool:
    """Heuristic: short line that is mostly title-cased or all-caps."""
    if len(text) > 60:
        return False
    words = text.split()
    if not words:
        return False
    capitalised = sum(1 for w in words if w and w[0].isupper())
    return capitalised / len(words) >= 0.7


def _detect_sections_from_text(text: str) -> dict[str, list[str]]:
    """Detect sections in plain text by scanning for heading-like lines."""
    sections: dict[str, list[str]] = {}
    current_section = "header"

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        detected = _detect_section_name(stripped)
        if detected:
            current_section = detected

        sections.setdefault(current_section, []).append(stripped)

    return sections
