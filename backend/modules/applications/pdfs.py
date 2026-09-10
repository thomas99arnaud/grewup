"""PDF CV ATS-friendly : Times New Roman, A4, 15 mm, une colonne, pas de tableaux."""

from __future__ import annotations

import base64
import io
import os
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer

INK = HexColor("#000000")
MARGIN = 15 * mm

SECTION_ALIASES = {
    "EXPERIENCES PROFESSIONNELLES": "experience",
    "EXPERIENCE PROFESSIONNELLE": "experience",
    "PROFESSIONAL EXPERIENCE": "experience",
    "FORMATION": "education",
    "EDUCATION": "education",
    "COMPETENCES & LANGUES": "skills",
    "COMPETENCES ET LANGUES": "skills",
    "SKILLS & LANGUAGES": "skills",
    "SKILLS AND LANGUAGES": "skills",
    "PROJETS ET CENTRES D INTERET": "interests",
    "PROJETS ET CENTRES D'INTERET": "interests",
    "PROJECTS & INTERESTS": "interests",
    "PROJECTS AND INTERESTS": "interests",
}

SKILL_PREFIXES = (
    "langages",
    "ia / data",
    "ia/data",
    "backend",
    "infrastructure",
    "langues",
    "languages",
    "projets et centres",
    "projects & interests",
    "projects and interests",
)


@lru_cache(maxsize=1)
def _font_names() -> tuple[str, str, str]:
    """Times New Roman du système, sinon Times intégré."""
    fonts = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    files = {
        "TimesNewRoman": fonts / "times.ttf",
        "TimesNewRoman-Bold": fonts / "timesbd.ttf",
        "TimesNewRoman-Italic": fonts / "timesi.ttf",
    }
    if all(path.exists() for path in files.values()):
        for name, path in files.items():
            pdfmetrics.registerFont(TTFont(name, str(path)))
        return "TimesNewRoman", "TimesNewRoman-Bold", "TimesNewRoman-Italic"
    return "Times-Roman", "Times-Bold", "Times-Italic"


def _norm_section(line: str) -> str:
    folded = unicodedata.normalize("NFKD", line)
    folded = "".join(ch for ch in folded if not unicodedata.combining(ch))
    folded = folded.upper().replace("&", "AND")
    folded = re.sub(r"[^A-Z0-9 ]+", " ", folded)
    return re.sub(r"\s+", " ", folded).strip()


def _section_kind(line: str) -> str | None:
    return SECTION_ALIASES.get(_norm_section(line))


def _winansi(text: str) -> str:
    repl = {
        "\u2019": "'",
        "\u2018": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "–",
        "\u2014": "–",
        "\u2022": "-",
        "\u2192": "→",
        "\u00a0": " ",
        "œ": "oe",
        "Œ": "OE",
        "…": "...",
    }
    out = []
    for ch in text:
        ch = repl.get(ch, ch)
        try:
            ch.encode("cp1252")
            out.append(ch)
        except UnicodeEncodeError:
            out.append(unicodedata.normalize("NFKD", ch).encode("ascii", "ignore").decode() or " ")
    return "".join(out)


def _p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(_winansi(text)).replace("\n", "<br/>"), style)


def _line(left: str, right: str, left_role: str, style: ParagraphStyle) -> Paragraph:
    """Une seule ligne texte (ATS) : gras ou italique à gauche, lieu/dates à droite du tiret."""
    left_html = escape(_winansi(left))
    right_html = escape(_winansi(right))
    if left_role == "bold":
        left_html = f"<b>{left_html}</b>"
    elif left_role == "italic":
        left_html = f"<i>{left_html}</i>"
    return Paragraph(f"{left_html} – {right_html}", style)


