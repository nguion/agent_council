## Agent Council — Internal Deployment Readiness Plan (Handoff Roadmap)

### Audience
- This document is written for the internal engineering team that will ultimately own, secure, operate, and scale Agent Council for broad internal use (up to ~10k Deloitte users).
- It also serves as a “how we got from prototype → handoff-ready” guide for non-experts.

### Goal (what “handoff-ready” means)
By the end of this roadmap, the repo should be something a skilled internal team can pick up and immediately trust:
- **Clear security posture** (data handling explained, guardrails enforced, auditability built-in).
- **Production-oriented architecture seams** (durable job execution + shared storage abstractions) without committing to a specific hosting platform yet.
- **Operational readiness** (observability, rate limits/quotas, runbooks, migrations, CI).
- **Admin visibility** (usage/cost/performance dashboard, RBAC-protected).
- **Minimal surprises** (docs match code; scripts work; no hidden local-only assumptions).

### Non-goals (explicitly out of scope for this repo owner)
- Implementing “real” Deloitte SSO end-to-end (Azure AD / Entra ID) login UX flows.
  - We will **stub** the integration points cleanly (JWT validation already exists in backend) so the handoff team can wire it to the chosen SSO/gateway.
- Picking the final hosting target (AKS vs App Service vs Container Apps vs on‑prem). We’ll keep changes **deployment-agnostic**.

---

## What we will hand off (explicit artifacts)
This roadmap intentionally produces concrete artifacts a real team expects:
- **Architecture & ops docs**
  - `docs/ARCHITECTURE.md` (accurate; single source of truth)
  - `docs/RUNBOOK.md` (how to run, deploy, rollback, troubleshoot)
- **Security & Risk docs**
  - `docs/DATA_HANDLING.md` (data boundary, retention, egress)
  - `docs/SECURITY_MODEL.md` (threat model + mitigations + assumptions)
  - `docs/PRIVACY_NOTES.md` (what is logged, what is not; how to delete)
- **Engineering baseline**
  - CI that runs lint/tests on PRs
  - Alembic migrations (no “create tables on startup” in prod path)
  - Clear configuration via environment variables (`.env.example`, `web-ui/.env.example`)

---

## Current State Snapshot (what exists today)

### Backend
- FastAPI app in `src/web/api.py`.
- DB schema in `src/web/database.py`:
  - `users` (external_id, display_name)
  - `sessions` (metadata: question, step, status, cost/token summary, soft delete)
  - `session_state` (full JSON state, JSONB on Postgres)
- Auth in `src/web/api.py`:
  - `AUTH_MODE=DEV`: trusts `X-User-Id` header (or defaults to `dev-user@localhost`).
  - `AUTH_MODE=PROD`: accepts either:
    - `X-Authenticated-User` trusted header (reverse proxy / gateway pattern), OR
    - `Authorization: Bearer <JWT>` with validation via `AUTH_JWT_*`.
    - Optional escape hatch: `AUTH_ALLOW_X_USER_ID_IN_PROD=true` (should be **disabled** by default).
- Background work uses FastAPI `BackgroundTasks` (in-process) for:
  - execute (`/execute`)
  - peer review (`/peer_review`)
  - synthesize (`/synthesize`)
- File uploads are stored under `sessions/{id}/uploaded_files` via `src/web/session_manager.py`.
- Logs are written as markdown under `sessions/{id}/logs` via `agent_council.utils.session_logger.SessionLogger`.

### Frontend
- React/Vite app in `web-ui/`.
- Frontend talks directly to the API via `VITE_API_URL` (`web-ui/src/api.js`).
- UI uses polling for status/results (good enough now, but must be managed for scale).

### Key data handling reality
This is critical for Risk/Compliance alignment:
- Uploaded files are saved server-side and **their contents are extracted** (`agent_council.utils.file_ingestion.FileIngestor`).
- The extracted contents are stored inside `session_state.state["ingested_data"]` today (`src/web/api.py` create session flow).
- That state is then used to build prompts and is **sent to the LLM provider** when building/executing/reviewing.
- Additionally, markdown logs can contain prompts and model outputs (potentially sensitive).

