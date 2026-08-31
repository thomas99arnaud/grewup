"""PDF CV + lettre au format des documents Word de Thomas (Times, bleu 2F5496, A4)."""

from __future__ import annotations

import base64
import io
import re
import unicodedata
from xml.sax.saxutils import escape

from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

NAVY = HexColor("#2F5496")
INK = HexColor("#272727")
MUTED = HexColor("#595959")
RULE = HexColor("#2F5496")

MARGIN = 16 * mm

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
        "\u2013": "-",
        "\u2014": "-",
        "\u2022": "-",
        "\u2192": "->",
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


def _styles() -> dict[str, ParagraphStyle]:
    return {
        "name": ParagraphStyle(
            "cvName",
            fontName="Times-Bold",
            fontSize=16,
            leading=20,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=2,
        ),
        "contact": ParagraphStyle(
            "cvContact",
            fontName="Times-Roman",
            fontSize=10,
            leading=13,
            textColor=MUTED,
            alignment=TA_LEFT,
            spaceAfter=8,
        ),
        "pitch": ParagraphStyle(
            "cvPitch",
            fontName="Times-Roman",
            fontSize=10.5,
            leading=14,
            textColor=INK,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
        ),
        "section": ParagraphStyle(
            "cvSection",
            fontName="Times-Bold",
            fontSize=11.5,
            leading=14,
            textColor=NAVY,
            spaceBefore=10,
            spaceAfter=3,
        ),
        "leftBold": ParagraphStyle(
            "cvLeftBold",
            fontName="Times-Bold",
            fontSize=10.5,
            leading=13,
            textColor=INK,
        ),
        "right": ParagraphStyle(
            "cvRight",
            fontName="Times-Italic",
            fontSize=10.5,
            leading=13,
            textColor=MUTED,
            alignment=TA_RIGHT,
        ),
        "left": ParagraphStyle(
            "cvLeft",
            fontName="Times-Roman",
            fontSize=10.5,
            leading=13,
            textColor=INK,
        ),
        "intro": ParagraphStyle(
            "cvIntro",
            fontName="Times-Italic",
            fontSize=10.5,
            leading=13.5,
            textColor=INK,
            spaceBefore=1,
            spaceAfter=1,
        ),
        "bullet": ParagraphStyle(
            "cvBullet",
            fontName="Times-Roman",
            fontSize=10.5,
            leading=13.5,
            textColor=INK,
            leftIndent=12,
            bulletIndent=0,
            spaceBefore=0.5,
            spaceAfter=0.5,
        ),
        "body": ParagraphStyle(
            "cvBody",
            fontName="Times-Roman",
            fontSize=10.5,
            leading=14,
            textColor=INK,
            spaceAfter=3,
        ),
        "letterName": ParagraphStyle(
            "lmName",
            fontName="Times-Bold",
            fontSize=13,
            leading=16,
            textColor=INK,
            spaceAfter=2,
        ),
        "letterMeta": ParagraphStyle(
            "lmMeta",
            fontName="Times-Roman",
            fontSize=11,
            leading=14.5,
            textColor=INK,
            spaceAfter=2,
        ),
        "letterBody": ParagraphStyle(
            "lmBody",
            fontName="Times-Roman",
            fontSize=11,
            leading=15.5,
            textColor=INK,
            alignment=TA_JUSTIFY,
            spaceAfter=10,
        ),
    }


def _pair_row(left: str, right: str, styles: dict[str, ParagraphStyle], left_bold: bool) -> Table:
    left_style = styles["leftBold"] if left_bold else styles["left"]
    table = Table(
        [[_p(left, left_style), _p(right, styles["right"])]],
        colWidths=[120 * mm, 58 * mm],
    )
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ("BACKGROUND", (0, 0), (-1, -1), white),
            ]
        )
    )
    return table


def _split_left_right(line: str) -> tuple[str, str] | None:
    for sep in (" — ", " – ", " - ", "\t"):
        if sep in line:
            left, right = line.split(sep, 1)
            if left.strip() and right.strip():
                return left.strip(), right.strip()
    return None


def _is_bullet(line: str) -> bool:
    return bool(re.match(r"^([\-\u2013\u2014\u2022]|o)\s+", line.strip()))


def _bullet_text(line: str) -> str:
    return re.sub(r"^([\-\u2013\u2014\u2022]|o)\s+", "", line.strip())


def _looks_like_dates(text: str) -> bool:
    return bool(re.search(r"(19|20)\d{2}|auj|present|aujourd", text, re.I))


def _cv_story(text: str, styles: dict[str, ParagraphStyle]) -> list:
    lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").split("\n")]
    while lines and not lines[0].strip():
        lines.pop(0)
    if not lines:
        return [_p("(CV vide)", styles["body"])]

    story: list = []
    story.append(_p(lines[0].strip(), styles["name"]))
    idx = 1
    if idx < len(lines) and lines[idx].strip().startswith("|"):
        story.append(_p(lines[idx].strip().lstrip("| ").replace("|", " · "), styles["contact"]))
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
        story.append(
            HRFlowable(width="100%", thickness=0.8, color=RULE, spaceBefore=0, spaceAfter=6)
        )

    while idx < len(lines):
        raw = lines[idx]
        stripped = raw.strip()
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
            target.append(_p(f"• {_bullet_text(stripped)}", styles["bullet"]))
            continue
        pair = _split_left_right(stripped)
        if pair:
            left, right = pair
            flush_block()
            bold = not _looks_like_dates(right) or current_kind == "education"
            if _looks_like_dates(right) and current_kind == "experience":
                bold = False
            block.append(_pair_row(left, right, styles, left_bold=bold))
            continue
        target = block if block else story
        if current_kind == "experience" and not _is_bullet(stripped):
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

    def emit_signature(lines: list[str]) -> list[str]:
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
