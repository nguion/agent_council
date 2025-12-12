<!-- AI Generated Code by Deloitte + Cursor (BEGIN) -->
## Agent Council — Internal Deployment Readiness Plan (Handoff Roadmap)

### Instructions for usage (mandatory for any agent/contributor)
- **Branch Strategy**: All work for this plan MUST happen on the `handoff-ready` branch. Do not commit directly to `main` until the full plan is complete and reviewed.
- **This plan is the single source of truth** for handoff-readiness work. If you execute tasks from it, you must keep it current so others can review progress.
- **Priority #1 (besides code quality): keep this file accurate.** Do not let work happen “in chat only” or in private notes.
- **Update the plan as you work**, not after:
  - When you start a task: mark it **in progress**.
  - When you finish: mark it **done** and add links (PR/commit) and notes (what changed, why).
  - When you discover new risks/requirements: add them to the plan with an owner and proposed mitigation.
  - When you change scope/order: record the change and rationale (so the next team understands).
- **Annotate decisions and unknowns**:
  - Keep a decision log (hosting/queue/storage/retention) and record the current default, owner, and due date.
- **Always include traceability**:
  - Reference the exact files touched and (when available) PR/commit identifiers.

### Status (active execution)
- **Last updated**: 2025-12-12 (UTC) by Cursor (GPT-5.2)
- **Current sprint**: Sprint 1 — Make the repo trustworthy + establish security posture (Handoff Polish)
- **In progress**:
  - (none)
- **Completed this sprint**:
  - `docs/ARCHITECTURE.md` rewritten to match current DB-first `session_state` + local filesystem artifacts (part of PR-1)
  - Added v1 docs for Data Handling, Security Model, Privacy, and Runbook (part of PR-1)
- **Open decisions**:
  - Hosting platform — Owner: SRE/Platform — Due: Handoff
  - Queue/worker system — Owner: Backend + SRE — Due: Sprint 3
  - Artifact storage — Owner: Backend + SRE — Due: Sprint 3
  - SSO mode — Owner: SSO/Identity — Due: Sprint 1–2
  - Uploads allowed in prod — Owner: Security/Risk — Due: Sprint 1
  - Prompt/response logging policy — Owner: Security/Risk — Due: Sprint 2
  - Retention window — Owner: Security/Risk — Due: Sprint 2
- **Risks / blockers**:
  - In-process BackgroundTasks are not durable/scale-safe (mitigation: JobRunner seam in Sprint 3)
  - Local filesystem artifacts won’t work in multi-instance deployments (mitigation: StorageProvider seam in Sprint 3)
  - Sensitive data boundary + logging policy not yet explicit enough (mitigation: docs + guardrails in Sprints 1–2)
  - `session_state` row bloat from extracted text (mitigation: refactor in Sprint 3)

#### Recommended “status block” format (keep at the top of the plan during active execution)
- **Last updated**: YYYY-MM-DD (UTC) by <name>
- **Current sprint**: Sprint N (dates)
- **In progress**: bullets
- **Completed this sprint**: bullets (+ PR/commit links)
- **Open decisions**: bullets (owner + due)
- **Risks / blockers**: bullets (mitigation)

### Read this first (context from the repo owner)
This plan is written as if Agent Council will be deployed internally at Deloitte to **~10,000 potential users**, but the goal of this repo (today) is **handoff readiness**, not a firm-wide rollout yet.

#### Why this exists
- The repo currently works as a prototype, but **enterprise expectations** (security, auditability, operability, scale, and developer experience) need to be made explicit and engineered for.
- We want this repo to be something a skilled internal team can pick up and **immediately trust**, not a fragile demo.

#### Hard constraints / commitments (from the owner)
- **LLM provider**: The **current OpenAI API integration is the right one for now** (we are not switching providers in this roadmap).
- **Hosting**: We **do not know the final hosting platform yet**. This plan intentionally stays **deployment-agnostic** and focuses on clean seams (containers, configuration, abstractions) so the handoff team can deploy on AKS/App Service/Container Apps/etc.
- **SSO**: Deloitte SSO will be **Microsoft-based (Entra ID / Azure AD)**.
  - The repo owner will not implement full Entra login UX end-to-end.
  - We will build a clean **SSO integration contract** and safe **stubbed dev mode**, so an identity team can wire it correctly later.
