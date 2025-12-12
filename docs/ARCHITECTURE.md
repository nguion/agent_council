<!-- AI Generated Code by Deloitte + Cursor (BEGIN) -->
## Agent Council — System Architecture (Current State)

This document describes **what the repository does today** (not the target future architecture). It is intended to be a reliable reference for new engineers and for Sprint planning in `docs/HANDOFF_READINESS_PLAN.md`.

### Overview
Agent Council orchestrates a panel of LLM “personas” to answer complex questions through a 5-step flow:

- **Build**: generate a council (personas + tools) from the question
- **Edit**: user edits the council configuration
- **Execute**: each agent answers in parallel
- **Peer review**: agents critique each other’s answers
- **Synthesis**: chairman produces a final verdict

The project includes both:
- **Web UI** (React/Vite) for the 5-step flow
- **CLI** entrypoints for local usage

### High-level architecture
```
Browser (React/Vite) ──HTTP──> FastAPI API ──calls──> OpenAI API (via openai-agents SDK)
        │                      │
        │                      ├── PostgreSQL/SQLite (DB-backed state + metadata)
        │                      │
        │                      └── Local filesystem artifacts (dev): sessions/{id}/uploads + logs
        │
        └── Polling during long-running operations (execute/review/synthesize)
```

### Repository layout (where things live)
- **Core orchestration**: `src/agent_council/`
  - `core/`: council building, execution, review, synthesis
  - `utils/`: file ingestion, session logging, context condensing
- **Web backend**: `src/web/`
  - `api.py`: FastAPI app + endpoints + auth
  - `database.py`: SQLAlchemy models + DB initialization
  - `state_service.py`: DB-first session state service (`session_state` JSON/JSONB)
  - `session_manager.py`: filesystem artifacts (uploads/log directories)
- **Web frontend**: `web-ui/`
  - `src/steps/`: Step1–Step6 screens
  - `src/api.js`: Axios client with `VITE_API_URL`

### Persistence model (DB-first + filesystem artifacts)
#### Database (source of truth for state)
Session state is stored in the database as JSON/JSONB:
- `users`: user identity (`external_id`)
- `sessions`: **metadata** for listing/filtering (question, status, current_step, cost/tokens, timestamps)
- `session_state`: **full session state** as JSON/JSONB (single source of truth)

Code references:
- Models: `src/web/database.py`
- State service: `src/web/state_service.py`

Important notes:
- The backend currently initializes tables on startup (`Base.metadata.create_all`) rather than running Alembic migrations (planned in the handoff roadmap).
- The JSON `session_state.state` currently includes `ingested_data` (extracted document contents). This is called out as a scale/compliance risk in the handoff plan.

#### Filesystem artifacts (dev/local)
The backend also writes session artifacts under `sessions/{session_id}/`:
- `uploaded_files/`: raw uploaded files
- `logs/`: markdown logs produced by `SessionLogger`

These artifacts are **not** a durable/shared storage mechanism in a scaled deployment. They are local-dev oriented and are explicitly called out as a handoff risk and a future abstraction seam.

Code references:
- Filesystem manager: `src/web/session_manager.py`
- Logger: `src/agent_council/utils/session_logger.py` (and usage inside `src/web/api.py`)

### Authentication & authorization
Auth is handled by the backend (`src/web/api.py`) with two modes:

- **DEV (`AUTH_MODE=DEV`, default)**:
  - Accepts `X-User-Id` as the external user identity (email/UPN)
  - If missing, defaults to `dev-user@localhost`

- **PROD (`AUTH_MODE=PROD`)**:
  - Requires either:
    - `X-Authenticated-User` (trusted identity header injected by a gateway/reverse proxy), OR
    - `Authorization: Bearer <JWT>` validated via `AUTH_JWT_*` environment variables
  - Optional escape hatch: `AUTH_ALLOW_X_USER_ID_IN_PROD=true` (should remain **false** by default)

