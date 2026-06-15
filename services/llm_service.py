"""Course recommendation logic built on the local LLM (Ollama).

Locale is passed explicitly from the route so generated descriptions match the
selected UI language. Response keys returned to the client are unchanged
(``summary`` / ``description``); only the natural-language content varies.
"""
from __future__ import annotations

import json
import re

from services.llm_client import OLLAMA_OFFLINE, check_ollama_status, clean_text, ollama_chat

__all__ = [
    'extract_place',
    'generate_course_description',
    'check_ollama_status',
    'OLLAMA_OFFLINE',
]


def extract_place(user_message: str) -> str:
    """Extract a place/region keyword from a free-form user message."""
    messages = [
        {
            'role': 'system',
            'content': (
                'You extract a Korean place name from a travel message.\n'
                'Reply with JSON only: {"keyword": "place"}.\n'
                'If there is no place: {"keyword": ""}.\n'
                'Output a single JSON line with no code block or extra text.'
            ),
        },
        {'role': 'user', 'content': f'Message: "{user_message}"\nExtract the place.'},
    ]

    raw = ollama_chat(messages, max_tokens=80)
    if raw == OLLAMA_OFFLINE:
        return OLLAMA_OFFLINE
    if not raw:
        return ''

    try:
        cleaned = re.sub(r'```(?:json)?\s*', '', raw).replace('```', '').strip()
        match = re.search(r'\{[^}]*\}', cleaned, re.DOTALL)
        if match:
            obj = json.loads(match.group())
            keyword = (obj.get('keyword') or '').strip()
            if keyword:
                return keyword
    except (ValueError, json.JSONDecodeError):
        pass

    for line in raw.split('\n'):
        line = re.sub(r'^\*+\s*', '', line.strip()).strip('"\'').strip()
        if line and len(line) <= 50 and not any(c in line for c in ['{', '}', '`']):
            return line
    return ''


def _is_english(locale: str) -> bool:
    return (locale or 'ko').lower().startswith('en')


def _offline_result(locale: str) -> dict[str, str]:
    if _is_english(locale):
        return {
            'summary': 'Ollama server is offline',
            'description': 'Please start the server first with the `ollama serve` command.',
        }
    return {
        'summary': 'Ollama 서버 오프라인',
        'description': '`ollama serve` 명령으로 서버를 먼저 시작해주세요.',
    }


def _build_spot_info(spots: list, overviews: list) -> str:
    lines = []
    for i, (spot, ov) in enumerate(zip(spots, overviews, strict=False), 1):
        title = spot.get('title', f'Spot {i}')
        addr = spot.get('addr1', '')
        ov_text = (ov[:200] + '…') if len(ov or '') > 200 else (ov or '')
        lines.append(f'{i}. {title} ({addr}): {ov_text}')
    return '\n'.join(lines)


def _prompts(locale: str, spot_info: str) -> tuple[list, list]:
    """Build (summary_messages, description_messages) for the given locale.

    Place names from the external API stay in their original language; only the
    surrounding narration follows the selected locale.
    """
    if _is_english(locale):
        summary_sys = 'You are a Korea travel expert. Answer in English only.'
        summary_user = (
            f'Summarize this 3-spot travel course in one or two sentences.\n\n'
            f'{spot_info}\n\nWrite only a short, appealing summary. Keep place names as given.'
        )
        desc_sys = (
            'You are a friendly Korea travel guide.\n'
            'Write in a warm, conversational English voice addressed to the visitor.\n'
            'Avoid markdown and special symbols. Keep place names as given.'
        )
        desc_user = (
            f'Introduce each of these 3 spots warmly, in visiting order.\n\n'
            f'{spot_info}\n\nWrite 2-3 conversational sentences per spot.'
        )
    else:
        summary_sys = '당신은 한국 여행 전문가입니다. 한국어로만 답하세요.'
        summary_user = (
            f'다음 3개 관광지 코스를 한두 문장으로 요약해주세요.\n\n'
            f'{spot_info}\n\n짧고 매력적인 요약문만 작성하세요.'
        )
        desc_sys = (
            '당신은 친근하고 따뜻한 한국 여행 가이드입니다.\n'
            '방문객에게 직접 말하는 대화체 한국어로 작성하세요.\n'
            '마크다운, 특수기호, 영어는 최대한 피하세요.'
        )
        desc_user = (
            f'다음 3개 관광지를 순서대로 방문하는 여행자에게 각 장소를 친근하게 소개해주세요.\n\n'
            f'{spot_info}\n\n각 관광지마다 2~3문장씩 대화체로 작성하세요.'
        )

    summary_msgs = [
        {'role': 'system', 'content': summary_sys},
        {'role': 'user', 'content': summary_user},
    ]
    desc_msgs = [
        {'role': 'system', 'content': desc_sys},
        {'role': 'user', 'content': desc_user},
    ]
    return summary_msgs, desc_msgs


def generate_course_description(spots: list, overviews: list, locale: str = 'ko') -> dict[str, str]:
    """Generate a course summary + conversational description in ``locale``."""
    spot_info = _build_spot_info(spots, overviews)
    summary_msgs, desc_msgs = _prompts(locale, spot_info)

    summary_raw = ollama_chat(summary_msgs, max_tokens=256)
    if summary_raw == OLLAMA_OFFLINE:
        return _offline_result(locale)

    desc_raw = ollama_chat(desc_msgs, max_tokens=1024)
    return {
        'summary': clean_text(summary_raw),
        'description': clean_text(desc_raw),
    }
