"""Course recommendation logic built on the local LLM (Ollama).

Locale is passed explicitly from the route so generated descriptions match the
selected UI language. Response keys returned to the client are unchanged
(``summary`` / ``description``); only the natural-language content varies.
Place keywords are always Korean (Hangul) for Tour API lookup, regardless of UI.
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

# Romanized / English aliases → Korean keywords for the Tour API.
_PLACE_ALIASES: dict[str, str] = {
    'gyeongbokgung': '경복궁',
    'gyeongbok palace': '경복궁',
    'sokcho': '속초',
    'jeju': '제주',
    'jeju island': '제주',
    'gyeongju': '경주',
    'seoraksan': '설악산',
    'mount seorak': '설악산',
    'busan': '부산',
    'seoul': '서울',
    'incheon': '인천',
    'gangneung': '강릉',
}


def _has_hangul(text: str) -> bool:
    return bool(re.search(r'[가-힣]', text))


def _normalize_keyword(keyword: str) -> str:
    """Map common English/romanized names to Korean Tour API keywords."""
    cleaned = keyword.strip()
    if not cleaned or _has_hangul(cleaned):
        return cleaned
    return _PLACE_ALIASES.get(cleaned.lower(), cleaned)


def extract_place(user_message: str) -> str:
    """Extract a Korean place keyword from a free-form user message."""
    messages = [
        {
            'role': 'system',
            'content': (
                'You extract a Korean place name in Hangul from a travel message in any language.\n'
                'Reply with JSON only: {"keyword": "한글지명"}.\n'
                'Always use the official Korean name (Hangul), never romanized English.\n'
                'Examples: Gyeongbokgung → 경복궁, Busan → 부산, Jeju → 제주, Sokcho → 속초.\n'
                'If there is no place: {"keyword": ""}.\n'
                'Output a single JSON line with no code block or extra text.'
            ),
        },
        {'role': 'user', 'content': f'Message: "{user_message}"\nExtract the place in Hangul.'},
    ]

    raw = ollama_chat(messages, max_tokens=48, temperature=0.2, num_ctx=1024)
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
                return _normalize_keyword(keyword)
    except (ValueError, json.JSONDecodeError):
        pass

    for line in raw.split('\n'):
        line = re.sub(r'^\*+\s*', '', line.strip()).strip('"\'').strip()
        if line and len(line) <= 50 and not any(c in line for c in ['{', '}', '`']):
            return _normalize_keyword(line)
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
        ov_text = (ov[:120] + '…') if len(ov or '') > 120 else (ov or '')
        lines.append(f'{i}. {title} ({addr}): {ov_text}')
    return '\n'.join(lines)


def _course_prompt(locale: str, spot_info: str) -> list[dict[str, str]]:
    """Single prompt that returns both summary and description (one LLM round-trip)."""
    if _is_english(locale):
        sys = (
            'You are a Korea travel expert. Reply with JSON only:\n'
            '{"summary":"1-2 sentence course overview","description":"guide text"}.\n'
            'Write in warm conversational English. Keep every place name exactly as given (Korean).\n'
            'Description: 2 short sentences per spot in visiting order. No markdown.'
        )
        user = (
            f'Create a travel course summary and guide for these 3 spots:\n\n{spot_info}\n\n'
            'JSON only.'
        )
    else:
        sys = (
            '당신은 한국 여행 전문가입니다. JSON만 출력하세요:\n'
            '{"summary":"한두 문장 요약","description":"가이드 본문"}.\n'
            '친근한 대화체 한국어. 관광지 이름은 주어진 그대로 유지. 마크다운 금지.\n'
            'description: 관광지마다 2문장씩 순서대로.'
        )
        user = (
            f'다음 3개 관광지 코스의 요약과 가이드를 작성하세요:\n\n{spot_info}\n\n'
            'JSON만 출력.'
        )

    return [
        {'role': 'system', 'content': sys},
        {'role': 'user', 'content': user},
    ]


def _coerce_text_field(value: object) -> str:
    """Normalize LLM JSON fields that may be returned as strings or lists."""
    if value is None:
        return ''
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts = [str(item).strip() for item in value if str(item).strip()]
        return '\n\n'.join(parts)
    return str(value).strip()


def _parse_course_json(raw: str) -> dict[str, str]:
    if not raw:
        return {'summary': '', 'description': ''}
    try:
        cleaned = re.sub(r'```(?:json)?\s*', '', raw).replace('```', '').strip()
        match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if match:
            obj = json.loads(match.group())
            return {
                'summary': clean_text(_coerce_text_field(obj.get('summary'))),
                'description': clean_text(_coerce_text_field(obj.get('description'))),
            }
    except (ValueError, json.JSONDecodeError, AttributeError, TypeError):
        pass
    parts = raw.split('\n\n', 1)
    return {
        'summary': clean_text(parts[0]),
        'description': clean_text(parts[1] if len(parts) > 1 else ''),
    }


def generate_course_description(spots: list, overviews: list, locale: str = 'ko') -> dict[str, str]:
    """Generate a course summary + conversational description in ``locale``."""
    spot_info = _build_spot_info(spots, overviews)
    messages = _course_prompt(locale, spot_info)

    raw = ollama_chat(messages, max_tokens=512, temperature=0.6, num_ctx=2048)
    if raw == OLLAMA_OFFLINE:
        return _offline_result(locale)

    return _parse_course_json(raw)