---

## “What breaks first” at 10k internal users (risk-ranked)

### 1) In-process background tasks (durability + scale)
FastAPI `BackgroundTasks` runs inside the web process. Under:
- multi-worker deployments,
- restarts,
- timeouts,
- horizontal scaling,
…jobs can be dropped, duplicated, or starve API throughput.

### 2) Local filesystem usage in a scaled deployment
`sessions/{id}/...` is local disk. In any multi-instance deployment, local disk is:
- not shared across instances, and/or
- ephemeral.
Uploads/logs may “disappear” depending on which instance serves the next request.

### 3) Compliance and sensitive-data exposure
Today the system can store and log:
- extracted document contents,
- prompts/responses,
without firm-wide controls like retention, redaction, legal hold, access auditing, or explicit user classification.

### 4) DB/JSON growth and performance
Storing full extracted text inside JSON (`session_state`) will bloat rows quickly and degrade performance. This gets worse with:
- large PDFs,
- high usage,
- long retention windows.

### 5) Traffic amplification via polling
Polling is fine early on; at high user counts it becomes a major driver of:
- API load,
- DB read load,
- cost.

---

## Target Architecture (deployment-agnostic, but “enterprise-shaped”)

### Principles
- **Backend is the policy enforcement point**: all authz, quotas, retention, and audit logging happens server-side.
- **Durable async execution**: long-running steps must be queue/worker-based, not tied to web process uptime.
- **Shared storage** for artifacts: uploads and logs must live in object storage (or equivalent), not local disk.
- **Split hot metadata vs large blobs**: session_state should not hold multi-megabyte texts.
- **Safe defaults**: web search off by default; file uploads restricted/guarded; logging minimized by default in production.

### Proposed components (logical)
- **API service** (FastAPI): handles HTTP, auth, authorization, reads/writes state, enqueues jobs.
- **Worker service**: executes council steps, writes progress/state updates, handles retries.
- **PostgreSQL**: primary data store for users/sessions/state/metrics/audit events.
- **Object storage**: uploaded docs + logs (and possibly extracted text).
- **Queue**: Redis/Celery or enterprise queue (to be chosen by handoff team).
- **Identity**: Deloitte SSO via gateway-injected header or JWT access tokens (Entra ID / Azure AD).

---

## Workstreams (what we build, in parallel)

### Workstream A — Security, compliance, and “data boundary clarity”
Deliverables:
- A clear, written **Data Handling & Exfiltration Statement**:
  - What data is accepted
  - Where it is stored
  - Who can access it
  - What is sent to external services (LLM provider, optional web search)
  - Retention / deletion behavior
- Guardrails:
  - File type allow-list, max size, and limits
  - Optional “no uploads” mode for strict environments
  - “web search disabled” mode for strict environments
- Auditability:
  - Audit events for session access, uploads, admin actions
- Logging safety:
  - Production default: **no raw prompt/response logging** unless explicitly enabled and routed to approved storage

### Workstream B — Identity, authorization, and RBAC
Deliverables:
- Keep existing `AUTH_MODE=PROD` patterns (JWT and/or trusted header).
- Add **RBAC** (roles like `user`, `admin`, `auditor`) and enforce on:
  - admin metrics endpoints
  - session deletion (hard delete)
  - export/bulk operations
- “Stub SSO” approach for this repo:
  - Maintain JWT validation and/or `X-Authenticated-User` header support.
  - Provide documented integration contract for the real SSO team.

### Workstream C — Durable jobs + shared storage (without committing to hosting)
Deliverables:
- Introduce a **JobRunner abstraction** with two implementations:
  - `InProcessJobRunner` (current behavior; safe fallback)
  - `QueueJobRunner` (interface + skeleton; runnable locally with Redis/Celery if desired)
