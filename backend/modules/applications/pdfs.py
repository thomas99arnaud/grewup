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
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

INK = HexColor("#000000")
MUTED = HexColor("#4b4b4b")
MARGIN = 15 * mm
PAGE_WIDTH = A4[0] - 2 * MARGIN

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


def _spread(left: Paragraph, right: Paragraph) -> Table:
    table = Table([[left, right]], colWidths=[PAGE_WIDTH * 0.66, PAGE_WIDTH * 0.34])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]
        )
    )
    return table


def _styles() -> dict[str, ParagraphStyle]:
    roman, bold, italic = _font_names()
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
            fontSize=11,
            leading=14,
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
            spaceAfter=6,
        ),
        "section": ParagraphStyle(
            "cvSection",
            fontName=bold,
            fontSize=12,
            leading=15,
            textColor=INK,
            spaceBefore=10,
            spaceAfter=2,
        ),
        "org": ParagraphStyle(
            "cvOrg",
            fontName=bold,
            fontSize=11.5,
            leading=14,
            textColor=INK,
            spaceAfter=0,
        ),
        "place": ParagraphStyle(
            "cvPlace",
            fontName=roman,
            fontSize=10,
            leading=13,
            textColor=MUTED,
            alignment=TA_RIGHT,
            spaceAfter=0,
        ),
        "role": ParagraphStyle(
            "cvRole",
            fontName=italic,
            fontSize=11,
            leading=13.5,
            textColor=INK,
            spaceAfter=0,
        ),
        "dates": ParagraphStyle(
            "cvDates",
            fontName=roman,
            fontSize=10,
            leading=13,
            textColor=MUTED,
            alignment=TA_RIGHT,
            spaceAfter=0,
        ),
        "intro": ParagraphStyle(
            "cvIntro",
            fontName=roman,
            fontSize=10.5,
            leading=13.5,
            textColor=INK,
            alignment=TA_JUSTIFY,
            spaceBefore=5,
            spaceAfter=1,
        ),
        "bullet": ParagraphStyle(
            "cvBullet",
            fontName=roman,
            fontSize=10.5,
            leading=13.5,
            textColor=INK,
            alignment=TA_JUSTIFY,
            leftIndent=16,
            firstLineIndent=-10,
            spaceBefore=0.6,
            spaceAfter=0.6,
        ),
        "skill": ParagraphStyle(
            "cvSkill",
            fontName=bold,
            fontSize=10.5,
            leading=13.5,
            textColor=INK,
            alignment=TA_JUSTIFY,
            spaceAfter=2,
        ),
        "body": ParagraphStyle(
            "cvBody",
            fontName=roman,
            fontSize=10.5,
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


_MONTHS = {
    "janvier": 1,
    "january": 1,
    "jan": 1,
    "fevrier": 2,
    "février": 2,
    "february": 2,
    "feb": 2,
    "mars": 3,
    "march": 3,
    "mar": 3,
    "avril": 4,
    "april": 4,
    "apr": 4,
    "mai": 5,
    "may": 5,
    "juin": 6,
    "june": 6,
    "jun": 6,
    "juillet": 7,
    "july": 7,
    "jul": 7,
    "aout": 8,
    "août": 8,
    "august": 8,
    "aug": 8,
    "septembre": 9,
    "september": 9,
    "sep": 9,
    "octobre": 10,
    "october": 10,
    "oct": 10,
    "novembre": 11,
    "november": 11,
    "nov": 11,
    "decembre": 12,
    "décembre": 12,
    "december": 12,
    "dec": 12,
}


def _fold_dates(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text or "")
    folded = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return folded.lower()


def _block_recency(text: str) -> tuple[int, int, int, int]:
    """Plus le tuple est grand, plus le poste est récent."""
    folded = _fold_dates(text)
    if re.search(r"aujourd|auj\.?|present|current|now", folded):
        return (9999, 12, 9999, 12)
    found: list[tuple[int, int]] = []
    month_re = (
        r"(janvier|fevrier|mars|avril|mai|juin|juillet|aout|septembre|octobre|novembre|decembre|"
        r"january|february|march|april|may|june|july|august|september|october|november|december|"
        r"jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)"
    )
    for match in re.finditer(month_re + r"\s+((?:19|20)\d{2})", folded):
        found.append((int(match.group(2)), _MONTHS.get(match.group(1), 1)))
    if not found:
        for match in re.finditer(r"(19|20)\d{2}", folded):
            found.append((int(match.group(0)), 12))
    if not found:
        return (0, 0, 0, 0)
    end = max(found)
    start = min(found)
    return (end[0], end[1], start[0], start[1])


def _experience_blocks(lines: list[str]) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current:
                current.append("")
            continue
        pair = _split_left_right(stripped)
        new_org = bool(pair and not _looks_like_dates(pair[1]) and any(x.strip() for x in current))
        if new_org:
            while current and not current[-1].strip():
                current.pop()
            blocks.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        while current and not current[-1].strip():
            current.pop()
        blocks.append(current)
    return [block for block in blocks if any(x.strip() for x in block)]


def order_cv_text(text: str) -> str:
    """Met les expériences du plus récent au plus ancien."""
    lines = [ln.rstrip() for ln in (text or "").replace("\r\n", "\n").split("\n")]
    out: list[str] = []
    i = 0
    while i < len(lines):
        kind = _section_kind(lines[i].strip()) if lines[i].strip() else None
        out.append(lines[i])
        i += 1
        if kind != "experience":
            continue
        start = i
        while i < len(lines) and not _section_kind(lines[i].strip()):
            i += 1
        body = lines[start:i]
        while body and not body[0].strip():
            body.pop(0)
        trailing_blanks = 0
        while body and not body[-1].strip():
            body.pop()
            trailing_blanks += 1
        blocks = _experience_blocks(body)
        blocks.sort(key=lambda block: _block_recency("\n".join(block)), reverse=True)
        joined: list[str] = []
        for idx, block in enumerate(blocks):
            if idx:
                joined.append("")
            joined.extend(block)
        if not joined:
            joined = body
        out.append("")
        out.extend(joined)
        if trailing_blanks:
            out.append("")
    return "\n".join(out)


def _section_rule() -> HRFlowable:
    return HRFlowable(
        width=PAGE_WIDTH,
        thickness=0.7,
        color=INK,
        spaceBefore=0,
        spaceAfter=8,
    )


def _is_skill_line(line: str) -> bool:
    head = line.split(":", 1)[0].strip().lower()
    return any(head.startswith(prefix) for prefix in SKILL_PREFIXES)


def _cv_story(text: str, styles: dict[str, ParagraphStyle]) -> list:
    lines = [ln.rstrip() for ln in order_cv_text(text).replace("\r\n", "\n").split("\n")]
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
        story.append(_section_rule())

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
                block.append(
                    _spread(_p(left, styles["role"]), _p(right, styles["dates"]))
                )
            else:
                if current_kind in {"experience", "education"} and block:
                    flush_block()
                block.append(
                    _spread(_p(left, styles["org"]), _p(right, styles["place"]))
                )
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


def _build_pdf(story: list, title: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title=title,
        author="Thomas ARNAUD",
    )
    doc.build(story)
    return buffer.getvalue()


def _slug(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value)
    folded = "".join(ch for ch in folded if not unicodedata.combining(ch))
    folded = re.sub(r"[^A-Za-z0-9]+", "_", folded).strip("_")
    return folded[:40]


def _professional_filenames(job_title: str, company: str) -> tuple[str, str]:
    bits = ["Thomas_ARNAUD"]
    if job_title.strip():
        bits.append(_slug(job_title))
    if company.strip():
        bits.append(_slug(company))
    stem = "_".join(part for part in bits if part)
    return f"{stem}_CV.pdf", f"{stem}_Lettre_de_motivation.pdf"


def render_application_pdfs(
    cv_text: str,
    letter_text: str,
    job_title: str = "",
    company: str = "",
) -> dict[str, str]:
    styles = _styles()
    cv_title = " – ".join(part for part in ("Thomas ARNAUD", "CV", job_title.strip()) if part)
    letter_title = " – ".join(
        part for part in ("Thomas ARNAUD", "Lettre de motivation", job_title.strip()) if part
    )
    cv_pdf = _build_pdf(_cv_story(cv_text, styles), cv_title)
    letter_pdf = _build_pdf(_letter_story(letter_text, styles), letter_title)
    cv_filename, letter_filename = _professional_filenames(job_title, company)
    return {
        "cv_pdf_base64": base64.b64encode(cv_pdf).decode("ascii"),
        "letter_pdf_base64": base64.b64encode(letter_pdf).decode("ascii"),
        "cv_filename": cv_filename,
        "letter_filename": letter_filename,
    }
