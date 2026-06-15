"""Low-level Ollama chat client and response cleaning helpers.

Separated from :mod:`services.llm_service` so each module stays focused and
within the project's per-file size budget.
"""
from __future__ import annotations

import re

import requests
from flask import current_app

OLLAMA_OFFLINE = '__OLLAMA_OFFLINE__'


def ollama_chat(
    messages: list[dict[str, str]],
    max_tokens: int = 2048,
    *,
    temperature: float = 0.7,
    num_ctx: int = 4096,
) -> str:
    """Call Ollama ``/api/chat`` and return the final text answer.

    Handles models that emit a separate ``thinking`` field by falling back to
    extracting the final answer from it when ``content`` is empty. Returns
    :data:`OLLAMA_OFFLINE` when the server is unreachable.
    """
    host = current_app.config.get('OLLAMA_HOST', 'http://localhost:11434')
    model = current_app.config.get('LLM_MODEL', 'gemma4:26b')

    payload = {
        'model': model,
        'stream': False,
        'messages': messages,
        'think': False,
        'options': {
            'temperature': temperature,
            'top_p': 0.9,
            'num_predict': max_tokens,
            'num_ctx': num_ctx,
        },
    }

    try:
        resp = requests.post(f'{host}/api/chat', json=payload, timeout=180)
        resp.raise_for_status()
        data = resp.json()
        msg = data.get('message', {})

        content = (msg.get('content') or '').strip()
        if content:
            return content

        thinking = (msg.get('thinking') or '').strip()
        if thinking:
            return extract_final_answer(thinking)
        return ''
    except requests.exceptions.ConnectionError:
        return OLLAMA_OFFLINE
    except requests.exceptions.RequestException as exc:
        current_app.logger.error('[LLM] Ollama error: %s', exc)
        return ''


def extract_final_answer(thinking: str) -> str:
    """Extract the final answer from a model's ``thinking`` output."""
    final_patterns = [
        r'(?:Final answer|Best option|Output|결론|최종 답변)\s*[:\-]\s*(.+?)(?:\n\*|\Z)',
        r'\*Final:\*\s*(.+?)(?:\n|\Z)',
    ]
    for pattern in final_patterns:
        m = re.search(pattern, thinking, re.IGNORECASE | re.DOTALL)
        if m:
            ans = m.group(1).strip()
            if ans:
                return clean_thinking_line(ans)

    good_match = re.search(r'\*Draft \d+:\*\s*(.+?)\s*\(Good', thinking, re.DOTALL)
    if good_match:
        return clean_thinking_line(good_match.group(1).strip())

    drafts = re.findall(r'\*Draft \d+:\*\s*(.+?)(?=\*Draft |\Z)', thinking, re.DOTALL)
    if drafts:
        last_draft = re.sub(r'\s*\([^)]*\)\s*$', '', drafts[-1].strip()).strip()
        if last_draft:
            return clean_thinking_line(last_draft)

    lines = [line.strip() for line in thinking.split('\n') if line.strip()]
    for line in reversed(lines):
        line = re.sub(r'^\*+\s*', '', line).strip()
        if line and not line.startswith('User') and not line.startswith('Constraint'):
            return line
    return thinking[:200].strip()


def clean_thinking_line(text: str) -> str:
    """Clean a single extracted thinking line."""
    text = re.sub(r'^\*+\s*', '', text).strip()
    text = re.sub(r'\s*\([^)]{0,30}\)\s*$', '', text).strip()
    return text


def clean_text(text: str) -> str:
    """Strip markdown noise from a generated answer."""
    if not text:
        return ''
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*{2,}([^*]+)\*{2,}', r'\1', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def check_ollama_status() -> dict[str, object]:
    """Return Ollama connection status and the configured model."""
    host = current_app.config.get('OLLAMA_HOST', 'http://localhost:11434')
    model = current_app.config.get('LLM_MODEL', 'gemma4:26b')
    try:
        resp = requests.get(f'{host}/api/tags', timeout=3)
        resp.raise_for_status()
        models = [m['name'] for m in resp.json().get('models', [])]
        return {'online': True, 'model': model, 'host': host, 'available_models': models}
    except requests.exceptions.RequestException:
        return {'online': False, 'model': model, 'host': host, 'available_models': []}
