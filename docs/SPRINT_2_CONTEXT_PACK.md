# Sprint 2 Context Pack — Handoff Readiness

**Date**: 2025-12-12  
**Branch**: `handoff-ready`  
**Status**: Sprint 1 Complete ✅ | Ready for Sprint 2

---

## 🎯 Quick Start for Next Agent

### Current State
- **Sprint 1**: ✅ **COMPLETE** — All PRs (PR-1 through PR-6) done and tested
- **Sprint 2**: Ready to begin — Admin telemetry + audit logs + quotas/rate limits
- **Branch**: `handoff-ready` (all work committed and pushed)
- **Test Status**: 40 tests passing (up from 15)

### What You Need to Know
1. **Always work on `handoff-ready` branch** (not `main`)
2. **Update `docs/HANDOFF_READINESS_PLAN.md`** as you work (it's the single source of truth)
3. **Follow the PR sequence** in the plan (PR-7, PR-8, PR-9, PR-10, PR-11)
4. **Write tests** for all new functionality
5. **Keep commits atomic** and reference PR numbers

---

## ✅ Sprint 1 Completion Summary

### What Was Built

#### PR-1: Documentation Alignment
- Rewrote `docs/ARCHITECTURE.md` to match actual codebase (DB-first architecture)
- Created `docs/DATA_HANDLING.md`, `docs/SECURITY_MODEL.md`, `docs/PRIVACY_NOTES.md`, `docs/RUNBOOK.md`
- **Files**: `docs/*.md`

#### PR-2: Developer Experience Fixes
- Fixed `scripts/verify_setup.py` (removed references to deleted files)
- Added `.env.example` and `web-ui/.env.example`
- **Files**: `scripts/verify_setup.py`, `.env.example`, `web-ui/.env.example`

#### PR-3: Containerization
- Added `Dockerfile` (backend) and `web-ui/Dockerfile` (frontend)
- Added `docker-compose.yml` for local dev (Postgres + backend + frontend)
- Added `.dockerignore`
- **Files**: `Dockerfile`, `web-ui/Dockerfile`, `docker-compose.yml`, `.dockerignore`

#### PR-4: CI Baseline
- Added `.github/workflows/ci.yml` (runs on push/PR to `main` and `handoff-ready`)
- Backend: Python lint (ruff) + tests (pytest)
- Frontend: npm ci + build
- **Files**: `.github/workflows/ci.yml`

#### PR-4.1: Enhanced Test Coverage
- Created `tests/test_auth.py` (9 tests)
- Created `tests/test_file_uploads.py` (7 tests, 3 skipped for PR-7)
- Created `tests/conftest.py` (shared fixtures)
- Enhanced `tests/test_api_integration.py` (+7 edge case tests)
- **Result**: 34 tests (up from 15)
- **Files**: `tests/test_auth.py`, `tests/test_file_uploads.py`, `tests/conftest.py`

#### PR-5: Alembic Migrations Baseline
- Initialized Alembic (`alembic/` directory, `alembic.ini`, `alembic/env.py`)
- Created initial migration (`950bd54c7a60`) for `users`, `sessions`, `session_state` tables
- Updated `src/web/database.py` `init_db()` to use migrations (with fallback for legacy DBs)
- Created comprehensive test suite (`scripts/test_alembic_migrations.py`)
- **Result**: Production-ready migrations, backward compatible
- **Files**: `alembic/`, `alembic.ini`, `src/web/database.py`, `scripts/test_alembic_migrations.py`

#### PR-6: RBAC Skeleton
- Created migration (`8b746e4b0150`) to add `role` column to `users` table
- Updated `User` model with `role` field (default='user', indexed)
- Created `require_role()` FastAPI dependency factory
- Created `/api/admin/metrics/summary` admin-only endpoint (placeholder)
- Created `tests/test_rbac.py` (6 tests)
- **Enhancements** (follow-up):
  - Added role validation (CheckConstraint for PostgreSQL, app-level for SQLite)
  - Added `UserService.update_role()` method
  - Created `scripts/promote_user_to_admin.py` utility
  - Updated `docs/SECURITY_MODEL.md` and `docs/ARCHITECTURE.md`
- **Result**: RBAC foundation complete, production-ready
- **Files**: 
  - `alembic/versions/8b746e4b0150_*.py`
  - `src/web/database.py`, `src/web/db_service.py`, `src/web/api.py`
  - `tests/test_rbac.py`
  - `scripts/promote_user_to_admin.py`
  - `docs/SECURITY_MODEL.md`, `docs/ARCHITECTURE.md`

### Test Coverage
- **Total**: 40 tests passing
  - 18 API integration tests
  - 9 authentication tests
  - 6 RBAC tests
  - 4 file upload tests (3 skipped for PR-7)
  - 3 service tests
- **Run tests**: `python3 -m pytest tests/ -v`

---

## 🚀 Sprint 2 Roadmap

### Objective
Make security and operational controls real, not aspirational; provide admin visibility.

### PR Sequence (Suggested)

#### PR-7: Security Guardrails
**Status**: Not started  
**What**:
- Upload allow-list + max size enforcement
- Environment kill-switches: `DISABLE_UPLOADS=true`, `DISABLE_WEB_SEARCH=true`
- Enforce server-side (UI toggle cannot override)

**Files to touch**:
- `src/web/api.py` (upload validation)
- `src/agent_council/core/council_runner.py` (web search kill-switch)
- `tests/test_file_uploads.py` (enable skipped tests)
- `.env.example` (document new env vars)

**Acceptance criteria**:
- File type allow-list enforced at API boundary
- Max file size enforced (configurable)
- `DISABLE_UPLOADS=true` blocks all uploads
- `DISABLE_WEB_SEARCH=true` blocks web search even if enabled in council config
- Tests cover all scenarios

---

#### PR-8: Audit Logging + Event Model
**Status**: Not started  
**What**:
- Create `audit_events` table (Alembic migration)
- Emit events for:
  - Session created
  - Session accessed (`/summary`, `/results`)
  - File uploaded (metadata only)
  - Execute/review/synthesize requested
  - Delete requested
  - Admin dashboard viewed
- Fields: `actor`, `action`, `session_id`, `timestamp`, `metadata` (redacted), `request_id`

**Files to touch**:
- `alembic/versions/` (new migration)
- `src/web/database.py` (AuditEvent model)
- `src/web/api.py` (emit events in endpoints)
- `src/web/audit_service.py` (new service)
- `tests/test_audit.py` (new)

**Acceptance criteria**:
- `audit_events` table created via migration
- Events emitted for all key actions
- Metadata redacted appropriately (no sensitive data)
- Tests verify event emission

---

#### PR-9: Quotas/Rate Limiting
**Status**: Not started  
**What**:
- Per-user throttles for expensive operations (execute/review/synthesize)
- Per-user budget controls (token/cost caps)
- Use existing `last_cost_usd`/token totals from `sessions` table
- Return clear error messages (don't fail silently)

**Files to touch**:
- `src/web/quota_service.py` (new)
- `src/web/api.py` (check quotas before expensive operations)
- `src/web/database.py` (maybe add `user_quotas` table or use existing fields)
- `tests/test_quotas.py` (new)

**Acceptance criteria**:
- Rate limits enforced on expensive operations
- Budget caps enforced per user
- Clear error messages returned
- Tests cover quota enforcement

---

#### PR-10: Admin Metrics Endpoints (Real Implementation)
**Status**: Not started  
**What**:
- Replace placeholder `/api/admin/metrics/summary` with real aggregation
- Add additional admin endpoints:
  - `/api/admin/metrics/usage` (time-series data)
  - `/api/admin/metrics/errors` (top errors)
  - `/api/admin/metrics/performance` (p50/p95 latencies)
- Aggregate from `sessions`, `audit_events`, and state data

**Files to touch**:
- `src/web/api.py` (implement real metrics endpoints)
- `src/web/admin_service.py` (new, aggregation logic)
- `tests/test_admin_metrics.py` (new)

**Acceptance criteria**:
- Real metrics aggregated from database
- Endpoints return accurate data
- Protected by `require_role("admin")`
- Tests verify aggregation logic

---

#### PR-11: Admin Dashboard UI Route `/admin`
**Status**: Not started  
**What**:
- Create React route `/admin` in `web-ui`
- Display aggregated usage (tokens/cost) over time
- Show top errors
- Show slowest steps
- Show active background tasks (even if still in-process)
- Protected by RBAC (check user role client-side, but backend enforces)

**Files to touch**:
- `web-ui/src/pages/AdminDashboard.jsx` (new)
- `web-ui/src/App.jsx` (add route)
- `web-ui/src/api.js` (add admin API calls)
- Update `web-ui/src/layouts/SessionLayout.jsx` if needed

**Acceptance criteria**:
- Admin dashboard accessible at `/admin`
- Displays real metrics from backend
- Non-admin users see 403 or redirect
- UI is responsive and clear

---

## 📁 Key Files & Patterns

### Database & Migrations
- **Models**: `src/web/database.py`
  - `User` (has `role` field)
  - `Session` (metadata)
  - `SessionState` (JSON/JSONB state)
- **Migrations**: `alembic/versions/`
  - Latest: `8b746e4b0150` (role column)
  - Pattern: Always create migrations, never use `create_all()` in production
- **Service**: `src/web/db_service.py`
  - `UserService.get_or_create_user()`, `UserService.update_role()`
  - `SessionService.*`

### Authentication & Authorization
- **Auth**: `src/web/api.py`
  - `get_current_user()` — gets/creates user from headers
  - `require_role(role)` — FastAPI dependency factory for RBAC
- **Modes**: `AUTH_MODE=DEV` (default) or `AUTH_MODE=PROD`
- **Roles**: `'user'` (default), `'admin'`, `'auditor'`

### API Endpoints
- **Main API**: `src/web/api.py`
- **Admin endpoint**: `/api/admin/metrics/summary` (placeholder, needs PR-10)
- **Session endpoints**: `/api/sessions/*` (all enforce ownership)

### Testing
- **Test fixtures**: `tests/conftest.py`
- **Test files**:
  - `tests/test_api_integration.py` (18 tests)
  - `tests/test_auth.py` (9 tests)
  - `tests/test_rbac.py` (6 tests)
  - `tests/test_file_uploads.py` (4 passing, 3 skipped for PR-7)
  - `tests/test_services.py` (3 tests)
- **Run**: `python3 -m pytest tests/ -v`

### Documentation
- **Plan**: `docs/HANDOFF_READINESS_PLAN.md` (single source of truth)
- **Architecture**: `docs/ARCHITECTURE.md` (current state)
- **Security**: `docs/SECURITY_MODEL.md` (threat model)
- **Data**: `docs/DATA_HANDLING.md` (what data goes where)

---

## 🔧 Development Workflow

### Setup
```bash
# Clone and checkout branch
git checkout handoff-ready

# Setup environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-web.txt
pip install -r requirements-dev.txt

# Copy env files
cp .env.example .env
# Edit .env and add OPENAI_API_KEY

# Initialize database (runs migrations)
python3 -c "import asyncio; from src.web.database import init_db; asyncio.run(init_db())"
```

### Running Tests
```bash
# All tests
python3 -m pytest tests/ -v

# Specific test file
python3 -m pytest tests/test_rbac.py -v

# With coverage
python3 -m pytest tests/ --cov=src --cov-report=html
```

### Running Locally
```bash
# Backend (Terminal 1)
python3 run_api.py

# Frontend (Terminal 2)
cd web-ui && npm run dev

# Or use docker-compose
docker-compose up
```

### Creating Migrations
```bash
# Create new migration
python3 -m alembic revision --autogenerate -m "Description"

# Apply migrations
python3 -m alembic upgrade head

# Check current revision
python3 -m alembic current
```

### Promoting Users to Admin (Dev/Testing)
```bash
# First, user must exist (created on first API access)
# Then promote:
python3 scripts/promote_user_to_admin.py user@example.com
```

---

## 🎯 Key Patterns to Follow

### 1. Always Update the Plan
When you start a PR:
- Mark it "in progress" in `docs/HANDOFF_READINESS_PLAN.md`
- Add execution plan under the PR section
- Update status block at top

When you finish:
- Mark PR "Done"
- Add progress notes (what changed, why)
- Add traceability (commit hash, files changed)
- Update status block

### 2. Write Tests First (TDD)
- Write tests before implementation
- Aim for >80% coverage on new code
- Use existing test patterns (`tests/conftest.py` fixtures)

### 3. Database Changes = Migration
- Never modify models without a migration
- Test migrations on fresh DB and existing DB
- Use Alembic, not `create_all()`

### 4. RBAC Enforcement
- Use `require_role("admin")` for admin endpoints
- Check ownership for session endpoints
- Return 403 for unauthorized, 404 for not found (prevents enumeration)

### 5. Environment Variables
- Document in `.env.example`
- Use `os.getenv()` with sensible defaults
- Document in `docs/RUNBOOK.md` if needed

---

## 🚨 Important Notes

### Branch Strategy
- **All work on `handoff-ready` branch** (not `main`)
- This is documented in the plan and enforced

### Database State
- Current DB: `agent_council.db` (SQLite, dev)
- Migrations applied: `950bd54c7a60` (initial), `8b746e4b0150` (role column)
- Production will use PostgreSQL (migrations handle both)

### Background Tasks
- Currently: FastAPI `BackgroundTasks` (in-process, not durable)
- **Sprint 3** will introduce JobRunner abstraction
- For now, document limitations

### Filesystem Artifacts
- Currently: `sessions/{id}/` for uploads and logs
- **Sprint 3** will introduce StorageProvider abstraction
- For now, works for single-instance dev

### Test Coverage
- 40 tests passing
- 3 tests skipped (waiting for PR-7 file upload guardrails)
- Aim to keep >80% coverage

---

## 📊 Sprint 1 Metrics

- **PRs Completed**: 6 (PR-1 through PR-6)
- **Tests Added**: +25 (15 → 40)
- **Migrations Created**: 2 (initial + role column)
- **Documentation Files**: 5 (ARCHITECTURE, DATA_HANDLING, SECURITY_MODEL, PRIVACY_NOTES, RUNBOOK)
- **Scripts Added**: 3 (verify_setup, test_alembic_migrations, promote_user_to_admin)
- **CI/CD**: ✅ GitHub Actions workflow active

---

## 🔗 Useful Links

- **Plan**: `docs/HANDOFF_READINESS_PLAN.md`
- **Architecture**: `docs/ARCHITECTURE.md`
- **Security Model**: `docs/SECURITY_MODEL.md`
- **API Docs**: http://localhost:8000/docs (when backend running)
- **Frontend**: http://localhost:5173 (when frontend running)

---

## ❓ Questions?

1. **Where do I start?** → Begin with PR-7 (Security Guardrails)
2. **How do I test?** → Use `pytest` with fixtures from `tests/conftest.py`
3. **How do I create a migration?** → `alembic revision --autogenerate -m "Description"`
4. **How do I promote a user?** → `python3 scripts/promote_user_to_admin.py <email>`
5. **Where's the plan?** → `docs/HANDOFF_READINESS_PLAN.md` (always keep it updated!)

---

**Good luck with Sprint 2! 🚀**

