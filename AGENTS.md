# Agent Council – AGENTS.md

> **ReadMe for Robots**: This file provides AI coding agents (Cursor, Claude, Copilot) with the context they need to work effectively in this codebase.

<!-- AI Generated Code by Deloitte + Cursor (BEGIN) -->
### Plan execution protocol (mandatory)
- **If you are handed a `.md` build plan** (for example: `docs/HANDOFF_READINESS_PLAN.md`), you MUST maintain progress **inside that plan file** so others can review.
- **Priority #1 (besides absolute code quality): keep the plan current.**
  - Mark tasks **in progress / done**
  - Record scope/order changes with rationale
  - Add decision log entries (owner + due date)
  - Add traceability (PR/commit + files touched)
- **Do not rely on chat history** as the only record of progress; treat the plan file as the durable tracker.
<!-- AI Generated Code by Deloitte + Cursor (END) -->

---

## What This Project Does

Agent Council orchestrates a panel of GPT-5.1 agents to answer complex questions through structured deliberation:

1. **Build** – GPT-5.1 designs a council of specialized personas (JSON output).
2. **Edit** – User can tweak personas before execution.
3. **Execute** – Each agent runs in parallel with optional web search and file context.
4. **Peer Review** – Agents critique each other's responses.
5. **Chairman Synthesis** – A chairman agent produces the final verdict.

The system tracks token usage and cost throughout. It provides both a **CLI** and a **Web UI**.

---

## Quick Start

### One-Command Setup

**macOS / Linux:**
```bash
bash setup.sh
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy Bypass -File setup.ps1
```

Both scripts create `.venv`, install dependencies, prompt for `OPENAI_API_KEY`, and optionally run the app.

### Manual Setup (Any OS)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-web.txt
pip install -e .
echo "OPENAI_API_KEY=sk-..." > .env
```

### Running the Application

**CLI (Interactive 5-Step Flow):**
```bash
python agentcouncil.py cli
```

**Full Web Stack (Recommended):**
```bash
python agentcouncil.py start
```
This command:
- Creates/activates `.venv`
- Installs Python and Node dependencies
- Starts a PostgreSQL container (via Docker)
- Launches the FastAPI backend (port 8000)
- Launches the Vite frontend (port 5173)

Then open: http://localhost:5173

**Teardown:**
```bash
python agentcouncil.py stop
```

**Manual Web Start (Alternative):**
```bash
# Terminal 1: Backend
python run_api.py

