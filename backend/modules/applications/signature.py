"""Signature de CV : mêmes règles de sélection que le prompt, sans LLM."""

from __future__ import annotations

import re
import unicodedata

BLOCK_IAS_RAG = "ias_rag"
BLOCK_IAS_CONFIG = "ias_config"
BLOCK_MTQ = "mtq"

BLOCK_LABELS = {
    BLOCK_IAS_RAG: "IAS RAG",
    BLOCK_IAS_CONFIG: "IAS outil de configuration industrielle",
    BLOCK_MTQ: "MTQ",
}

ALL_PRO_BLOCKS = (BLOCK_IAS_RAG, BLOCK_IAS_CONFIG, BLOCK_MTQ)

_RAG = (
    "rag",
    "llm",
    "chatbot",
    "langchain",
    "langgraph",
    "llama",
    "generative ai",
    "ia generative",
    "ia générative",
    "gpt",
    "huggingface",
    "embedding",
    "vectoriel",
    "retrieval",
    "large language",
)
_DATA_GEO = (
    "transport",
    "mobilite",
    "mobilité",
    "geo",
    "géo",
    "geospatial",
    "géospatial",
    "osrm",
    "itineraire",
    "itinéraire",
    "cyclist",
    "data analyst",
    "data scientist",
    "data engineer",
    "enquete od",
    "enquête od",
    "graphe routier",
    "modelisation des deplacements",
    "modélisation des déplacements",
)
_DOTNET = (
    ".net",
    "c#",
    "csharp",
    " mes ",
    "versioning",
    "industriel",
    "industrielle",
    "configuration industrielle",
    " iis ",
    "active directory",
    "asp.net",
)
_INTL = (
    " vie ",
    "canada",
    "montreal",
    "montréal",
    "quebec",
    "québec",
    "international",
    "abroad",
    "overseas",
)

_KNOWN_SKILLS = (
    "Python",
    "C#",
    "SQL",
    "C",
    "RAG",
    "LangChain",
    "LangGraph",
    "Docker",
    ".NET",
    "API REST",
    "Git",
    "CI/CD",
    "IIS",
    "PostgreSQL",
    "Azure DevOps",
    "Streamlit",
    "OSRM",
    "ChromaDB",
    "Active Directory",
    "CUDA",
)

_SKILL_HEADINGS = ("competences", "compétences", "skills")


def _fold(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text or "")
    folded = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return f" {folded.lower()} "


def _hits(haystack: str, needles: tuple[str, ...]) -> int:
    return sum(1 for needle in needles if needle in haystack)


def detect_language(offer_text: str, hint: str | None = None) -> str:
    if hint in {"fr", "en"}:
        return hint
    text = _fold(offer_text)
    en = _hits(text, (" the ", " we ", " our ", " you ", " responsibilities", "looking for", "we're"))
    fr = _hits(text, (" nous ", " poste ", " votre ", " mission", " profil", "experience", "recherchons"))
    return "en" if en > fr else "fr"


def select_blocks(offer_text: str) -> list[str]:
    text = _fold(offer_text)
    rag = _hits(text, _RAG)
    data = _hits(text, _DATA_GEO)
    dotnet = _hits(text, _DOTNET)
    intl = _hits(text, _INTL)
    kept: list[str] = []

    hybrid = rag > 0 and dotnet > 0 and (data > 0 or intl > 0)
    if hybrid:
        kept.append(BLOCK_IAS_RAG)
        kept.append(BLOCK_IAS_CONFIG)
        if data > 0 or intl > 0:
            kept.append(BLOCK_MTQ)
    elif rag >= data and rag >= dotnet and rag > 0:
        kept.append(BLOCK_IAS_RAG)
        if data >= 2:
            kept.append(BLOCK_MTQ)
        if dotnet >= 2:
            kept.append(BLOCK_IAS_CONFIG)
    elif data >= dotnet and data > 0:
        kept.append(BLOCK_MTQ)
        if rag >= 2:
            kept.append(BLOCK_IAS_RAG)
    elif dotnet > 0:
        kept.append(BLOCK_IAS_CONFIG)
        if rag >= 2:
            kept.append(BLOCK_IAS_RAG)
        if intl > 0:
            kept.append(BLOCK_MTQ)
    elif intl > 0:
        kept.append(BLOCK_MTQ)
    else:
        kept.append(BLOCK_IAS_RAG)

    ordered = [block for block in ALL_PRO_BLOCKS if block in kept]
    return ordered or [BLOCK_IAS_RAG]


def cv_signature(offer_text: str, language: str | None = None) -> str:
    lang = detect_language(offer_text, language)
    blocks = select_blocks(offer_text)
    return f"{lang}|{'+'.join(blocks)}"


def block_labels(block_ids: list[str]) -> list[str]:
    return [BLOCK_LABELS.get(block, block) for block in block_ids]


def omitted_labels(kept_ids: list[str]) -> list[str]:
    return [BLOCK_LABELS[block] for block in ALL_PRO_BLOCKS if block not in kept_ids]


def guess_job_title(offer_text: str) -> str:
    for raw in (offer_text or "").splitlines():
        line = raw.strip()
        if 8 <= len(line) <= 90 and not line.lower().startswith("http"):
            return line[:90]
    return "Ingénieur logiciel"


def adapt_cv(cv_text: str, job_title: str, offer_text: str) -> str:
    """Retouche sans LLM : intitulé + ordre des compétences."""
    lines = (cv_text or "").replace("\r\n", "\n").split("\n")
    if not lines:
        return cv_text
    title = (job_title or "").strip() or guess_job_title(offer_text)
    first = lines[0]
    if re.search(r"\s+[–—-]\s+", first):
        name = re.split(r"\s+[–—-]\s+", first, maxsplit=1)[0].strip()
        lines[0] = f"{name} – {title}"
    else:
        lines[0] = f"Thomas ARNAUD – {title}"

    offer_fold = _fold(offer_text)
    in_skills = False
    for i, line in enumerate(lines):
        kind = unicodedata.normalize("NFKD", line.strip())
        kind_ascii = "".join(ch for ch in kind if not unicodedata.combining(ch)).lower()
        if any(head in kind_ascii for head in _SKILL_HEADINGS) and len(line.strip()) < 40:
            in_skills = True
            continue
        if in_skills and line.strip() and line.strip().isupper() and len(line.strip()) < 40:
            in_skills = False
            continue
        if in_skills and ":" in line:
            lines[i] = _reorder_skill_line(line, offer_fold)
    return "\n".join(lines)


def _reorder_skill_line(line: str, offer_fold: str) -> str:
    prefix, _, rest = line.partition(":")
    tokens = [tok.strip() for tok in rest.split(",") if tok.strip()]
    if len(tokens) < 2:
        return line
    matched, other = [], []
    for tok in tokens:
        needle = _fold(tok)
        hit = needle in offer_fold or any(
            _fold(skill) in needle and _fold(skill) in offer_fold for skill in _KNOWN_SKILLS
        )
        (matched if hit else other).append(tok)
    if not matched:
        return line
    return f"{prefix}: {', '.join(matched + other)}"
