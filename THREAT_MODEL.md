# Threat Model — LLM Security Gateway

Scope: a FastAPI gateway that mediates chat requests between a client and an LLM backend (Ollama local, or Groq cloud free-tier). This document maps relevant [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/) risks to concrete attack scenarios, the mitigation implemented (or planned) in this codebase, and residual risk after mitigation.

## In scope

- The gateway API (`app/main.py`), guardrail layer (`app/guards/`), and policy engine (`app/policies/`)
- The model client abstraction (`app/model_client.py`) and its two backends (Ollama, Groq)
- Chat-only interaction (no file upload, no tool-calling/agentic execution in v1)

## Out of scope

- Model training/fine-tuning security (LLM03 — Training Data Poisoning): not applicable, this project only consumes pre-trained models via inference APIs
- Supply-chain security of the underlying model weights (LLM05): tracked as an assumption, not actively mitigated in v1
- Multi-tenant infrastructure hardening (network segmentation, secrets management beyond `.env`): noted as future work

---

## LLM01 — Prompt Injection

**Threat:** A user crafts input designed to override the system prompt, exfiltrate it, or manipulate the model into ignoring its guardrails (e.g. "ignore previous instructions and...").

**Attack scenarios:**
- Direct injection: user asks the model to reveal its system prompt or reverse its safety instructions
- Indirect injection: if content from an external source (e.g. a fetched document) is later added to context, it could carry embedded instructions

**Mitigation:**
- Structured prompts with clear delimiters separating system instructions from user input, so the model can distinguish instruction from data
- Pattern-based deny list for known injection phrasings (`app/guards/`), rejecting or flagging requests before they reach the model
- System prompt explicitly instructs the model not to disclose its own instructions

**Residual risk:** Pattern/deny-list detection cannot catch every injection phrasing — it reduces the attack surface but is not a complete solution. Documented as a known limitation.

---

## LLM02 — Insecure Output Handling

**Threat:** Model output is trusted and passed downstream (e.g. rendered in a frontend, or used in a follow-up action) without validation, enabling XSS or injection if the output contains malicious markup/code.

**Attack scenarios:**
- Model output includes `<script>` tags or malformed markup rendered directly in the frontend
- Model output includes text crafted to look like a system command if consumed by a downstream process

**Mitigation:**
- All model output passes through a sanitization step before being returned to the client (`app/guards/`)
- Output is validated against an expected response schema; unexpected structure is flagged, not silently passed through

**Residual risk:** Sanitization covers known patterns (HTML/script injection); a fully novel encoding could bypass filters. Mitigation is defense-in-depth, not a guarantee.

---

## LLM06 — Excessive Agency

**Threat:** The model is given more autonomy, tool access, or permission than the task requires, so a successful injection or hallucination can cause real-world side effects.

**Attack scenarios:**
- If future versions add tool-calling (e.g. web search, code execution), a hijacked model could invoke tools outside its intended scope

**Mitigation:**
- v1 exposes no tool-calling or agentic actions — the gateway is read-only chat, so there is no action for a hijacked model to take beyond generating text
- `app/policies/` defines an explicit allow-list for any future capability, rather than defaulting to open access

**Residual risk:** None in v1 scope by design. This becomes the primary risk to re-assess if/when tool use is added.

---

## LLM09 — Overreliance

**Threat:** Users treat model output as authoritative fact without independent verification, leading to bad decisions based on hallucinated content.

**Attack scenarios:**
- Not an "attack" in the traditional sense — a usability/trust risk rather than an exploit

**Mitigation:**
- Response metadata includes guardrail status (e.g. flagged/passed) so the client can surface a caveat
- Documented here and in the README so it's an explicit, visible limitation rather than an implicit assumption

**Residual risk:** Cannot be fully mitigated at the gateway level — this is a UX/user-education problem as much as a technical one.

---

## Test Coverage Mapping

| Risk | Test file | What's verified |
|---|---|---|
| LLM01 | `tests/test_guards.py` *(planned)* | Known injection payloads are blocked/flagged |
| LLM02 | `tests/test_guards.py` *(planned)* | Malicious output patterns are sanitized before return |
| LLM06 | `tests/test_policies.py` *(planned)* | No unauthorized action/tool path is reachable |
| LLM09 | — | Not automatable; addressed via response metadata + docs |

## Assumptions

- The model backend (Ollama or Groq) itself is not adversarial — this threat model covers the gateway's handling of untrusted *input*, not a compromised model provider
- `.env` secrets (API keys) are not committed and are managed outside version control

## Change Log

- Initial threat model drafted alongside project architecture, covering LLM01, LLM02, LLM06, LLM09.