Authorization model:
- Session endpoints enforce **ownership**: a user can only access sessions they own.
- Unauthorized access is returned as **404** (prevents enumeration).
- Deletion is implemented as **soft delete** in the `sessions` table (with an optional "hard" flag that also removes filesystem artifacts and marks DB state as deleted).

**RBAC (Role-Based Access Control)**:
- Roles: `user` (default), `admin`, `auditor`
- Users table includes `role` column (indexed for fast queries)
- `require_role()` FastAPI dependency enforces role-based access on protected endpoints
- Admin-only endpoints (e.g., `/api/admin/metrics/summary`) require `role='admin'`
- New users are automatically assigned `role='user'` on first access
- Role management: use `scripts/promote_user_to_admin.py` for dev/testing (production should use SSO app-role mapping)

Code references:
- RBAC dependency: `src/web/api.py` (`require_role()`)
- User model: `src/web/database.py` (`User.role`)
- User service: `src/web/db_service.py` (`UserService.get_or_create_user()`)

### Execution model (in-process background tasks)
Long-running work is started via FastAPI `BackgroundTasks`:
- `POST /api/sessions/{id}/execute` → background `execute_council_task()`
- `POST /api/sessions/{id}/peer_review` → background `peer_review_task()`
- `POST /api/sessions/{id}/synthesize` → background synthesis task

Progress updates:
- Progress callbacks coalesce updates using `SessionStateService.update_state_batched(...)` to reduce write pressure (especially on SQLite).

Operational implications:
- BackgroundTasks are **in-process** (not durable across restarts and not safe for multi-worker/multi-instance production deployments).
- The handoff roadmap introduces a JobRunner abstraction + queue-backed worker skeleton as the scalable path forward.

### Web search tool (optional per-agent)
The council supports optional tool access per agent:
- `enable_web_search`: adds the OpenAI Agents `WebSearchTool()` to that agent
- Default is **disabled** unless explicitly enabled in council configuration

There is currently **no environment-level kill-switch** for web search in the codebase (planned in the handoff roadmap).

Code references:
- Tool wiring: `src/agent_council/core/agent_builder.py`
- Per-agent config: `src/agent_council/core/agent_config.py`
- Runner wiring: `src/agent_council/core/council_runner.py`

### Primary API endpoints (web flow)
Key endpoints (see `src/web/api.py`):
- `POST /api/sessions`: create session (optional uploads + ingestion)
- `POST /api/sessions/{id}/build_council`: build council configuration
- `PUT /api/sessions/{id}/council`: update council configuration
- `POST /api/sessions/{id}/execute`: execute council (background task)
- `POST /api/sessions/{id}/peer_review`: peer review (background task)
- `POST /api/sessions/{id}/synthesize`: chairman synthesis (background task)
- `GET /api/sessions/{id}/status`: progress/status (polled by UI)
- `GET /api/sessions/{id}/results`: execution results
- `GET /api/sessions/{id}/summary`: full state (UI hydration)
- `GET /api/sessions`: list sessions for current user
- `DELETE /api/sessions/{id}`: soft-delete session (optional hard)

### Known architectural risks (explicit)
These are intentionally documented because they drive the handoff roadmap:
- **In-process background tasks** are not durable/scale-safe.
- **Local filesystem artifacts** are not shared in multi-instance deployments.
- **Session state JSON bloat** risk (extracted document text in `session_state`).
- **Polling amplification** at high user counts.

### Related docs
- Execution backlog and target-state seams: `docs/HANDOFF_READINESS_PLAN.md`
- Data boundary and egress notes: `docs/DATA_HANDLING.md`
- Threat model and security assumptions: `docs/SECURITY_MODEL.md`
- Logging/retention/deletion notes: `docs/PRIVACY_NOTES.md`
- “How to run” and ops basics: `docs/RUNBOOK.md`
<!-- AI Generated Code by Deloitte + Cursor (END) -->


