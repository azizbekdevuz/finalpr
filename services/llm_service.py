"""
services/llm_service.py
Ollama REST API를 통한 로컬 LLM 연동 모듈

gemma4:26b는 기본적으로 thinking 모드로 동작합니다.
→ /api/chat 호출 시 think: false 옵션으로 thinking 비활성화.
  비활성화가 안 될 경우, thinking 필드에서 최종 답변을 정제하여 추출.

지원 모델 후보 (config.py의 LLM_MODEL로 전환):
  - gemma4:26b      (Gemma 4 26B  — 기본)
  - llama3.1:8b     (Llama 3.1 8B)
  - mistral:7b      (Mistral 7B)
  - qwen2.5:14b     (Qwen2.5 14B)
"""

import re
import json
import requests
from flask import current_app


# ── Ollama Chat API 호출 ───────────────────────────────────────────────────────

def _ollama_chat(messages: list, max_tokens: int = 2048) -> str:
    """
    Ollama /api/chat 엔드포인트를 호출합니다.

    gemma4:26b thinking 모드 처리:
      - think: false 옵션으로 thinking 비활성화 시도
      - 그래도 content가 비면 thinking 필드에서 최종 답변 추출
    """
    host  = current_app.config.get('OLLAMA_HOST', 'http://localhost:11434')
    model = current_app.config.get('LLM_MODEL', 'gemma4:26b')

    payload = {
        'model':    model,
        'stream':   False,
        'messages': messages,
        'think':    False,   # gemma4 thinking 모드 비활성화
        'options':  {
            'temperature': 0.7,
            'top_p':       0.9,
            'num_predict': max_tokens,
            'num_ctx':     4096,
        },
    }

    try:
        resp = requests.post(
            f'{host}/api/chat',
            json=payload,
            timeout=180,
        )
        resp.raise_for_status()
        data = resp.json()
        msg  = data.get('message', {})

        # ① content에 실제 응답이 있으면 사용
        content = (msg.get('content') or '').strip()
        if content:
            return content

        # ② thinking 필드에서 최종 답변 추출 (thinking 모드 폴백)
        thinking = (msg.get('thinking') or '').strip()
        if thinking:
            return _extract_final_answer(thinking)

        return ''

    except requests.exceptions.ConnectionError:
        return '__OLLAMA_OFFLINE__'
    except Exception as e:
        current_app.logger.error(f'[LLM] Ollama 오류: {e}')
        return ''


def _extract_final_answer(thinking: str) -> str:
    """
    gemma4:26b thinking 필드에서 최종 답변을 추출합니다.

    thinking 구조:
      - 내부 추론 단계들 (Draft 1, Draft 2, ...)
      - 최종 선택: "Final answer:" 또는 마지막 단계의 실제 텍스트

    전략:
      1. "Final answer:", "Best:", "Output:", "결론:" 이후 텍스트 우선
      2. Draft 중 (Good) 또는 마지막으로 선택된 것
      3. 위 모두 실패 시 마지막 비공백 줄
    """
    # 패턴 1: "Final answer:", "Best option:", "Output:" 등 뒤의 텍스트
    final_patterns = [
        r'(?:Final answer|Best option|Output|결론|최종 답변)\s*[:\-]\s*(.+?)(?:\n\*|\Z)',
        r'\*Final:\*\s*(.+?)(?:\n|\Z)',
    ]
    for pattern in final_patterns:
        m = re.search(pattern, thinking, re.IGNORECASE | re.DOTALL)
        if m:
            ans = m.group(1).strip()
            if ans:
                return _clean_thinking_line(ans)

    # 패턴 2: Draft X 중 "(Good" 표시된 것
    good_match = re.search(r'\*Draft \d+:\*\s*(.+?)\s*\(Good', thinking, re.DOTALL)
    if good_match:
        return _clean_thinking_line(good_match.group(1).strip())

    # 패턴 3: 마지막 Draft 내용
    drafts = re.findall(r'\*Draft \d+:\*\s*(.+?)(?=\*Draft |\Z)', thinking, re.DOTALL)
    if drafts:
        last_draft = drafts[-1].strip()
        # "(A bit", "(Too" 등 비평 주석 제거
        last_draft = re.sub(r'\s*\([^)]*\)\s*$', '', last_draft).strip()
        if last_draft:
            return _clean_thinking_line(last_draft)

    # 패턴 4: 마지막 비공백 줄
    lines = [l.strip() for l in thinking.split('\n') if l.strip()]
    for line in reversed(lines):
        line = re.sub(r'^\*+\s*', '', line).strip()
        if line and not line.startswith('User') and not line.startswith('Constraint'):
            return line

    return thinking[:200].strip()


def _clean_thinking_line(text: str) -> str:
    """thinking에서 추출한 텍스트 정제."""
    # bullet, 괄호 주석 제거
    text = re.sub(r'^\*+\s*', '', text).strip()
    text = re.sub(r'\s*\([^)]{0,30}\)\s*$', '', text).strip()
    return text


# ── Step 1: 장소 키워드 추출 ──────────────────────────────────────────────────

