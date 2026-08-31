"""Charge le suivi Word et le compacte pour le LLM (relecture à chaque modification)."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from backend.core.config import settings

MODULE_DIR = Path(__file__).resolve().parent
DEFAULT_DOCX = MODULE_DIR / "suivi-competences.docx"
DEFAULT_MD = MODULE_DIR / "dossier.md"

_YEAR = re.compile(r"\b(?:19|20)\d{2}\b")
_PARENS = re.compile(r"\([^)]*\)")
_PROJECT = re.compile(
    r"\b(projet|projets|mandat\s*:|réalisation|tp\s*:|contribution\s*:)",
    re.IGNORECASE,
)
_GENERIC_PART = re.compile(
    r"^(cours|td|colles|ds|tp|python|c|java|lisp|prolog|compte rendu|"
    r"projets|présentations(?: orales)?|pitchs|présentations, pitchs)$",
    re.IGNORECASE,
)


def _norm(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text.replace("\xa0", " ")).strip()


def _first_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _right_parts(right: str) -> list[str]:
    return [p.strip() for p in re.split(r"[,;/]", right) if p.strip()]


def _is_generic_tools(right: str) -> bool:
    parts = _right_parts(right)
    if not parts:
        return True
    return all(_GENERIC_PART.match(p) for p in parts)


def _is_parent(left: str, right: str) -> bool:
    if _YEAR.search(right):
        return True
    lines = [ln.strip() for ln in left.splitlines() if ln.strip()]
    if len(lines) >= 2 and lines[1].lower().startswith("contexte"):
        return True
    return False


def _course_label(title: str) -> str:
    label = _PARENS.sub(" ", title)
    label = re.split(r"\s[:–—]\s", label, maxsplit=1)[0]
    return _norm(label)[:80]


def _is_course_row(left: str, right: str) -> bool:
    """Matière / titre de cours sans récit de projet — à fusionner."""
    if not left or _is_parent(left, right):
        return False
    if _PROJECT.search(left):
        return False
    if not _is_generic_tools(right):
        return False
    stripped = _norm(_PARENS.sub(" ", left))
    if stripped.endswith("."):
        return False
    return len(stripped) <= 80 and stripped.count(".") == 0


def compact_rows(rows: list[tuple[str, str]]) -> str:
    """Transforme le tableau (gauche, droite) en fiche compacte pour le LLM."""
    lines: list[str] = [
        "# Dossier candidat — Thomas Arnaud",
        "",
        "Source : tableau Word de suivi de compétences. Ne rien inventer au-delà.",
        "",
    ]
    current_courses: list[str] = []

    def flush_courses() -> None:
        nonlocal current_courses
        if not current_courses:
            return
        # Dédupliquer en gardant l'ordre
        seen: set[str] = set()
        unique: list[str] = []
        for title in current_courses:
            key = title.lower()
            if key not in seen:
                seen.add(key)
                unique.append(title)
        lines.append("Matières (ne pas lister une par une sur un CV) : " + " ; ".join(unique))
        lines.append("")
        current_courses = []

    def emit_parent(left: str, right: str) -> None:
        title = _first_line(left)
        body_lines = [ln.strip() for ln in left.splitlines() if ln.strip()]
        rest = body_lines[1:] if body_lines else []
        lines.append(f"## {title}")
        if right:
            lines.append(right)
        if rest:
            lines.append("\n".join(rest))
        lines.append("")

    def emit_fact(left: str, right: str) -> None:
        body = _norm(left)
        if not body:
            return
        lines.append(f"- {body}")
        if right and right.lower() not in body.lower():
            lines.append(f"  Outils : {right}")
        lines.append("")

    for left_raw, right_raw in rows:
        left = left_raw.strip()
        right = right_raw.strip()
        if not left and not right:
            continue
        if _is_parent(left, right):
            flush_courses()
            emit_parent(left, right)
            continue
        if _is_course_row(left, right):
            current_courses.append(_course_label(_first_line(left)))
            continue
        flush_courses()
        emit_fact(left, right)

    flush_courses()
    return "\n".join(lines).strip() + "\n"


def _table_rows(docx_path: Path) -> list[tuple[str, str]]:
    try:
        from docx import Document
    except ImportError as exc:
        raise ImportError(
            "python-docx est requis pour lire le suivi Word. "
            "Installe-le dans le venv : pip install python-docx"
        ) from exc

    table = Document(str(docx_path)).tables[0]
    rows: list[tuple[str, str]] = []
    for row in table.rows:
        left = row.cells[0].text.strip()
        right = row.cells[1].text.strip() if len(row.cells) > 1 else ""
        rows.append((left, right))
    return rows


@lru_cache(maxsize=4)
def _compact_from_docx_cached(path_str: str, mtime_ns: int, size: int) -> str:
    rows = _table_rows(Path(path_str))
    return compact_rows(rows)


def _resolve_path() -> Path:
    configured = (settings.candidate_dossier_path or "").strip()
    path = Path(configured) if configured else DEFAULT_DOCX
    if path.exists():
        return path
    if DEFAULT_DOCX.exists() and path != DEFAULT_DOCX:
        return DEFAULT_DOCX
    if DEFAULT_MD.exists():
        return DEFAULT_MD
    raise FileNotFoundError(
        f"Suivi de compétences introuvable : {path}. "
        "Place suivi-competences.docx dans backend/modules/applications/ "
        "ou renseigne CANDIDATE_DOSSIER_PATH."
    )


def load_dossier() -> str:
    """Relit le Word dès qu'il change (mtime) ; compacte les listes de cours."""
    path = _resolve_path()
    if path.suffix.lower() == ".docx":
        stat = path.stat()
        return _compact_from_docx_cached(str(path.resolve()), stat.st_mtime_ns, stat.st_size)
    return path.read_text(encoding="utf-8")