- Introduce a **StorageProvider abstraction**:
  - `LocalStorageProvider` (current filesystem behavior)
  - `ObjectStorageProvider` interface (stub for Azure Blob/S3/GCS)

### Workstream D — Observability and operability
Deliverables:
- Structured logging + correlation IDs
- Metrics (per endpoint + per job stage) and basic dashboards
- Error budgets / alerting hooks (for the handoff team)
- Migrations (Alembic) instead of `create_all()` for production workflows

### Workstream E — Admin dashboard (usage + performance)
Deliverables:
- Admin-only API endpoints for aggregated metrics:
  - total sessions, active users, token/cost totals, error rates, p50/p95 latencies by step
  - queue depth / job duration (when queue exists)
- Admin UI route in `web-ui` (RBAC-gated)

---

## Sprint Plan (2–3 sprints to “handoff-ready”, not “fully deployed”)

### Sprint 1 — Make the repo trustworthy + establish security posture (Handoff Polish)
**Objective:** remove surprises; align docs with code; add the minimum security scaffolding + RBAC foundation.

Deliverables:
- **Docs accuracy audit**
  - Update/replace `docs/ARCHITECTURE.md` so it matches the real state source of truth and background execution model.
  - Add `docs/DATA_HANDLING.md` with an explicit “where data goes” section.
  - Add `docs/SECURITY_MODEL.md` (threat model + mitigations + assumptions).
- **Fix dev scripts and DX**
  - Update `scripts/verify_setup.py` (it currently references removed scripts/docs).
  - Add `Makefile` (or `taskfile`) targets: `dev`, `lint`, `test`, `clean`.
  - Add `.env.example` and `web-ui/.env.example` (no secrets).
  - Add a minimal `docker-compose.yml` for local dev (Postgres + backend + frontend), without assuming the production hosting platform.
  - Add a backend `Dockerfile` and a frontend `web-ui/Dockerfile` (or document why not).
- **CI baseline**
  - Add a GitHub Actions workflow that runs:
    - Python lint (ruff) + unit/integration tests (pytest)
    - Frontend lint (eslint) + build
    - Optional: Playwright e2e (can be nightly if too heavy for every PR)
- **Database migrations baseline**
  - Introduce Alembic migrations for `users/sessions/session_state` and future tables (audit events, roles).
  - Define a policy: “no schema changes without a migration”.
- **RBAC foundation**
  - Add a `role` column to `users` (or separate `user_roles` table).
  - Default role assignment: `user`.
  - Add a simple `require_role("admin")` dependency for FastAPI.
- **Security guardrails (baseline)**
  - Enforce upload allow-list and size limit at API boundary.
  - Add an environment kill-switch: `DISABLE_UPLOADS=true`.
  - Add an environment kill-switch: `DISABLE_WEB_SEARCH=true` (enforced in council execution; UI toggle cannot override).

Acceptance criteria:
- A new engineer can run “verify setup” and follow docs without hitting dead ends.
- Data handling is clearly documented, including external LLM provider boundary.
- RBAC exists and at least one endpoint is admin-only (to prove wiring).
 - CI runs on PRs and is green on main.

### Sprint 2 — Admin telemetry + audit logs + quotas/rate limits (Risk & Ops)
**Objective:** make security and operational controls real, not aspirational; provide admin visibility.

Deliverables:
- **Audit log**
  - DB table `audit_events`: actor, action, session_id, timestamp, metadata (redacted), request_id.
  - Emit events for:
    - session created
    - session accessed (`/summary`, `/results`)
    - file uploaded (metadata only)
    - execute/review/synthesize requested
    - delete requested
    - admin dashboard viewed
- **Quotas / rate limiting (cleanly designed)**
  - Add per-user throttles for “expensive operations” (execute/review/synthesize).
  - Add per-user budget controls (token/cost caps) using the existing `last_cost_usd`/token totals.
  - Prefer “deny with clear message” over silent failure.