# Terminal 2: Frontend
cd web-ui && npm run dev
```

---

## Architecture

### Tech Stack

| Layer    | Technology                                      |
|----------|-------------------------------------------------|
| LLM      | OpenAI GPT-5.1 via `openai-agents` SDK          |
| Backend  | FastAPI (async), SQLAlchemy 2.0, Pydantic v2    |
| Database | SQLite (dev) / PostgreSQL (prod)                |
| Frontend | React 19, Vite, Tailwind CSS 4, React Router 7  |
| Logging  | Rich (CLI), Markdown logs (files)               |

### Hybrid Storage Model

The application uses a **dual-storage architecture**:

1. **Database (SQLite/PostgreSQL):**
   - User identity and ownership (`users` table)
   - Session metadata: question, status, timestamps (`sessions` table)
   - Full session state as JSON/JSONB (`session_state` table)
   - Fast queries for listing, filtering, authorization

2. **Filesystem (`sessions/{id}/`):**
   - `uploaded_files/` – User-uploaded documents
   - `logs/` – Per-session LLM call logs (Markdown)

### State Management

- **Backend is source of truth** – All durable state lives in the database.
- **Frontend hydrates from backend** – Components fetch `/api/sessions/{id}/summary` on mount.
- **Operations are idempotent** – All mutating endpoints check existing state before running expensive LLM calls. Use `?force=true` to override.
- **Controlled polling** – Frontend polls only during active background operations (execution, review).

### URL Routes (Frontend)

| Route                          | Purpose                     |
|--------------------------------|-----------------------------|
| `/`                            | New session input (Step 1)  |
| `/sessions`                    | List all user sessions      |
| `/sessions/:id/build`          | Council build (Step 2)      |
| `/sessions/:id/edit`           | Council edit (Step 3)       |
| `/sessions/:id/execute`        | Execution (Step 4)          |
| `/sessions/:id/review`         | Peer review & verdict (Step 5) |

### API Endpoints

All mutating endpoints are **idempotent**:

| Method | Endpoint                              | Purpose                                  |
|--------|---------------------------------------|------------------------------------------|
| POST   | `/api/sessions`                       | Create session with file uploads         |
| POST   | `/api/sessions/{id}/build_council`    | Generate council (returns cached if exists) |
| PUT    | `/api/sessions/{id}/council`          | Update council configuration             |
| POST   | `/api/sessions/{id}/execute`          | Execute council (background task)        |
| GET    | `/api/sessions/{id}/status`           | Poll execution/review progress           |
| GET    | `/api/sessions/{id}/results`          | Get execution results                    |
| POST   | `/api/sessions/{id}/peer_review`      | Start peer review (background task)      |
| GET    | `/api/sessions/{id}/reviews`          | Get peer review results                  |
| POST   | `/api/sessions/{id}/synthesize`       | Generate Chairman's verdict              |
| GET    | `/api/sessions/{id}/summary`          | Get complete session data (hydration)    |
| GET    | `/api/sessions`                       | List current user's sessions             |
| DELETE | `/api/sessions/{id}`                  | Soft-delete session                      |

Interactive API docs: http://localhost:8000/docs

---

## Key Files

### Core Logic (`src/agent_council/`)

| File                          | Purpose                                      |
|-------------------------------|----------------------------------------------|
| `core/agent_config.py`        | `AgentConfig` dataclass (model defaults to `gpt-5.1`) |
| `core/council_builder.py`     | Uses GPT-5.1 to design council personas (JSON) |
| `core/council_runner.py`      | Builds per-agent instructions, executes in parallel |
| `core/agent_runner.py`        | Runs single agent, captures tool usage + tokens |
| `core/council_reviewer.py`    | Peer review logic                            |
| `core/council_chairman.py`    | Final synthesis                              |
| `utils/session_logger.py`     | Token/cost tracking with model pricing       |
| `utils/file_ingestion.py`     | PDF/DOCX parsing for context                 |
| `utils/context_condense.py`   | Summarization fallback for large contexts    |

### Web Backend (`src/web/`)

| File                  | Purpose                                      |
|-----------------------|----------------------------------------------|
| `api.py`              | FastAPI app with all endpoints + auth        |
| `services.py`         | Service layer wrapping core functions        |
| `session_manager.py`  | File-based session operations (uploads/logs) |
| `database.py`         | SQLAlchemy models: `User`, `Session`, `SessionState` |
| `db_service.py`       | User and session DB operations               |
| `state_service.py`    | Unified state access (DB-first, file fallback) |

### Web Frontend (`web-ui/src/`)

| File/Dir              | Purpose                                      |
|-----------------------|----------------------------------------------|
| `App.jsx`             | React Router setup                           |
| `api.js`              | Axios-based API client                       |
| `layouts/`            | `SessionLayout.jsx` (wraps session routes)   |
| `steps/`              | Step1Input through Step6Synthesize           |
| `components/`         | Shared UI: `SessionSidebar`, `UserSessionsSidebar` |
| `pages/`              | `SessionsList.jsx`                           |

### Scripts & Utilities

| File                          | Purpose                                      |
|-------------------------------|----------------------------------------------|
| `agentcouncil.py`             | Main CLI: `start`, `stop`, `cli` subcommands |
| `run_api.py`                  | Standalone backend startup (uvicorn)         |
| `scripts/migrate_state_json_to_db.py` | Migrate old file-based state to database     |
| `scripts/verify_setup.py`     | Verify installation is complete              |
| `scripts/verify_multi_user.py`| Test multi-user session isolation            |

---

## Environment & Configuration

### Required Environment Variables

| Variable         | Description                                      |
|------------------|--------------------------------------------------|
| `OPENAI_API_KEY` | OpenAI API key (required)                        |
| `DATABASE_URL`   | Database connection string (default: SQLite)     |

### Optional Environment Variables

| Variable               | Description                                   |
|------------------------|-----------------------------------------------|
| `AUTH_MODE`            | `DEV` (default) or `PROD`                     |
| `AUTH_JWT_SECRET`      | JWT secret for PROD auth (HS256)              |
| `AUTH_JWT_PUBLIC_KEY`  | JWT public key for PROD auth (RS256)          |
| `AUTH_JWT_ALG`         | Algorithm override                            |
| `AUTH_JWT_AUDIENCE`    | JWT audience claim validation                 |
| `AUTH_JWT_ISSUER`      | JWT issuer claim validation                   |
| `DB_POOL_SIZE`         | Database connection pool size (default: 10)   |
| `DB_MAX_OVERFLOW`      | Max overflow connections (default: 20)        |

### Model Configuration

- **Default model:** `gpt-5.1` (set in `AgentConfig`)
- **Reasoning effort:** `low`, `medium` (default), `high`
- **Verbosity:** `low` (default), `medium`, `high`

---

## Development Workflows

### Adding a New Persona Field or Tool

1. Update `AgentConfig` in `src/agent_council/core/agent_config.py`
2. Update `CouncilBuilder` JSON schema in `council_builder.py`
3. Update `CouncilRunner` instruction builder in `council_runner.py`
4. Update web UI components if needed (`Step2Build.jsx`, `Step3Edit.jsx`)

### Running Tests

**Verify Setup:**
```bash
python scripts/verify_setup.py
```

**Multi-User Isolation Tests:** (requires backend running)
```bash
python scripts/verify_multi_user.py
```

**API Integration Tests:**
```bash
pytest tests/
```

**E2E Tests (Playwright):**
```bash
cd web-ui && npx playwright test
```

### Database Migration (Old Sessions)

If you have existing file-based sessions from before the DB migration:

```bash
python scripts/migrate_state_json_to_db.py
```

This script:
- Scans `sessions/` for `state.json` files
- Creates `SessionState` records in the database
- Assigns orphaned sessions to an admin user
- Preserves original files for safety

---

## Multi-User Features

### Authentication

**Development Mode (default):**
- Pass `X-User-Id` header with email/UPN
- Defaults to `dev-user@localhost` if no header

**Production Mode:**
- Set `AUTH_MODE=PROD`
- Configure JWT validation via environment variables
- Integrate with Azure AD/Okta via OIDC

### Authorization

- All session endpoints enforce ownership
- Users see only their own sessions
- Cross-user access returns 404
- Deletion requires ownership

### Database Schema

```
users
├── id (UUID)
├── external_id (email/UPN, unique)
├── display_name
└── created_at, updated_at

