# Ollama in production

<p align="right">
  <a href="../ko/ollama-production.md">한국어</a> ·
  <strong>English</strong>
</p>

This app calls Ollama from the **server** (`OLLAMA_HOST` in [`services/llm_client.py`](../../services/llm_client.py)). On hosted platforms such as Render, `localhost:11434` points at the container itself—not your PC—so AI features stay offline unless Ollama is reachable at a public URL.

**Demo approach (recommended):** run Ollama on your machine, expose it with [ngrok](https://ngrok.com), set `OLLAMA_HOST` on the host (e.g. Render), redeploy.

See also [Configuration](configuration.md) and [Deployment](deployment.md).

---

## 1. Install Ollama

Install the runtime for your OS, then verify it works.

| OS | Install | Verify |
| --- | --- | --- |
| **Windows** | Download the installer from [ollama.com/download](https://ollama.com/download) and run it. Ollama usually starts as a background service. | Open PowerShell: `ollama --version` |
| **macOS** | Download the app from [ollama.com/download](https://ollama.com/download), or: `brew install ollama` | Terminal: `ollama --version` |
| **Linux** | `curl -fsSL https://ollama.com/install.sh \| sh` | Terminal: `ollama --version` |

**What this does:** installs the Ollama CLI and local API on port `11434`.

---

## 2. Start Ollama and pull a model

Pick one model name and use the **same** value for `LLM_MODEL` locally and in production.

### Windows (PowerShell)

```powershell
# Start the server if it is not already running (tray app or service).
ollama serve

# In another terminal — download the model (example).
ollama pull qwen2.5:3b
```

### macOS / Linux (Terminal)

```bash
# Start the server (skip if already running as a service).
ollama serve

# In another terminal — download the model (example).
ollama pull qwen2.5:3b
```

**What this does:** `ollama serve` listens on `http://127.0.0.1:11434`. `ollama pull` downloads weights so `/api/chat` can run.

**Check:** `ollama list` should show your model.

---

## 3. Expose Ollama with ngrok

Hosted apps cannot reach your private `127.0.0.1`. A tunnel gives you a temporary public HTTPS URL that forwards to local port `11434`.

### Windows

1. Sign up at [ngrok.com](https://ngrok.com) and install ngrok.
2. Add your authtoken (once): `ngrok config add-authtoken <YOUR_TOKEN>`
3. Run:

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
# See https://ngrok.com/download for your distro, then:
ngrok config add-authtoken <YOUR_TOKEN>
ngrok http 11434
```

**What this does:** ngrok prints a line like `Forwarding  https://abc123.ngrok-free.app -> http://localhost:11434`. Copy the **HTTPS** host only:

```text
https://abc123.ngrok-free.app
```

Do **not** append `/api/chat`—the app adds API paths automatically.

Keep this terminal open for the whole demo. Free ngrok URLs change when you restart ngrok.

---

## 4. Configure production environment

On your host (e.g. **Render** → Web Service → **Environment**), set:

| Variable | Example | Notes |
| --- | --- | --- |
| `OLLAMA_HOST` | `https://abc123.ngrok-free.app` | Full URL, no trailing slash |
| `LLM_MODEL` | `qwen2.5:3b` | Must match a model from `ollama list` |

Save changes so the service redeploys.

**What this does:** Flask reads `OLLAMA_HOST` from [`config.py`](../../config.py) and POSTs to `{OLLAMA_HOST}/api/chat`.

**Local `.env`:** keep `OLLAMA_HOST=http://localhost:11434` for development; production values live only on the host dashboard.

---

## 5. Verify

1. **Tunnel + Ollama running** on your machine.
2. Open your deployed site → course / AI page.
3. Or call the status route your app exposes (see [`routes/courses.py`](../../routes/courses.py)).

If it fails:

| Symptom | Likely cause |
| --- | --- |
| “Ollama offline” | Tunnel stopped, PC asleep, or wrong `OLLAMA_HOST` |
| Empty / error response | `LLM_MODEL` not pulled (`ollama pull …`) |
| Worked before, broken now | Free ngrok URL changed—update `OLLAMA_HOST` and redeploy |

---

## Security

- A public tunnel exposes your GPU/CPU to the internet. **Stop ngrok** when the demo ends.
- Do not commit tunnel URLs or secrets to git.
- `OLLAMA_ORIGINS` (CORS) is for browser → Ollama calls. This app uses **server-side** requests, so changing origins alone does **not** connect Render to your PC.

---

## Alternatives (brief)

| Goal | Approach |
| --- | --- |
| One-time demo | ngrok + `OLLAMA_HOST` (steps above) |
| Stable tunnel hostname | [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) to `localhost:11434` |
| Always-on without your PC | Run Ollama on a small cloud VM; protect with HTTPS + auth; set `OLLAMA_HOST` to that URL |

For 24/7 free hosting, a small VPS with a lightweight model (`qwen2.5:3b`, `llama3.2:3b`) is more reliable than keeping a home PC and tunnel online.
