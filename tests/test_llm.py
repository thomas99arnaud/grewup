import json

import pytest

from backend.modules.applications.llm import parse_llm_json


def test_parse_plain_json():
    data = parse_llm_json('{"job_title": "Dev", "cv_markdown": "x"}')
    assert data["job_title"] == "Dev"


def test_parse_fenced_json():
    raw = """```json
{"job_title": "Dev", "cover_letter": "Bonjour"}
```"""
    data = parse_llm_json(raw)
    assert data["cover_letter"] == "Bonjour"


def test_parse_json_with_preamble():
    raw = 'Voici le résultat :\n{"language": "fr", "company": "IAS"}\n'
    assert parse_llm_json(raw)["company"] == "IAS"


def test_parse_rejects_empty():
    with pytest.raises(json.JSONDecodeError):
        parse_llm_json("   ")
