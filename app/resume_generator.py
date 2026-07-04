"""
resume_generator.py
Build a new, ATS-optimised .docx resume from analysis results.

Two modes:
  - AI mode   : uses GPT-4o optimised section content
  - Basic mode: copies the original .docx and appends a keyword-suggestion
                note so the user can make targeted edits themselves
"""

import os
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_optimized_resume(
    original_path: str,
    results: dict,
    output_path: str,
) -> None:
    """Write an optimised .docx to *output_path*.

    Uses AI-produced sections when available, otherwise creates an annotated
    copy of the original with keyword suggestions.
    """
    if results.get("ai_used") and results.get("optimized_sections"):
        _build_ai_resume(original_path, results, output_path)
    else:
        _build_annotated_resume(original_path, results, output_path)


# ---------------------------------------------------------------------------
# AI-driven resume builder
# ---------------------------------------------------------------------------

def _build_ai_resume(original_path: str, results: dict, output_path: str) -> None:
    sections = results["optimized_sections"]
    resume_data = results["resume_data"]
    paragraphs = resume_data.get("paragraphs", [])

    doc = Document()
    _set_margins(doc)
    _apply_normal_style(doc)

    # ── Header: name + contact ──
    name = paragraphs[0] if paragraphs else "Your Name"
    contact_lines = [p for p in paragraphs[1:5] if _looks_like_contact(p)]

    name_para = doc.add_paragraph()
    name_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _run(name_para, name, size=20, bold=True, color=_C_HEADING)
    _space(name_para, before=0, after=2)

    if contact_lines:
        c_para = doc.add_paragraph()
        c_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _run(c_para, "  •  ".join(contact_lines), size=10, color=_C_SUB)
        _space(c_para, before=0, after=4)

    _rule(doc)

    # ── Summary ──
    summary = sections.get("summary", "").strip()
    if summary:
        _section_heading(doc, "PROFESSIONAL SUMMARY")
        p = doc.add_paragraph(summary)
        _space(p, before=4, after=4)

    # ── Skills ──
    skills = sections.get("skills", [])
    if skills:
        _section_heading(doc, "CORE SKILLS & COMPETENCIES")
        skill_items = skills if isinstance(skills, list) else [skills]
        # Three-column-style row using bullet separator
        p = doc.add_paragraph("  •  ".join(str(s) for s in skill_items))
        _space(p, before=4, after=4)

    # ── Experience ──
    experience = sections.get("experience", [])
    if experience:
        _section_heading(doc, "PROFESSIONAL EXPERIENCE")
        for item in experience:
            if not str(item).strip():
                continue
            item_str = str(item).strip()
            # If the line looks like a company/title header treat it as bold
            if _looks_like_header(item_str):
                p = doc.add_paragraph()
                _run(p, item_str, bold=True)
                _space(p, before=6, after=1)
            else:
                bullet = item_str.lstrip("•-– *").strip()
                p = doc.add_paragraph(bullet, style="List Bullet")
                _space(p, before=0, after=1)

    # ── Education ──
    education = sections.get("education", "")
    if education:
        _section_heading(doc, "EDUCATION")
        edu_text = education if isinstance(education, str) else "\n".join(education)
        for line in edu_text.splitlines():
            if line.strip():
                p = doc.add_paragraph(line.strip())
                _space(p, before=1, after=1)

    doc.save(output_path)


# ---------------------------------------------------------------------------
# Basic (no-AI) annotated copy
# ---------------------------------------------------------------------------

