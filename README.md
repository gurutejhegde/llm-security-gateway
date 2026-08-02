# LLM Security Gateway

A FastAPI gateway that sits in front of an LLM (local via **Ollama**, or cloud via a **Groq**-compatible free-tier API) and enforces input/output guardrails mapped to the **OWASP Top 10 for LLM Applications**.

Instead of trusting a raw prompt straight from a user into a model, this gateway validates, filters, and audits every request/response pair — the same pattern used in production LLM deployments to reduce prompt-injection, data-leakage, and unsafe-output risk.

## Why this project exists

Most "AI chatbot" demos wire a UI directly to an LLM API. This project treats the LLM as an **untrusted, non-deterministic component** and builds the security boundary around it: allow/deny policies, structured system-prompt hardening, output sanitization, and a documented threat model — not just a working chat window.

## OWASP LLM Top 10 Coverage

| Risk | Description | Mitigation in this project |
|---|---|---|
| **LLM01** — Prompt Injection | Malicious input manipulates model behavior or leaks the system prompt | Input classification layer, delimiter-based prompt structuring, injection-pattern deny list (see `app/guards/`) |
| **LLM02** — Insecure Output Handling | Model output trusted/rendered without validation (XSS, command injection downstream) | Output schema validation + sanitization before returning to client (`app/guards/`) |
| **LLM06** — Excessive Agency | Model given more capability/autonomy than the task needs | No tool-calling/agentic actions exposed; gateway is read-only chat, explicit policy allow-list in `app/policies/` |
| **LLM09** — Overreliance | Users trusting model output as fact without caveats | Response includes confidence/guardrail metadata; documented in `THREAT_MODEL.md` |

Full details, attack scenarios, and residual risk: see [`THREAT_MODEL.md`](./THREAT_MODEL.md).

## Architecture

```
┌──────────┐      ┌───────────────────┐      ┌──────────────────┐
│ Frontend │ ───▶ │  FastAPI Gateway  │ ───▶ │   Model Backend   │
│ (chat UI)│      │  app/main.py      │      │ Ollama (local) or │
└──────────┘      │                   │      │ Groq (cloud, free)│
                  │  ┌─────────────┐  │      └──────────────────┘
                  │  │ app/guards  │  │  input validation,
                  │  │             │  │  prompt-injection checks,
                  │  └─────────────┘  │  output sanitization
                  │  ┌─────────────┐  │
                  │  │ app/policies│  │  allow/deny rules,
                  │  │             │  │  rate limits, topic scope
                  │  └─────────────┘  │
                  └───────────────────┘
```

- **`app/model_client.py`** abstracts the model backend behind a single interface, so the same guardrail pipeline runs regardless of whether the request goes to a local Ollama model or the Groq API. Backend is selected via `.env`.
- **`app/guards/`** — input/output validation: prompt-injection pattern detection, PII/secret leakage checks on output, response schema enforcement.
- **`app/policies/`** — declarative allow/deny rules (topics, max tokens, rate limits) loaded at startup, not hardcoded in route logic.

## Tech Stack

- **FastAPI** — gateway API layer
- **Ollama** — local model serving (dev/offline)
- **Groq API** — free-tier cloud inference (OpenAI-compatible)
- **LangChain** *(optional, if used in `model_client.py`)* — prompt templating
- **uv** — Python dependency/environment management
- **pytest** — guardrail test suite

## Setup

```bash
# clone
git clone https://github.com/<your-username>/llm-security-gateway.git
cd llm-security-gateway

# install dependencies with uv
uv sync

# configure environment
cp .env.example .env
# edit .env: set MODEL_PROVIDER=ollama|groq, GROQ_API_KEY=..., OLLAMA_HOST=...

# (if using Ollama) pull a model
ollama pull llama3.2

# run the gateway
uv run uvicorn app.main:app --reload
```

## Testing

```bash
uv run pytest tests/ -v
```

Test suite covers guardrail behavior directly — prompt-injection payloads that must be blocked, and outputs that must be sanitized. See `tests/` and `THREAT_MODEL.md` for the mapping between test cases and OWASP risks.

## Project Status

🚧 Actively in development. Architecture and guardrail design in progress — see commit history for build log.

## Roadmap

- [ ] Input guard: prompt-injection pattern detection
- [ ] Output guard: sanitization + schema validation
- [ ] Policy engine: allow/deny + rate limiting
- [ ] Model client: Ollama + Groq pluggable backend
- [ ] Test report generation
- [ ] Minimal frontend chat UI

## License

MIT — see [`LICENSE`](./LICENSE).