- **Repo ownership / intent**: The core work remains in the repo owner’s GitHub for now; this plan is about making the codebase **clean and handoff-ready** for an internal engineering team to adopt.
- **Do not break what works**: We should go far, but avoid overstepping—keep the app runnable locally throughout, and prefer incremental PRs over rewrites.
- **Security clarity is mandatory**: Risk/Compliance concerns (especially around **client documents**, uploads, and “oops I saw someone else’s session”) must be addressed explicitly in docs and enforced in code (ownership, RBAC, audit logs, kill-switches, retention).

#### What “done” means (where this plan starts and ends)
- **Start state**: Current repo state (FastAPI + React/Vite, DB-backed `session_state`, in-process background tasks, local `sessions/{id}` uploads/logs, OpenAI API calls).
- **End state (handoff-ready)**:
  - The repo has clear, accurate docs and runnable tooling (CI, scripts, containerized dev).
  - Security posture is explicit (what data is stored, what can leave Deloitte, and how isolation is enforced).
  - RBAC exists (including admin-only capabilities).
  - An **admin dashboard** exists for cumulative usage/cost/performance visibility.
  - Durable-job + shared-storage **abstractions (“seams”)** exist so the handoff team can implement real workers/queues/object storage without refactoring business logic.
  - We are **not** claiming “production rollout to 10k users is complete” inside this repo; we are preparing the foundation so the owning team can do it safely.
  - This aligns to “Phase 0–3” readiness work (security/ops/scale foundations) and intentionally does **not** include Phase 4 org-wide rollout activities.

#### How to use this plan
- Treat this document as an **execution backlog for the next 2–3 sprints**.
- Keep a running **decision log** (hosting, queue, storage, retention policy) so the handoff team doesn’t inherit uncertainty.
- Prefer **small PRs** with clear acceptance criteria and tests.
- If you’re new to enterprise deployment/security: follow the acceptance criteria literally, and treat the security/data-handling sections as **non-negotiable** (engage Risk/Identity early when uncertain).

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

## 10 upgrades to make this plan execution-ready (this update)
Each item below is a concrete enhancement that turns this document from “directionally correct” into an executable backlog/spec. The corresponding details are added in the **Execution-ready details** section later in this file.