def _build_annotated_resume(
    original_path: str, results: dict, output_path: str
) -> None:
    ext = os.path.splitext(original_path)[1].lower()
    missing = results.get("missing_keywords", [])

    if ext == ".docx":
        doc = Document(original_path)
    else:
        # Build a simple text-based document from parsed paragraphs
        doc = Document()
        _set_margins(doc)
        _apply_normal_style(doc)
        for text in results["resume_data"].get("paragraphs", []):
            doc.add_paragraph(text)

    # Append keyword suggestions at the end
    if missing:
        doc.add_paragraph()
        note_p = doc.add_paragraph()
        _run(
            note_p,
            "── RESUME OPTIMIZER: KEYWORD SUGGESTIONS ──",
            bold=True, size=9, color=_C_NOTE,
        )
        doc.add_paragraph()

        intro = doc.add_paragraph()
        _run(
            intro,
            (
                "The following keywords appear in the job description but were "
                "NOT found in your resume. Review each one and add it to the "
                "relevant section ONLY if it truthfully describes your experience:"
            ),
            size=9, color=_C_NOTE,
        )

        for kw in missing:
            p = doc.add_paragraph(f"  • {kw}", style="List Bullet")
            for run in p.runs:
                run.font.size = Pt(9)
                run.font.color.rgb = _C_NOTE

        remind = doc.add_paragraph()
        _run(
            remind,
            (
                "Add your OpenAI API key in the app's Step 3 to have AI "
                "automatically incorporate these keywords for you."
            ),
            size=9, italic=True, color=_C_NOTE,
        )

    doc.save(output_path)


# ---------------------------------------------------------------------------
# Document-style helpers
# ---------------------------------------------------------------------------

_C_HEADING = RGBColor(0x1A, 0x1A, 0x2E)   # dark navy
_C_SUB     = RGBColor(0x55, 0x55, 0x55)   # grey
_C_ACCENT  = RGBColor(0x20, 0x5D, 0x99)   # blue accent for rule
_C_NOTE    = RGBColor(0xAA, 0x44, 0x00)   # amber – annotation text


def _set_margins(doc: Document, margin_in: float = 0.85) -> None:
    for section in doc.sections:
        m = Inches(margin_in)
        section.top_margin = m
        section.bottom_margin = m
        section.left_margin = m
        section.right_margin = m


def _apply_normal_style(doc: Document) -> None:
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10.5)


def _run(
    para,
    text: str,
    size: float = 10.5,
    bold: bool = False,
    italic: bool = False,
    color: RGBColor | None = None,
) -> None:
    r = para.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    if color:
        r.font.color.rgb = color


def _space(para, before: float = 4, after: float = 4) -> None:
    fmt = para.paragraph_format
    fmt.space_before = Pt(before)
    fmt.space_after  = Pt(after)
    fmt.line_spacing = Pt(14)


def _section_heading(doc: Document, text: str):
    p = doc.add_paragraph()
    _space(p, before=10, after=3)
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(11.5)
    r.font.bold = True
    r.font.color.rgb = _C_HEADING
    _add_bottom_border(p)
    return p


def _rule(doc: Document) -> None:
    p = doc.add_paragraph()
    _space(p, before=2, after=2)
    _add_bottom_border(p, color="2059a0", width="12")


def _add_bottom_border(
    para, color: str = "1a1a2e", width: str = "6"
) -> None:
    pPr = para._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    pPr.append(pBdr)
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), width)
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), color)
    pBdr.append(bottom)


# ---------------------------------------------------------------------------
# Small text-classification helpers
# ---------------------------------------------------------------------------

def _looks_like_contact(text: str) -> bool:
    """Heuristic: does this line look like a phone/email/LinkedIn entry?"""
    import re
    patterns = [
        r"@",           # email
        r"\d{3}[-.\s]\d{3}[-.\s]\d{4}",  # US phone
        r"linkedin\.com",
        r"github\.com",
        r"http[s]?://",
    ]
    return any(re.search(p, text, re.I) for p in patterns)


def _looks_like_header(text: str) -> bool:
    """Heuristic: short line that seems to be a company/title header."""
    if len(text) > 100:
        return False
    separators = ["|", "–", "—", "-", ",", "•"]
    has_sep = any(s in text for s in separators)
    words = text.split()
    caps = sum(1 for w in words if w and w[0].isupper())
    return has_sep or (len(words) <= 8 and caps / max(len(words), 1) >= 0.6)
