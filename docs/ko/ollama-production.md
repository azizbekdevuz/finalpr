# 프로덕션에서 Ollama 사용하기

<p align="right">
  <strong>한국어</strong> ·
  <a href="../en/ollama-production.md">English</a>
</p>

이 앱은 **서버**에서 Ollama를 호출합니다([`services/llm_client.py`](../../services/llm_client.py)의 `OLLAMA_HOST`). Render 같은 호스팅 환경에서 `localhost:11434`는 **내 PC가 아니라** 컨테이너 자신을 가리키므로, Ollama에 도달할 수 있는 공개 URL이 없으면 AI 기능은 오프라인으로 표시됩니다.

**데모 권장:** PC에서 Ollama 실행 → [ngrok](https://ngrok.com)으로 노출 → 호스팅(Render 등)의 `OLLAMA_HOST` 설정 → 재배포.

관련 문서: [환경 변수](configuration.md), [배포](deployment.md).

---

## 1. Ollama 설치

OS에 맞게 설치한 뒤 동작을 확인합니다.

| OS | 설치 | 확인 |
| --- | --- | --- |
| **Windows** | [ollama.com/download](https://ollama.com/download)에서 설치 파일 실행. 보통 백그라운드 서비스로 실행됩니다. | PowerShell: `ollama --version` |
| **macOS** | [ollama.com/download](https://ollama.com/download) 앱 설치, 또는 `brew install ollama` | 터미널: `ollama --version` |
| **Linux** | `curl -fsSL https://ollama.com/install.sh \| sh` | 터미널: `ollama --version` |

**설명:** Ollama CLI와 로컬 API(포트 `11434`)가 설치됩니다.

---

## 2. Ollama 실행 및 모델 다운로드

모델 이름은 로컬과 프로덕션의 `LLM_MODEL`에 **동일하게** 맞춥니다.

### Windows (PowerShell)

```powershell
# 서버가 떠 있지 않다면 실행 (트레이 앱 또는 서비스).
ollama serve

# 다른 터미널에서 모델 다운로드 (예시).
ollama pull qwen2.5:3b
```

### macOS / Linux (터미널)

```bash
# 서버 실행 (이미 서비스로 떠 있으면 생략 가능).
ollama serve

# 다른 터미널에서 모델 다운로드 (예시).
ollama pull qwen2.5:3b
```

**설명:** `ollama serve`는 `http://127.0.0.1:11434`에서 대기합니다. `ollama pull`은 `/api/chat`에 필요한 모델 파일을 받습니다.

**확인:** `ollama list`에 해당 모델이 보여야 합니다.

---

## 3. ngrok으로 Ollama 노출

호스팅 서버는 내 PC의 `127.0.0.1`에 직접 접속할 수 없습니다. 터널은 로컬 `11434` 포트를 임시 공개 HTTPS URL로 연결합니다.

### Windows

1. [ngrok.com](https://ngrok.com) 가입 후 ngrok 설치.
2. 인증 토큰 등록 (최초 1회): `ngrok config add-authtoken <YOUR_TOKEN>`
3. 실행:

```powershell
ngrok http 11434
```

### macOS

```bash
brew install ngrok/ngrok/ngrok
ngrok config add-authtoken <YOUR_TOKEN>
ngrok http 11434
```

### Linux

```bash
# 배포판별 설치: https://ngrok.com/download
ngrok config add-authtoken <YOUR_TOKEN>
ngrok http 11434
```

**설명:** `Forwarding  https://abc123.ngrok-free.app -> http://localhost:11434` 같은 줄이 나옵니다. **HTTPS** 주소만 복사합니다:

```text
https://abc123.ngrok-free.app
```

끝에 `/api/chat`을 붙이지 마세요. 앱이 API 경로를 자동으로 붙입니다.

데모가 끝날 때까지 이 터미널을 열어 두세요. 무료 ngrok URL은 재시작할 때마다 바뀔 수 있습니다.

---

## 4. 프로덕션 환경 변수 설정

호스팅(Render → Web Service → **Environment** 등)에서 설정:

| 변수 | 예시 | 참고 |
| --- | --- | --- |
| `OLLAMA_HOST` | `https://abc123.ngrok-free.app` | 전체 URL, 끝 슬래시 없음 |
| `LLM_MODEL` | `qwen2.5:3b` | `ollama list`에 있는 이름과 일치 |

저장하면 서비스가 재배포됩니다.

**설명:** Flask는 [`config.py`](../../config.py)의 `OLLAMA_HOST`를 읽어 `{OLLAMA_HOST}/api/chat`으로 요청합니다.

**로컬 `.env`:** 개발용은 `OLLAMA_HOST=http://localhost:11434` 유지. 프로덕션 값은 호스팅 대시보드에만 둡니다.

---

## 5. 동작 확인

1. PC에서 **Ollama + ngrok**이 실행 중인지 확인.
2. 배포된 사이트 → 코스 / AI 페이지 접속.
3. 또는 앱의 Ollama 상태 API 확인([`routes/courses.py`](../../routes/courses.py)).

문제가 있을 때:

| 증상 | 가능한 원인 |
| --- | --- |
| “Ollama offline” | 터널 종료, PC 절전, `OLLAMA_HOST` 오타 |
| 빈 응답 / 오류 | `LLM_MODEL` 미설치 (`ollama pull …` 필요) |
| 예전엔 됐는데 안 됨 | ngrok URL 변경 → `OLLAMA_HOST` 갱신 후 재배포 |

---

## 보안

- 공개 터널은 GPU/CPU를 인터넷에 노출합니다. 데모 후 **ngrok을 종료**하세요.
- 터널 URL·비밀값을 git에 커밋하지 마세요.
- `OLLAMA_ORIGINS`(CORS)는 **브라우저 → Ollama**용입니다. 이 앱은 **서버 측** 요청만 하므로, origin만 허용해도 Render가 내 PC에 연결되지는 **않습니다**.

---

## 대안 (요약)

| 목적 | 방법 |
| --- | --- |
| 일회성 데모 | ngrok + `OLLAMA_HOST` (위 단계) |
| 고정에 가까운 터널 URL | [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) → `localhost:11434` |
| PC 없이 상시 운영 | 클라우드 VM에 Ollama 설치 → HTTPS·인증 앞단 → `OLLAMA_HOST`에 VM URL 설정 |

24/7 무료 운영이 필요하면, 가벼운 모델(`qwen2.5:3b`, `llama3.2:3b`)을 올린 소형 VPS가 가정 PC + 터널보다 안정적입니다.