sessions
├── id (session_id)
├── user_id (FK → users)
├── question
├── current_step
├── status
├── is_deleted
├── last_cost_usd
├── last_total_tokens
└── created_at, updated_at

session_state
├── session_id (PK)
├── state (JSON/JSONB)
└── updated_at
```

---

## Experimental Features

### Streaming Demo (`STREAMING_TEST/`)

This directory contains an experimental proof-of-concept for GPT-5.1 streaming responses using the lower-level Responses API.

**Purpose:** Explore token-level streaming for terminal/UI rendering without modifying the core Agent Council pipeline.

**Files:**
- `streaming_demo.py` – Minimal streaming sample with inline docs
- `README.md` – Usage instructions

**Run:**
```bash
cd STREAMING_TEST
python streaming_demo.py "Write a 2-line poem"
# Add --debug-events to see all event types
```

**Note:** This is separate from the main app because the OpenAI Agents SDK (`AgentBuilder` + `Runner`) does not currently surface token-level streaming.

---

## Production Deployment

### Backend

```bash
# Use gunicorn with uvicorn workers
gunicorn src.web.api:app -w 4 -k uvicorn.workers.UvicornWorker

# Required environment
export DATABASE_URL="postgresql+asyncpg://user:pass@host/agent_council"
export AUTH_MODE=PROD
export AUTH_JWT_SECRET="your-secret"  # or AUTH_JWT_PUBLIC_KEY for RS256
```

### Frontend

```bash
cd web-ui
npm run build
# Serve dist/ with nginx/Apache
# Set VITE_API_URL to production API URL before building
```

### Database Setup (PostgreSQL)

```bash
createdb agent_council
export DATABASE_URL="postgresql+asyncpg://user:password@localhost/agent_council"
# Tables auto-create on first startup
```

### Production Checklist

- [ ] Configure `DATABASE_URL` for PostgreSQL
- [ ] Set `AUTH_MODE=PROD` with JWT configuration
- [ ] Configure proper CORS origins in `api.py`
- [ ] Add rate limiting per user
- [ ] Set up monitoring and audit logs
- [ ] Configure HTTPS via reverse proxy
- [ ] Run `scripts/migrate_state_json_to_db.py` for existing sessions

---

## Coding Conventions

- Keep agent instructions concise but explicit about tool availability.
- Prefer updating `AgentConfig`/`CouncilRunner` flows over hardcoding in CLI.
- **Never commit** `.env` or API keys.
- Clean old logs before committing (`logs/` keeps only `.gitkeep`).
- Web API uses `async/await` throughout.
- Frontend uses polling (1.5-5s intervals), not WebSockets.
- All state mutations go through the database, not direct file writes.

---

## Known Limitations

1. **Trust-based auth in dev** – Production requires SSO integration
2. **Polling-based updates** – No WebSocket support (trade-off for simplicity)
3. **No progress percentage** – Status is qualitative (Queued/Running/Done)
4. **File size limits** – Large uploads may hit context limits (handled gracefully)
5. **No session sharing** – Each session has one owner

---

## File Structure

```
Agent_Council/
├── agentcouncil.py              # CLI entrypoint: start/stop/cli
├── run_api.py                   # Standalone backend startup
├── scripts/                     # Utility scripts
│   ├── verify_setup.py          # Installation verification
│   ├── verify_multi_user.py     # Multi-user isolation tests
│   └── migrate_state_json_to_db.py  # DB migration tool
│
├── tests/                       # Backend tests
│   ├── test_api_integration.py
│   └── test_services.py
│
├── STREAMING_TEST/              # Experimental streaming demo
│   ├── streaming_demo.py
│   └── README.md
│
├── sessions/                    # Session file storage (runtime)
├── logs/                        # CLI session logs (runtime)
└── agent_council.db             # SQLite database (dev, runtime)
```

---

## Dependencies

### Backend (requirements-web.txt)

```
openai-agents, openai, python-dotenv, rich, pypdf, python-docx
fastapi>=0.115.0, uvicorn[standard]>=0.31.1, python-multipart>=0.0.9
python-jose[cryptography]==3.3.0
pydantic>=2.12.3, pydantic-settings>=2.5.2
sqlalchemy>=2.0.0, alembic>=1.13.0, aiosqlite>=0.19.0, greenlet>=3.0.0
```

For PostgreSQL in production, add: `asyncpg`

### Frontend (web-ui/package.json)

```
react@19, react-dom@19, react-router-dom@7
axios, lucide-react, react-markdown
vite@7, tailwindcss@4, postcss, autoprefixer
```

---

*Last updated: December 12 2025*