- **Admin API + UI**
  - API endpoints under `/api/admin/*` protected by RBAC.
  - Web UI route `/admin`:
    - aggregated usage (tokens/cost) over time
    - top errors
    - slowest steps
    - active background tasks (even if still in-process)

Acceptance criteria:
- Admin can see aggregate usage/cost and basic performance KPIs.
- Audit trail exists for key actions.
- System prevents runaway spend from a single user/session.

### Sprint 3 — Durable jobs + shared storage seams (Scale Foundations)
**Objective:** enable the handoff team to deploy safely on any platform by swapping implementations, not rewriting app logic.

Deliverables:
- **Job system abstraction**
  - Define job model + statuses (queued/running/succeeded/failed).
  - Introduce a `JobRunner` interface and keep existing in-process runner as default.
  - Add a queue-backed “skeleton” implementation and docs for wiring (Redis/Celery or internal queue).
- **Storage abstraction**
  - Introduce `StorageProvider` and route uploads/logs through it.
  - Keep local storage for dev; add an object-storage stub for prod.
- **State model refactor (critical)**
  - Stop storing full extracted document text in `session_state.state`.
  - Store only:
    - file metadata + storage keys
    - derived snippets/summaries (bounded size)
  - Add a `session_documents` table (or object storage keys) for extracted text.
  - Add retention controls and deletion paths.

Acceptance criteria:
- The system can be run in “stateless API + workers” mode without relying on local disk.
- Large file uploads do not inflate `session_state` rows.
- Handoff team can pick queue/storage provider and implement without refactoring business logic.

---

## Security Clarity (what Risk will ask, answered explicitly)

### Data egress (“what can leave Deloitte”)
Until you switch providers, assume:
- User question + extracted text + intermediate prompts/responses are **sent to the LLM provider** during runs.
- If web search is enabled, search queries may be sent to third parties.

Action items (in sprints above):
- Force **explicit user acknowledgement** in UI before enabling uploads or web search.
- Default to **web search off**; allow admins to disable it entirely via env.
- Provide a “no uploads” mode for restricted environments.

### Data isolation (“oops I logged into someone else’s account”)
The system must guarantee:
- session access is always filtered by current user ownership
- admin access is explicit and audited

Action items:
- Maintain `404` on unauthorized access (no enumeration).
- Add RBAC with explicit admin role.
- Add audit logs for access and admin actions.

### File uploads (secure handling)
Minimum controls (Sprint 1–3):
- file type allow-list and size limits
- store files in restricted, private storage
- avoid storing absolute server paths in metadata
- retention and deletion policies
- (handoff team) add malware scanning and DLP classification integration

---

## Handoff Checklist (what the receiving team should see)
- A single authoritative architecture doc (accurate).
- A clear data-handling/security document.
- CI: lint + tests run on PRs.
- Alembic migrations present and documented.
- JobRunner and StorageProvider abstractions present.
- Admin dashboard present and RBAC-protected.
- Audit logging present with retention guidance.
- Runbooks: local dev, staging deploy, rollback strategy (deployment-agnostic).

---

## Open Decisions for the Handoff Team (tracked, not blocked)
- Hosting platform choice (AKS vs App Service vs Container Apps vs on-prem).
- Queue choice (Redis/Celery vs enterprise queue).
- Storage choice (Azure Blob vs other).
- SSO implementation choice:
  - gateway-injected identity header vs direct OIDC to backend
- Data classification policy:
  - what documents are allowed
  - retention windows
  - whether prompt/response logs are permitted

---

## Suggested reference standards (for the receiving team)
These are useful “north stars” for internal security review and production readiness:
- [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [Microsoft identity platform (Entra ID)](https://learn.microsoft.com/en-us/entra/identity-platform/)
- [Microsoft guidance on secure application development](https://learn.microsoft.com/en-us/security/)


