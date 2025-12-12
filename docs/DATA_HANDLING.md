<!-- AI Generated Code by Deloitte + Cursor (BEGIN) -->
## Agent Council — Data Handling (Current State + Handoff Notes)

This document answers the most common Risk/Compliance questions: **what data we accept, where it goes, what leaves the environment, and how deletion works today**. It is intentionally explicit about “current behavior” vs “planned behavior” from `docs/HANDOFF_READINESS_PLAN.md`.

### Scope and non-goals
- **Scope**: current repository behavior (local dev and “as-is” deployment).
- **Non-goals**: defining Deloitte-wide retention/classification policy (tracked as open decisions).

### External data boundary (egress)
Agent Council sends data to external services in these cases:

- **LLM provider (OpenAI API)**:
  - Used for: council build, per-agent execution, peer review, chairman synthesis.
  - Also used for: **prompt condensation** when prompts are too large (`condense_prompt`).
  - Data sent can include: user question, extracted document contents, intermediate prompts, and model outputs.

- **Web search (optional, per-agent)**:
  - If an agent has `enable_web_search=true`, the OpenAI Agents `WebSearchTool()` can be used.
  - **Note**: There is currently **no environment-level kill-switch** to disable web search; it is controlled per-agent in council configuration (planned in Sprint 1 PR-7).

### What data the system accepts
- **User identity**
  - DEV: `X-User-Id` header (defaults to `dev-user@localhost`)
  - PROD: `X-Authenticated-User` (trusted gateway header) or `Authorization: Bearer <JWT>`
- **User question**: arbitrary text
- **Uploaded files**: any file types are accepted by the API today (no allow-list/size limit yet)

### Where data is stored (current)
#### Database (durable; DB-first state)
- **`users`**: external user identity (`external_id`) and optional display name.
- **`sessions`**: session metadata (question, current step/status, timestamps, last token/cost totals, soft-delete flag).
- **`session_state`**: primary JSON/JSONB store for the session’s full state.

The DB is SQLite by default (`agent_council.db`) and can be PostgreSQL when `DATABASE_URL` is set.

#### Filesystem (local artifacts; not shared in multi-instance deployments)
Per-session filesystem artifacts are stored under `sessions/{session_id}/`:
- `uploaded_files/`: raw uploaded file bytes (as saved)
- `logs/`: markdown logs of LLM calls (prompts + responses + tokens/cost)

These filesystem paths are **local to the API instance** and are not safe for multi-instance deployments without a shared storage layer (planned via StorageProvider seam in Sprint 3).

### Uploaded files and ingestion (current)
When a session is created via `POST /api/sessions`:

1. Each uploaded file is saved to `sessions/{session_id}/uploaded_files/{filename}`.
2. The server ingests files into structured JSON (`ingested_data`) via `FileIngestor`:
   - Supported extraction formats:
     - `.pdf` (text extraction via `pypdf`)
     - `.docx` (text extraction via `python-docx`)
     - `.txt`, `.md`, `.json`, `.py`, `.csv` (read as text)
   - Unsupported types result in a placeholder content string: `"[Unsupported file type]"`.
3. **The ingested result includes**:
   - `metadata.filename`, `metadata.extension`, `metadata.size_bytes`
   - `metadata.path` (**absolute server-side file path**, e.g. `/.../sessions/{id}/uploaded_files/...`)
   - `content` (extracted text)
4. `ingested_data` (including extracted text) is persisted in **DB `session_state.state["ingested_data"]`**.

Implications:
- Extracted document text is stored durably in the DB today.
- Absolute server paths are stored in metadata today (this is undesirable for enterprise hardening; called out as a future change).

### What is sent to the LLM provider (current)
The system constructs prompts that can include:
- the user question, and
- the full extracted contents of uploaded documents (from `ingested_data[*].content`).

This occurs at minimum during:
- Council build (`build_council`)
- Council execution (`execute_council`) for **each agent**
- Peer review (`peer_review`)
- Chairman synthesis (`synthesize`)
- Prompt condensation (if triggered)

### Logging (current)
LLM calls are logged to markdown files using `SessionLogger`. The logs include:
- stage + agent name + token/cost counts
- **raw prompt**
- **raw response**

Where logs go:
- Web flows: `sessions/{session_id}/logs/session_*.md`
- CLI flows: typically `logs/session_*.md` (depending on entrypoint)

This is a major privacy/compliance consideration and is expected to be gated/changed for production usage (planned in Sprint 2).

### Deletion and retention (current)
#### Retention
- There is currently **no automated retention policy** for DB state, uploaded files, or logs.
- Data remains until manually deleted.

#### Deletion
API supports `DELETE /api/sessions/{session_id}`:
- Default behavior is **soft delete**:
  - `sessions.is_deleted` is set true (session disappears from list)
  - `session_state.state["deleted"]` is set true
  - Files under `sessions/{id}/` are preserved
- With `?hard=true`:
  - The API deletes the local filesystem directory `sessions/{id}/`
  - **DB rows are not purged** (session is still soft-deleted; session_state remains with `"deleted": true`)

Important caveat:
- “Hard delete” today is **best-effort cleanup of local artifacts**, not a full DB purge. A future enterprise-ready implementation should implement true purge semantics and/or retention workflows aligned to policy.

### Current controls vs planned controls
#### Controls present today
- Ownership enforcement on session endpoints (no cross-user reads; unauthorized returns 404).
- PROD auth supports trusted header or JWT validation.
- In-process batched DB updates to reduce SQLite lock contention.

#### Controls planned in the handoff roadmap (not yet implemented)
- Upload allow-list and max size limits + `DISABLE_UPLOADS=true` kill-switch.
- Global web search kill-switch: `DISABLE_WEB_SEARCH=true` enforced server-side.
- Audit logging and admin visibility.
- Retention windows + safe deletion paths.
- Moving extracted text out of `session_state` to avoid DB bloat and reduce exposure surface.

### Open decisions (tracked; do not block Sprint 1)
- **Uploads allowed in prod?** (owner: Security/Risk)
- **Prompt/response logging policy** (owner: Security/Risk)
- **Retention window** (owner: Security/Risk)
- **Web search policy** (default off; whether it can ever be enabled in prod)

### References (code)
- Upload + ingestion path: `src/web/api.py` and `src/web/session_manager.py`
- File ingestion implementation: `src/agent_council/utils/file_ingestion.py`
- DB state store: `src/web/state_service.py` and `src/web/database.py`
- LLM prompt construction: `src/agent_council/core/council_builder.py`, `src/agent_council/core/council_runner.py`
- Prompt condensation: `src/agent_council/utils/context_condense.py`
- Logging: `src/agent_council/utils/session_logger.py`
<!-- AI Generated Code by Deloitte + Cursor (END) -->