def _styles() -> dict[str, ParagraphStyle]:
    roman, bold, _italic = _font_names()
    return {
        "name": ParagraphStyle(
            "cvName",
            fontName=bold,
            fontSize=12,
            leading=15,
            textColor=INK,
            alignment=TA_LEFT,
            spaceAfter=1,
        ),
        "contact": ParagraphStyle(
            "cvContact",
            fontName=roman,
            fontSize=12,
            leading=15,
            textColor=INK,
            alignment=TA_LEFT,
            spaceAfter=8,
        ),
        "pitch": ParagraphStyle(
            "cvPitch",
            fontName=roman,
            fontSize=11,
            leading=14,
            textColor=INK,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
        ),
        "section": ParagraphStyle(
            "cvSection",
            fontName=bold,
            fontSize=12,
            leading=15,
            textColor=INK,
            spaceBefore=8,
            spaceAfter=4,
        ),
        "org": ParagraphStyle(
            "cvOrg",
            fontName=roman,
            fontSize=11,
            leading=14,
            textColor=INK,
            spaceAfter=0,
        ),
        "role": ParagraphStyle(
            "cvRole",
            fontName=roman,
            fontSize=11,
            leading=14,
            textColor=INK,
            spaceAfter=2,
        ),
        "intro": ParagraphStyle(
            "cvIntro",
            fontName=roman,
            fontSize=11,
            leading=13.5,
            textColor=INK,
            alignment=TA_JUSTIFY,
            spaceBefore=2,
            spaceAfter=1,
        ),
        "bullet": ParagraphStyle(
            "cvBullet",
            fontName=roman,
            fontSize=11,
            leading=13.5,
            textColor=INK,
            alignment=TA_JUSTIFY,
            leftIndent=14,
            firstLineIndent=-10,
            spaceBefore=0.4,
            spaceAfter=0.4,
        ),
        "skill": ParagraphStyle(
            "cvSkill",
            fontName=bold,
            fontSize=11,
            leading=13.5,
            textColor=INK,
            alignment=TA_JUSTIFY,
            spaceAfter=2,
        ),
        "body": ParagraphStyle(
            "cvBody",
            fontName=roman,
            fontSize=11,
            leading=13.5,
            textColor=INK,
            alignment=TA_JUSTIFY,
            spaceAfter=2,
        ),
        "letterName": ParagraphStyle(
            "lmName",
            fontName=bold,
            fontSize=12,
            leading=15,
            textColor=INK,
            spaceAfter=2,
        ),
        "letterMeta": ParagraphStyle(
            "lmMeta",
            fontName=roman,
            fontSize=11,
            leading=14.5,
            textColor=INK,
            spaceAfter=2,
        ),
        "letterBody": ParagraphStyle(
            "lmBody",
            fontName=roman,
            fontSize=11,
            leading=15,
            textColor=INK,
            alignment=TA_JUSTIFY,
            spaceAfter=10,
        ),
    }


def _split_left_right(line: str) -> tuple[str, str] | None:
    for sep in (" — ", " – ", " - ", "\t"):
        if sep in line:
            left, right = line.split(sep, 1)
            if left.strip() and right.strip():
                return left.strip(), right.strip()
    return None


def _is_bullet(line: str) -> bool:
    return bool(re.match(r"^([\-\u2013\u2014\u2022*]|o)\s+", line.strip()))


def _bullet_text(line: str) -> str:
    return re.sub(r"^([\-\u2013\u2014\u2022*]|o)\s+", "", line.strip())


def _looks_like_dates(text: str) -> bool:
    return bool(re.search(r"(19|20)\d{2}|auj|present|aujourd", text, re.I))


def _is_skill_line(line: str) -> bool:
    head = line.split(":", 1)[0].strip().lower()
    return any(head.startswith(prefix) for prefix in SKILL_PREFIXES)