def extract_place(user_message: str) -> str:
    """
    사용자 메시지에서 장소/지역 키워드를 추출합니다.

    Returns:
        추출된 키워드 (없으면 빈 문자열, Ollama 오프라인이면 '__OLLAMA_OFFLINE__')
    """
    messages = [
        {
            'role': 'system',
            'content': (
                '당신은 여행 메시지에서 장소 이름을 추출하는 도우미입니다.\n'
                'JSON 형식으로만 답하세요: {"keyword": "장소명"}\n'
                '장소가 없으면: {"keyword": ""}\n'
                '코드블록이나 부가 설명 없이 JSON 한 줄만 출력하세요.'
            ),
        },
        {
            'role': 'user',
            'content': f'메시지: "{user_message}"\n장소를 추출해주세요.',
        },
    ]

    raw = _ollama_chat(messages, max_tokens=80)

    if raw == '__OLLAMA_OFFLINE__':
        return '__OLLAMA_OFFLINE__'

    if not raw:
        return ''

    # JSON 파싱 시도
    try:
        cleaned = re.sub(r'```(?:json)?\s*', '', raw).replace('```', '').strip()
        # 첫 번째 { } 블록 추출
        match = re.search(r'\{[^}]*\}', cleaned, re.DOTALL)
        if match:
            obj = json.loads(match.group())
            kw  = obj.get('keyword', '').strip()
            if kw:
                return kw
    except Exception:
        pass

    # JSON 실패 시: 텍스트에서 의미 있는 한국어 단어 추출
    for line in raw.split('\n'):
        line = re.sub(r'^\*+\s*', '', line.strip()).strip('"\'').strip()
        if line and len(line) <= 50 and not any(c in line for c in ['{', '}', '`']):
            return line
    return ''


# ── Step 5: 코스 설명 생성 ────────────────────────────────────────────────────

def generate_course_description(spots: list, overviews: list) -> dict:
    """
    3개 관광지 + overview를 바탕으로 코스 요약과 대화형 설명을 생성합니다.

    Returns:
        {'summary': '한두 문장 요약', 'description': '대화형 상세 설명'}
    """
    spot_lines = []
    for i, (spot, ov) in enumerate(zip(spots, overviews), 1):
        title   = spot.get('title', f'관광지 {i}')
        addr    = spot.get('addr1', '')
        ov_text = (ov[:200] + '…') if len(ov or '') > 200 else (ov or '')
        spot_lines.append(f'{i}. {title} ({addr}): {ov_text}')

    spot_info = '\n'.join(spot_lines)

    # ── 요약 ────────────────────────────────────────
    summary_msgs = [
        {'role': 'system', 'content': '당신은 한국 여행 전문가입니다. 한국어로만 답하세요.'},
        {
            'role': 'user',
            'content': (
                f'다음 3개 관광지 코스를 한두 문장으로 요약해주세요.\n\n'
                f'{spot_info}\n\n'
                f'짧고 매력적인 요약문만 작성하세요.'
            ),
        },
    ]

    summary_raw = _ollama_chat(summary_msgs, max_tokens=256)

    if summary_raw == '__OLLAMA_OFFLINE__':
        return {
            'summary':     'Ollama 서버 오프라인',
            'description': '`ollama serve` 명령으로 서버를 먼저 시작해주세요.',
        }

    # ── 상세 설명 ────────────────────────────────────
    desc_msgs = [
        {
            'role': 'system',
            'content': (
                '당신은 친근하고 따뜻한 한국 여행 가이드입니다.\n'
                '방문객에게 직접 말하는 대화체 한국어로 작성하세요.\n'
                '마크다운, 특수기호, 영어는 최대한 피하세요.'
            ),
        },
        {
            'role': 'user',
            'content': (
                f'다음 3개 관광지를 순서대로 방문하는 여행자에게 각 장소를 친근하게 소개해주세요.\n\n'
                f'{spot_info}\n\n'
                f'각 관광지마다 2~3문장씩 대화체로 작성하세요.'
            ),
        },
    ]

    desc_raw = _ollama_chat(desc_msgs, max_tokens=1024)

    return {
        'summary':     _clean_text(summary_raw),
        'description': _clean_text(desc_raw),
    }


def _clean_text(text: str) -> str:
    """마크다운 제거 및 텍스트 정제."""
    if not text:
        return ''
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*{2,}([^*]+)\*{2,}', r'\1', text)   # 굵은글씨 제거
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# ── Ollama 상태 확인 ──────────────────────────────────────────────────────────

def check_ollama_status() -> dict:
    """Ollama 서버 연결 상태와 현재 모델 반환."""
    host  = current_app.config.get('OLLAMA_HOST', 'http://localhost:11434')
    model = current_app.config.get('LLM_MODEL',   'gemma4:26b')
    try:
        resp   = requests.get(f'{host}/api/tags', timeout=3)
        resp.raise_for_status()
        models = [m['name'] for m in resp.json().get('models', [])]
        return {'online': True, 'model': model, 'host': host, 'available_models': models}
    except Exception:
        return {'online': False, 'model': model, 'host': host, 'available_models': []}
