<!-- AI Generated Code by Deloitte + Cursor (BEGIN) -->
## Agent Council — Operations Runbook (v1)

This runbook describes how to run, troubleshoot, and operate the Agent Council application **in its current state** (local / single-instance).

### 1. Quick Start (Local Dev)
The application runs as a hybrid Python (FastAPI) + Node.js (React/Vite) stack.

#### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker (optional, for local PostgreSQL)
- OpenAI API Key

#### Start Everything
```bash
# Uses agentcouncil.py orchestrator
python agentcouncil.py start
```
This command:
1. Creates/activates `.venv`.
2. Installs Python & Node dependencies.
3. Starts a Postgres container (if Docker available; falls back to SQLite if not).
4. Launches Backend (port 8000) and Frontend (port 5173).

#### Stop Everything
```bash
python agentcouncil.py stop
```

### 2. Manual Startup (Component by Component)
If you need to debug specific components or run without the orchestrator:

#### Backend
```bash
# Terminal 1
source .venv/bin/activate
export OPENAI_API_KEY=sk-...
export AUTH_MODE=DEV
python run_api.py
```
- Listens on: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

#### Frontend
```bash
# Terminal 2
cd web-ui
npm run dev
```
- Listens on: `http://localhost:5173`
- Configured via `.env` (creates implicit `VITE_API_URL`)

### 3. Configuration (Environment Variables)
The app is configured via environment variables (or `.env` file).

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | (required) | API key for LLM calls |
| `DATABASE_URL` | `sqlite+aiosqlite:///./agent_council.db` | Connection string (use `postgresql+asyncpg://...` for prod) |
| `AUTH_MODE` | `DEV` | `DEV` (header spoofing) or `PROD` (JWT/Trusted Header) |
| `LOG_LEVEL` | `info` | Backend logging level |

### 4. Troubleshooting Common Issues

#### "Database is locked" (SQLite)
- **Symptom**: API errors 500/503 during heavy execution.
- **Cause**: SQLite concurrency limits.
- **Fix**: Switch to PostgreSQL (`DATABASE_URL`) or reduce parallel agents.

#### "Session not found" / 404
- **Cause**: You are likely hitting the API with a different user identity than the creator.
- **Fix**: Check `X-User-Id` header (in Dev) or your JWT/Auth header (in Prod).

#### "Execution hangs" (Infinite loading)
- **Cause**: Background task failed silently or worker process died.
- **Check**: Server stdout/stderr for tracebacks.
- **Recovery**: Restart backend; execution will not auto-resume (known limitation).

#### Files disappearing
- **Cause**: Running on ephemeral container without persistent volume.
- **Fix**: Mount `sessions/` directory or wait for S3 storage implementation (Sprint 3).

### 5. Deployment Notes (Pre-Handoff)
- **Single Instance Only**: The current architecture relies on local filesystem for uploads/logs and in-process memory for background tasks. **Do not scale horizontally** (run 1 replica).
- **Persistence**: Ensure `sessions/` and `agent_council.db` (if using SQLite) are on persistent storage.
- **Security**: Set `AUTH_MODE=PROD` and configure JWT validation.

### 6. Maintenance
- **Database Migrations**: Currently `Base.metadata.create_all` runs on startup. Alembic support is planned (Sprint 1).
- **Log Cleanup**: Manually delete old directories in `sessions/` to free space.
<!-- AI Generated Code by Deloitte + Cursor (END) -->