def _cv_story(text: str, styles: dict[str, ParagraphStyle]) -> list:
    lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").split("\n")]
    while lines and not lines[0].strip():
        lines.pop(0)
    if not lines:
        return [_p("(CV vide)", styles["body"])]

    story: list = []
    story.append(_p(lines[0].strip(), styles["name"]))
    idx = 1
    if idx < len(lines) and ("|" in lines[idx] or "@" in lines[idx]):
        contact = lines[idx].strip()
        if contact.startswith("|"):
            contact = contact
        story.append(_p(contact, styles["contact"]))
        idx += 1

    pitch: list[str] = []
    while idx < len(lines) and not _section_kind(lines[idx].strip()):
        if lines[idx].strip():
            pitch.append(lines[idx].strip())
        idx += 1
    if pitch:
        story.append(_p(" ".join(pitch), styles["pitch"]))

    current_kind: str | None = None
    block: list = []

    def flush_block() -> None:
        nonlocal block
        if block:
            story.append(KeepTogether(block))
            block = []

    def add_section(title: str) -> None:
        flush_block()
        story.append(_p(title.upper(), styles["section"]))

    while idx < len(lines):
        stripped = lines[idx].strip()
        idx += 1
        if not stripped:
            flush_block()
            continue
        kind = _section_kind(stripped)
        if kind:
            add_section(stripped)
            current_kind = kind
            continue
        if _is_bullet(stripped):
            target = block if block else story
            target.append(_p(f"- {_bullet_text(stripped)}", styles["bullet"]))
            continue
        pair = _split_left_right(stripped)
        if pair:
            left, right = pair
            if _looks_like_dates(right):
                block.append(_line(left, right, "italic", styles["role"]))
            else:
                if current_kind in {"experience", "education"} and block:
                    flush_block()
                block.append(_line(left, right, "bold", styles["org"]))
            continue
        target = block if block else story
        if current_kind == "skills" and _is_skill_line(stripped):
            target.append(_p(stripped, styles["skill"]))
        elif current_kind == "experience":
            target.append(_p(stripped, styles["intro"]))
        else:
            target.append(_p(stripped, styles["body"]))
    flush_block()
    return story


def _letter_story(text: str, styles: dict[str, ParagraphStyle]) -> list:
    chunks = [c.strip() for c in re.split(r"\n\s*\n", text.replace("\r\n", "\n")) if c.strip()]
    if not chunks:
        return [_p("(Lettre vide)", styles["letterBody"])]
    story: list = []
    header_done = False
    name_re = re.compile(r"^thomas\s+arnaud\.?$", re.I)

    def emit_signature(lines: list[str]):
        if len(lines) >= 2 and name_re.match(lines[-1]):
            return lines[:-1], lines[-1]
        return lines, None

    for i, chunk in enumerate(chunks):
        lines = [ln.strip() for ln in chunk.split("\n") if ln.strip()]
        body_lines, signature = emit_signature(lines)
        joined = " ".join(body_lines)
        is_header = i == 0 or (
            not header_done
            and (
                joined.upper().startswith("THOMAS")
                or joined.lower().startswith("a l'attention")
                or joined.lower().startswith("à l'attention")
                or joined.lower().startswith("objet")
            )
        )
        if is_header and i < 6:
            style = styles["letterName"] if i == 0 else styles["letterMeta"]
            for line in body_lines:
                story.append(_p(line, style))
            if signature:
                story.append(Spacer(1, 10))
                story.append(_p(signature, styles["letterName"]))
            story.append(Spacer(1, 8))
            if joined.lower().startswith("objet") or "madame" in joined.lower():
                header_done = True
            continue
        header_done = True
        if body_lines:
            story.append(_p(joined, styles["letterBody"]))
        if signature:
            story.append(Spacer(1, 8))
            story.append(_p(signature, styles["letterName"]))
    return story


def _build_pdf(story: list) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title="Thomas ARNAUD",
        author="Thomas ARNAUD",
    )
    doc.build(story)
    return buffer.getvalue()


def _slug(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value)
    folded = "".join(ch for ch in folded if not unicodedata.combining(ch))
    folded = re.sub(r"[^A-Za-z0-9]+", "_", folded).strip("_")
    return folded[:48] or "offre"


def render_application_pdfs(
    cv_text: str,
    letter_text: str,
    job_title: str = "",
    company: str = "",
) -> dict[str, str]:
    styles = _styles()
    cv_pdf = _build_pdf(_cv_story(cv_text, styles))
    letter_pdf = _build_pdf(_letter_story(letter_text, styles))
    suffix = _slug("_".join(part for part in (job_title, company) if part))
    return {
        "cv_pdf_base64": base64.b64encode(cv_pdf).decode("ascii"),
        "letter_pdf_base64": base64.b64encode(letter_pdf).decode("ascii"),
        "cv_filename": f"CV_Thomas_ARNAUD_{suffix}.pdf",
        "letter_filename": f"LM_Thomas_ARNAUD_{suffix}.pdf",
    }
