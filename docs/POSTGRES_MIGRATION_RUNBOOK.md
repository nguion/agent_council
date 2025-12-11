# PostgreSQL JSONB Migration Runbook

## Overview
- Move session state from file/SQLite to PostgreSQL JSONB (`session_state` table).
- Keep uploads/logs on filesystem; metadata stays in `sessions` (status/current_step/cost/user_id).
- State reads/writes are gated by `DATABASE_URL`: Postgres → DB state; SQLite → file fallback.
- Progress updates are batched per-session (~350ms) to avoid thundering writes.

## Prerequisites
- PostgreSQL reachable; create DB `agent_council` (or equivalent).
- Set `DATABASE_URL=postgresql+asyncpg://user:pass@host:port/agent_council`.
- Optional tuning via env:
  - `DB_POOL_SIZE` (default 10)
  - `DB_MAX_OVERFLOW` (default 20)
- Backup current `sessions/` directory (state.json files) and database.

## Schema
- New table `session_state` (session_id PK, state JSONB, updated_at).
- GIN index on `session_state.state` (best-effort at startup).
- Existing `sessions` table unchanged (still holds metadata and legacy `state` column for compatibility).

## Migration Steps
1) **Staging first**
   - Export `DATABASE_URL` to Postgres.
   - Start backend once (creates tables/index).
   - Run migration script:
     ```bash
     DATABASE_URL=postgresql+asyncpg://... \
     python scripts/migrate_state_json_to_db.py
     ```
   - Validate: run full flow (build/execute/review/summarize), ensure /status polling works.

2) **Production cutover**
   - Backup `sessions/` and DB snapshots.
   - Export `DATABASE_URL` to Postgres.
   - Run migration script (idempotent; can rerun safely).
   - Start backend; verify health `/api/health`.
   - Run smoke: create session, build, execute, review, synthesize.
   - Keep files as temporary fallback/read-only until confidence window passes.

## Validation Checklist
- API health: `curl /api/health`.
- Status/summary: `curl /api/sessions/{id}/status` and `/summary` return live data.
- Execution progress updates smoothly; no hangs.
- DB checks:
  - `SELECT count(*) FROM session_state;`
  - Optional: `SELECT * FROM session_state LIMIT 1;`
  - Confirm `sessions.status/current_step` advance during flows.

## Monitoring
- DB metrics: connection count, lock waits, slow queries.
- App logs: look for `Warning: batched update failed` or migration errors.
- Endpoint error rates: /status, /summary, /execute, /peer_review.

## Rollback
- Unset `DATABASE_URL` (fall back to SQLite+files) and restart backend.
- Preserve `sessions/` directory; DB state remains available for re-cutover.
- If migration partially applied, rerun script after addressing issues.

## Notes
- Batching: progress writes coalesced per session (~350ms) to reduce write pressure.
- Reads: always prefer DB when `DATABASE_URL` is set; file used only as legacy fallback.
- Keep uploads/logs on filesystem; only state moves to Postgres.
