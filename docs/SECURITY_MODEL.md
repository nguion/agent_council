<!-- AI Generated Code by Deloitte + Cursor (BEGIN) -->
## Agent Council — Security Model (Current State + Handoff Guidance)

This document describes the **current** security posture of Agent Council and the explicit gaps the handoff roadmap is designed to close. It is written to support early security review and to prevent “surprise behaviors” during internal adoption.

### Security goals
- **Prevent cross-user data access** (no session data leakage across identities).
- **Make data egress explicit** (LLM provider, optional web search).
- **Minimize sensitive-data sprawl** (uploads, extracted text, logs).
- **Enable auditability** (who did what, when) — planned.
- **Provide safe production defaults** (e.g., disable risky features unless explicitly enabled) — partially planned.

### Non-goals (in this repo)
- Implementing a full Deloitte Entra ID login UX end-to-end.
- Selecting a specific hosting platform, queue, or object store.

### Trust boundaries and assumptions
Assumptions (must be revisited by the owning team):
- Users may upload **sensitive client or internal documents**.
- Uploaded files and LLM outputs must be treated as **untrusted input**.
- In production, identity is expected to be enforced by either:
  - a trusted gateway that injects identity headers, or
  - JWT access tokens validated server-side.

Trust boundaries:
- **Browser/UI**: untrusted client.
- **API service**: policy enforcement point (auth, authz, data limits, logging policy).
- **Database**: durable store; compromise exposes historical state.
- **Local filesystem artifacts**: present in current implementation, not safe for multi-instance prod.
- **External LLM provider**: prompts/responses can contain sensitive data; must be disclosed and controlled.
- **Optional web search**: may contact third parties; must be disclosed and controlled.

### Authentication (current)
Implemented in `src/web/api.py`:
- **DEV mode (`AUTH_MODE=DEV`, default)**:
  - Identity comes from `X-User-Id` header; defaults to `dev-user@localhost` if missing.
- **PROD mode (`AUTH_MODE=PROD`)**:
  - Requires either:
    - `X-Authenticated-User` trusted header (gateway pattern), OR
    - `Authorization: Bearer <JWT>` validated with `AUTH_JWT_*`
  - Optional escape hatch: `AUTH_ALLOW_X_USER_ID_IN_PROD=true` (should remain disabled by default).

Security note:
- In production, the owning team should ensure `AUTH_MODE=PROD` and avoid enabling any header-based escape hatches except via vetted gateway controls.

### Authorization (current)
- Ownership checks are enforced on all session endpoints: a user can only access sessions they own.
- Unauthorized access returns **404** (prevents session-id enumeration).
- **RBAC implemented** (Sprint 1 PR-6):
  - Roles: `user` (default), `admin`, `auditor`
  - `require_role()` FastAPI dependency enforces role-based access
  - Admin-only endpoints protected (e.g., `/api/admin/metrics/summary`)
  - New users default to `role='user'`

### Data handling and egress (current)
See `docs/DATA_HANDLING.md` for the full matrix.

Key points:
- Uploaded files are saved on local disk and ingested into extracted text (`ingested_data`).
- Extracted text is stored in DB `session_state` today.
- Prompts and model outputs are logged to markdown files by default.
- If enabled per-agent, web search can be used via OpenAI Agents tool integration.

### Threat model (minimum viable)
This table intentionally focuses on the threats most likely to be raised in internal review.

| Threat | Example | Current mitigation | Gaps / planned work |
|---|---|---|---|
| Cross-user session access | User A accesses `/api/sessions/{id}` for User B | Ownership checks + 404 on unauthorized | Add audit logs; add RBAC for privileged access |
| Identity spoofing | Attacker sets `X-User-Id` in prod | `AUTH_MODE=PROD` requires trusted header or JWT; optional escape hatch exists | Ensure escape hatch disabled; document gateway contract; add deployment guardrails |
| Sensitive data exfiltration to external services | Uploaded doc text sent to LLM provider | Behavior exists and must be disclosed | Add explicit user acknowledgement; add env kill-switches; add DLP/AV scanning integration (handoff team) |
| Malicious file upload | Malware in PDF/DOCX | None beyond basic extraction libraries | Add allow-list + size limits + AV scanning/DLP integration (planned) |
| Prompt injection (via uploads) | Document instructs model to leak secrets | No dedicated mitigations beyond model instructions | Harden instructions; minimize tool access; add prompt-injection test suite (planned) |
| XSS via rendered output | Model returns HTML/script | UI uses `react-markdown` without raw HTML plugin by default | Keep raw HTML disabled; add tests and dependency review |
| Data over-retention | Data persists indefinitely | No retention automation | Add retention policy + purge workflows (planned) |
| Background task loss/duplication | API restarts mid-execution | In-process `BackgroundTasks` only | Introduce JobRunner + durable queue/worker (planned Sprint 3) |

### Security controls checklist (current vs planned)
#### Current controls (implemented)
- Auth mode separation (DEV vs PROD).
- Ownership authorization on session resources.
- DB state stored in `session_state` with batched updates to reduce SQLite contention.
- UI renders markdown without enabling raw HTML execution (as currently coded).

#### Controls implemented (Sprint 1)
- RBAC: `user` / `admin` / `auditor` roles enforced on admin endpoints (PR-6).

#### Controls planned (handoff roadmap)
- File upload guardrails: allow-list + size limit + disable-uploads kill-switch.
- Web search kill-switch enforced server-side.
- Audit logging in DB (session access, uploads metadata, admin actions).
- Quotas/rate limiting and budget caps.
- Move large extracted document text out of `session_state` into a safer bounded storage model.

### Testing guidance (current)
Recommended minimum tests for security-critical behavior:
- Ownership isolation: ensure all session endpoints return 404 for non-owners.
- PROD auth enforcement: ensure requests fail without trusted header or valid JWT when `AUTH_MODE=PROD`.
- UI markdown safety: ensure no raw HTML rendering is enabled (avoid adding `rehype-raw`).

Existing helpers:
- `scripts/verify_multi_user.py` (multi-user isolation verification; requires backend running).

### References
- Auth + ownership enforcement: `src/web/api.py`, `src/web/db_service.py`
- State: `src/web/state_service.py`, `src/web/database.py`
- Upload + ingestion: `src/web/session_manager.py`, `src/agent_council/utils/file_ingestion.py`
- LLM tools: `src/agent_council/core/agent_builder.py` (WebSearchTool/FileSearchTool)
- UI markdown rendering: `web-ui/src/steps/Step4Execute.jsx`, `Step5Review.jsx`, `Step6Synthesize.jsx`
<!-- AI Generated Code by Deloitte + Cursor (END) -->


