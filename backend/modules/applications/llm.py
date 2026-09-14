import json
import re
from typing import Any

import httpx

from backend.core.config import settings

APPLICATION_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "job_title": {"type": "string"},
        "company": {"type": "string"},
        "language": {"type": "string"},
        "fit_summary": {"type": "string"},
        "emphasized_experiences": {"type": "array", "items": {"type": "string"}},
        "omitted_experiences": {"type": "array", "items": {"type": "string"}},
        "cv_markdown": {"type": "string"},
        "cover_letter": {"type": "string"},
    },
    "required": [
        "job_title",
        "company",
        "language",
        "fit_summary",
        "emphasized_experiences",
        "omitted_experiences",
        "cv_markdown",
        "cover_letter",
    ],
}

LETTER_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "job_title": {"type": "string"},
        "company": {"type": "string"},
        "language": {"type": "string"},
        "fit_summary": {"type": "string"},
        "cover_letter": {"type": "string"},
    },
    "required": [
        "job_title",
        "company",
        "language",
        "fit_summary",
        "cover_letter",
    ],
}


class LlmError(Exception):
    pass


def _uses_openrouter() -> bool:
    return "openrouter.ai" in settings.openai_base_url.lower()


def _auth_headers() -> dict[str, str]:
    key = settings.openai_api_key.strip()
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if _uses_openrouter():
        headers["HTTP-Referer"] = "http://localhost:5173"
        headers["X-Title"] = settings.app_name
        headers["X-OpenRouter-Title"] = settings.app_name
    return headers


def _message_text(message: dict[str, Any]) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                text = block.get("text") or block.get("content") or ""
                if isinstance(text, str):
                    parts.append(text)
        return "".join(parts)
    return ""


def parse_llm_json(raw: str) -> dict[str, Any]:
    """Accepte du JSON brut, un bloc ```json, ou du texte autour."""
    text = (raw or "").strip()
    if not text:
        raise json.JSONDecodeError("empty", raw or "", 0)
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, count=1, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        raise json.JSONDecodeError("no object", text, 0)
    data = json.loads(text[start : end + 1])
    if not isinstance(data, dict):
        raise json.JSONDecodeError("not an object", text, 0)
    return data


async def chat_json(
    system: str,
    user: str,
    *,
    schema: dict[str, Any] | None = None,
    require_cv: bool = True,
) -> dict[str, Any]:
    if not settings.openai_api_key:
        raise LlmError(
            "Clé API manquante. Ajoute OPENAI_API_KEY (ou OPENROUTER_API_KEY) dans .env "
            "à la racine du projet, sans guillemets, puis relance uvicorn."
        )

    url = settings.openai_base_url.rstrip("/") + "/chat/completions"
    if _uses_openrouter():
        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": system,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
            },
            {"role": "user", "content": user},
        ]
        used_schema = schema or APPLICATION_JSON_SCHEMA
        response_format: dict[str, Any] = {
            "type": "json_schema",
            "json_schema": {
                "name": "generated_application" if require_cv else "generated_letter",
                "strict": True,
                "schema": used_schema,
            },
        }
    else:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        response_format = {"type": "json_object"}

    payload = {
        "model": settings.openai_model,
        "temperature": 0.3,
        "max_tokens": 8192,
        "response_format": response_format,
        "messages": messages,
    }

    try:
        async with httpx.AsyncClient(
            timeout=180.0,
            follow_redirects=False,
            trust_env=False,
        ) as client:
            response = await client.post(url, headers=_auth_headers(), json=payload)
            if response.status_code == 400 and response_format.get("type") == "json_schema":
                payload["response_format"] = {"type": "json_object"}
                response = await client.post(url, headers=_auth_headers(), json=payload)
    except httpx.HTTPError as exc:
        raise LlmError(f"Appel LLM impossible : {exc}") from exc

    if response.status_code == 401:
        raise LlmError(
            "OpenRouter a refusé la clé (401). Dans .env, à la racine du repo : "
            "OPENAI_API_KEY=sk-or-v1-... sans guillemets ni espace, "
            "OPENAI_BASE_URL=https://openrouter.ai/api/v1 — puis relance uvicorn."
        )
    if response.status_code >= 400:
        raise LlmError(f"LLM HTTP {response.status_code} : {response.text[:800]}")

    try:
        body = response.json()
        choice = body["choices"][0]
        finish = str(choice.get("finish_reason") or "")
        raw = _message_text(choice.get("message") or {})
        if finish in {"length", "max_tokens"}:
            raise LlmError(
                "La réponse du modèle a été coupée (trop longue). Réessaie : "
                "en général ça passe au second essai."
            )
        parsed = parse_llm_json(raw)
    except LlmError:
        raise
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        preview = (raw if "raw" in locals() else response.text)[:180].replace("\n", " ")
        raise LlmError(
            f"Réponse LLM illisible (JSON attendu). Aperçu : {preview or '(vide)'}"
        ) from exc

    letter = str(parsed.get("cover_letter") or "").strip()
    cv = str(parsed.get("cv_markdown") or "").strip()
    if require_cv and (not cv or not letter):
        raise LlmError("Le modèle n'a pas renvoyé de CV et de lettre complets.")
    if not require_cv and not letter:
        raise LlmError("Le modèle n'a pas renvoyé de lettre complète.")
    return parsed