1. **Assumptions & constraints** (no hosting decision yet; OpenAI API provider fixed; SSO integrated by another team) — define what this plan does/doesn’t assume.
2. **RACI (roles & responsibilities)** — clarify who owns security, SSO, backend, frontend, ops, and approvals.
3. **Decision log + open decisions** — prevent “tribal knowledge”; make sure unknowns are tracked without blocking progress.
4. **Execution backlog + PR sequencing** — convert each sprint into a set of shippable PRs with clear acceptance tests.
5. **Data handling matrix** — spell out exactly what data is stored where, what is sent externally, and retention/deletion expectations.
6. **Threat model + control checklist** — map top risks (exfiltration, cross-user access, uploads) to concrete mitigations and tests.
7. **RBAC spec + Entra app-role mapping** — make admin/auditor controls unambiguous and easy for SSO team to wire.
8. **Admin dashboard spec (usage + performance)** — define metrics, data sources, endpoints, and UI scope.
9. **Observability + SLOs** — define the minimum viable logging/metrics/tracing needed to run this safely at scale.
10. **CI/CD + deployment packaging + env-var matrix** — make the repo runnable by a real team immediately (local and CI) without guessing.

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
- [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
- [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
- [Microsoft identity platform (Entra ID)](https://learn.microsoft.com/en-us/entra/identity-platform/)
- [Microsoft Entra ID — App roles](https://learn.microsoft.com/en-us/entra/identity-platform/howto-add-app-roles-in-apps)
- [Microsoft guidance on secure application development](https://learn.microsoft.com/en-us/security/)
- [FastAPI — Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [OpenAI — “Your data” (API data handling)](https://platform.openai.com/docs/guides/your-data)

---

## Execution-ready details (researched + expanded)

### 1) Assumptions & constraints (what this plan assumes)
- **LLM provider**: The current OpenAI API integration is considered “correct for now”.
- **Hosting**: Unknown/undecided. All architecture changes should be **deployment-agnostic** (container-friendly, stateless where possible).
- **SSO**: Will be Deloitte Microsoft-based SSO (Entra ID / Azure AD). This repo should only provide **clean integration contracts** and a safe dev stub.
- **Risk posture**: Treat uploads/prompts/responses as potentially **sensitive client data** unless policy says otherwise.
- **Non-breaking constraint**: The app should remain runnable locally throughout the work. “Seams first; swaps later.”

### 2) RACI (roles & responsibilities)
Use this as the handoff team’s “who owns what” map. Replace names once a real team is assigned.

| Work area | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| Backend API + DB schema | Backend Eng | Tech Lead | Security/Risk, SRE | Product |
| Frontend UI + routing | Frontend Eng | Tech Lead | Security/Risk | Product |
| Identity/SSO integration (Entra) | SSO/Identity Eng | Security Lead | Backend Eng | Product |
| RBAC policy (roles/permissions) | Backend Eng | Security Lead | Product | All |
| File upload policy + DLP/AV scanning requirements | Security/Risk | Security Lead | Product, Backend Eng | All |
| Observability (logs/metrics/tracing) | SRE/Platform Eng | SRE Lead | Backend Eng | All |
| Rate limits + quota policy | Backend Eng | Product | Security/Risk | All |
| Admin dashboard metrics definitions | Product + Backend Eng | Product | SRE, Security/Risk | All |
| Data retention + deletion policy | Security/Risk | Security Lead | Product | All |

### 3) Decision log + open decisions (avoid churn)
Keep this table current as decisions get made. Default stance: **track unknowns without blocking Sprint 1 work**.

| Decision area | Current default | Rationale | Owner | Due |
|---|---|---|---|---|
| Hosting platform | TBD | Don’t block; keep changes portable | SRE/Platform | Handoff |
| Queue/worker system | TBD (seam first) | Avoid locking in Celery/Redis if platform team prefers alternatives | Backend + SRE | Sprint 3 |
| Artifact storage | TBD (seam first) | Object storage likely; don’t block dev | Backend + SRE | Sprint 3 |
| SSO mode | Trusted header OR JWT | Both supported already; final depends on gateway pattern | SSO/Identity | Sprint 1–2 |
| Uploads allowed? | Allowed in dev; controllable in prod | Risk posture differs by environment | Security/Risk | Sprint 1 |
| Prompt/response logging | Off by default in prod | Minimize sensitive data sprawl | Security/Risk | Sprint 2 |
| Retention window | TBD (configurable) | Must be approved | Security/Risk | Sprint 2 |

### 4) Execution backlog + PR sequencing (turn sprints into “doable PRs”)
This section is the “ready to execute” slice: each PR is scoped to be reviewable and reversible.

#### Sprint 1 — suggested PR sequence
1. **PR-1 Docs alignment** — **Done**
   - Update `docs/ARCHITECTURE.md` to match DB-primary state and in-process BackgroundTasks reality.
   - Add `docs/DATA_HANDLING.md`, `docs/SECURITY_MODEL.md`, `docs/PRIVACY_NOTES.md`, `docs/RUNBOOK.md` stubs (high-level first; iterate later).
   - **Execution plan (this session)**:
     - **Steps**:
       - Read current `docs/ARCHITECTURE.md` and identify mismatches vs code (backend state, auth, background execution, storage).
       - Update `docs/ARCHITECTURE.md` to accurately describe: API endpoints, DB-first state, filesystem artifacts, auth modes, background tasks, and frontend polling.
       - Create the 4 new docs as concise “v1” stubs with explicit current behavior + clearly-marked TODOs for policy decisions.
     - **Files to touch**:
       - `docs/ARCHITECTURE.md`
       - `docs/DATA_HANDLING.md` (new)
       - `docs/SECURITY_MODEL.md` (new)
       - `docs/PRIVACY_NOTES.md` (new)
       - `docs/RUNBOOK.md` (new)
     - **Acceptance criteria**:
       - `docs/ARCHITECTURE.md` matches current code paths (DB-first state + in-process BackgroundTasks + local filesystem artifacts) without aspirational/incorrect claims.
       - New docs exist, are internally consistent with the plan’s “Key data handling reality”, and clearly call out open decisions (retention, logging policy, hosting/queue/storage).
       - No product behavior changes (docs-only PR).
   - **Progress notes**:
     - 2025-12-12: Started PR-1. (Traceability will be added as files change.)
     - 2025-12-12: `docs/ARCHITECTURE.md` currently documents legacy `state.json`-primary behavior; current implementation is DB-backed `session_state` via `SessionStateService`. Updating docs to match current code.
     - 2025-12-12: Updated `docs/ARCHITECTURE.md` to describe current DB-first state + in-process background tasks + filesystem artifacts. Traceability: PR/commit TBD. Files: `docs/ARCHITECTURE.md`.
     - 2025-12-12: Added `docs/DATA_HANDLING.md`, `docs/SECURITY_MODEL.md`, `docs/PRIVACY_NOTES.md`, `docs/RUNBOOK.md` as v1 stubs. Traceability: Commit `f69354b`. Files: `docs/*`.
     - 2025-12-12: Completed PR-1. All docs present and aligned with code.
2. **PR-2 DX fixes**
   - Fix `scripts/verify_setup.py` (it currently references removed files and missing docs).
   - Add `.env.example` + `web-ui/.env.example`.
3. **PR-3 Containerized local dev**
   - Add backend `Dockerfile`, frontend `web-ui/Dockerfile` (or document why not).
   - Add minimal `docker-compose.yml` (Postgres + backend + frontend). Keep optional.
4. **PR-4 CI baseline**
   - GitHub Actions: ruff + pytest + frontend build (and eslint if desired).
   - Optional: Playwright e2e as nightly.
5. **PR-5 Alembic baseline**
   - Introduce Alembic migrations for current DB schema and future additions (roles/audit tables).
6. **PR-6 RBAC skeleton**
   - Add roles + `require_role()` dependency.
   - Add first admin-only endpoint (e.g., `/api/admin/metrics/summary` returning placeholders).
7. **PR-7 Security guardrails**
   - Upload allow-list + max size + env kill-switches.
   - `DISABLE_WEB_SEARCH=true` enforced server-side.

#### Sprint 2 — suggested PR sequence
1. **PR-8 Audit logging + event model**
2. **PR-9 Quotas/rate limiting**
3. **PR-10 Admin metrics endpoints (real)**
4. **PR-11 Admin dashboard UI route `/admin`**

#### Sprint 3 — suggested PR sequence
1. **PR-12 JobRunner abstraction (in-process default)**
2. **PR-13 StorageProvider abstraction (local default)**
3. **PR-14 State model refactor: remove full extracted text from `session_state`**

### 5) Data handling matrix (the Risk team’s #1 question)
This is the single most important “clarity artifact” for internal rollout discussions.

#### Data handling table (current and target)
| Data | Current behavior | Where stored (current) | Sent to external LLM? | Target behavior (handoff-ready) |
|---|---|---|---|---|
| User identity | `external_id` from header/JWT | DB (`users`) | No | Same |
| Session metadata | question, status, timestamps | DB (`sessions`) | Question: yes | Same; add pagination |
| Uploaded file bytes | saved server-side | Local disk (`sessions/{id}/uploaded_files`) | Indirectly (after extraction) | StorageProvider → object storage in prod |
| Extracted text | extracted and saved in state | DB JSON (`session_state.state.ingested_data`) | **Yes** | Move extracted text to separate store; keep only bounded summaries/snippets in state |
| Prompts/responses | constructed by core | In memory; may be logged | **Yes** | Default: do not persist raw prompts/responses in prod |
| Web search queries | optional tool use | N/A | Possibly (3rd parties) | Default off; admin kill-switch; user acknowledgement |
| LLM call logs | markdown file | Local disk (`sessions/{id}/logs`) | N/A | StorageProvider; redaction policy; retention controls |
| Audit events | none today | N/A | No | DB `audit_events` with minimal metadata |

#### Required user-facing disclosure (for later UI/legal review)
- If uploads are enabled: “Uploaded documents may be processed and their content may be sent to the configured LLM provider to generate results.”
- If web search is enabled: “Queries may be sent to external search providers.”

### 6) Threat model + control checklist (security made concrete)
This keeps the plan “proven and comprehensive” by naming the threats and the specific mitigations.

#### Top threats (minimum list)
| Threat | Example | Primary mitigation | How we test |
|---|---|---|---|
| Cross-user data access | user A loads user B’s session by URL | strict ownership checks; 404 on unauthorized | integration tests for isolation; negative tests |
| Header spoofing | attacker sets `X-User-Id` in prod | enforce `AUTH_MODE=PROD`; disable `AUTH_ALLOW_X_USER_ID_IN_PROD` | config tests; deploy guardrails |
| Sensitive data exfiltration | client doc text sent to external LLM | disclosure + policy + kill-switch + DLP (handoff) | config tests; user acknowledgement in UI |
| Malicious file upload | malware in PDF | allow-list + size limit; (handoff) AV scanning | unit tests for allow-list/limits |
| Prompt injection via uploads | uploaded doc tells model to leak secrets | treat uploads as untrusted; instruction hardening; least tool access | red-team test set; prompt-injection test cases |
| Budget runaway | accidental reruns or huge docs | idempotence + quotas + size limits | tests + admin metrics |
| XSS in rendered markdown | model returns HTML/script | keep `react-markdown` safe defaults (no raw HTML) | frontend security test; dependency review |

#### Control checklist (baseline)
- **Auth**: `AUTH_MODE=PROD` required in production; deny unauthenticated requests.
- **Authz**: ownership enforcement on all session endpoints; RBAC for admin endpoints.
- **Uploads**: allow-list extensions + MIME sniffing + max bytes; kill-switch env var.
- **Logging**: production default should avoid storing raw prompts/responses; audit log is metadata-only.
- **Retention**: documented and configurable; deletion paths tested.
- **Rate limiting/quotas**: per-user throttles for expensive operations; budget caps.

### 7) RBAC spec + Entra app roles mapping
#### Roles (initial)
- **user**: can create/read/update/delete their own sessions (soft delete).
- **admin**: can view aggregated metrics, configure global limits, and manage retention settings.
- **auditor** (optional): can view compliance metadata and audit logs (not raw content by default).

#### Permission matrix (illustrative)
| Capability | user | auditor | admin |
|---|---:|---:|---:|
| Create session | ✅ | ✅ | ✅ |
| View own sessions | ✅ | ✅ | ✅ |
| View other users’ session *content* | ❌ | ⚠️ (policy) | ⚠️ (policy) |
| View audit logs | ❌ | ✅ | ✅ |
| View admin metrics dashboard | ❌ | ✅ | ✅ |
| Change global limits (quotas, kill-switches) | ❌ | ❌ | ✅ |

#### Entra app roles mapping (handoff-ready stub)
- Use Entra “App roles” (preferred) so tokens contain a `roles` claim (more stable than group overage).
- Backend should map token `roles` → internal roles (`admin`, `auditor`).
- Dev stub: allow setting role via local config (never via arbitrary headers in PROD).

### 8) Admin dashboard spec (usage + performance)
#### Metrics to expose (minimum viable)
- **Usage**: sessions created/day, sessions executed/day, active users (DAU/WAU), tokens + cost totals by day, by model.
- **Performance**: duration p50/p95 for build/execute/review/synthesize, queue wait time (when queue exists).
- **Reliability**: error rate by endpoint and by job stage; top error messages (redacted).

#### Data sources (what we must record)
- Add a DB event model (either `audit_events` + structured fields or a dedicated `metrics_events` table) capturing:
  - timestamp, user_id, session_id, event_type, duration_ms, tokens, cost_usd, model, status.

#### Admin API endpoints (example)
- `GET /api/admin/metrics/summary`
- `GET /api/admin/metrics/time_series?metric=tokens&window=30d`
- `GET /api/admin/audit?since=...&limit=...`

#### Admin UI (scope)
- Route: `/admin`
- RBAC gated
- Read-only dashboards first (no destructive controls in v1).

### 9) Observability + SLOs (minimum viable)
#### Logging
- Structured logs (JSON) with:
  - `request_id`, `user_id` (or hashed), `session_id`, `stage`, `status`, `duration_ms`
- Do not log raw document contents or prompts in production by default.

#### Metrics (minimum)
- API: request count, latency histograms, error rate by endpoint
- Jobs: duration histograms per stage, success/fail counts
- Cost: tokens/cost per stage (already available via `SessionLogger` totals)

#### Initial SLO suggestions (for later tuning)
- `/api/sessions/{id}/summary`: p95 < 300ms (DB read only)
- `/api/sessions` list: p95 < 300ms with pagination
- job completion: “execute completes successfully” > 98% (excluding provider outages)

### 10) CI/CD + deployment packaging + environment variable matrix
#### CI quality gates (recommended)
- Python: ruff + pytest
- Frontend: eslint + build
- Optional: Playwright e2e (nightly)
- Security: dependency audit + secret scanning

#### Environment variable matrix (baseline)
| Variable | Dev | Prod | Notes |
|---|---:|---:|---|
| `OPENAI_API_KEY` | ✅ | ✅ | secret |
| `DATABASE_URL` | ✅ | ✅ | Postgres in prod strongly recommended |
| `AUTH_MODE` | ✅ | ✅ | must be `PROD` in prod |
| `AUTH_JWT_*` | ❌/✅ | ✅ | if JWT auth is used |
| `AUTH_ALLOW_X_USER_ID_IN_PROD` | ❌ | ❌ | keep false by default |
| `DISABLE_UPLOADS` | optional | optional | risk control |
| `DISABLE_WEB_SEARCH` | optional | optional | risk control |

---
<!-- AI Generated Code by Deloitte + Cursor (END) -->

