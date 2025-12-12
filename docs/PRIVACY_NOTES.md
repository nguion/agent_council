<!-- AI Generated Code by Deloitte + Cursor (BEGIN) -->
## Agent Council — Privacy Notes (Logging, Retention, and Deletion)

This document provides specific privacy implementation details to support Compliance/Privacy reviews.

### 1. What is logged?
The system currently produces extensive execution logs to aid debugging and auditability of AI behavior.

#### LLM Call Logs (Markdown)
- **Location**: `sessions/{session_id}/logs/session_*.md` (local filesystem).
- **Content**:
  - Full **raw prompts** sent to the LLM (including injected context from uploaded files).
  - Full **raw responses** from the LLM.
  - Tool usage arguments (e.g., web search queries).
  - Cost and token usage metrics.
- **Privacy Impact**: These logs contain sensitive user data and extracted document text.
- **Mitigation Plan (Sprint 2)**:
  - Production default will be changed to **disable** raw prompt/response logging.
  - Logs will be moved to secure blob storage with lifecycle policies.

#### Application Logs (Stdout/Stderr)
- **Content**: API request paths, status codes, error traces.
- **Privacy Impact**: Generally low, but stack traces may reveal file paths.

### 2. Data Retention
There is currently **no automated expiration** or retention policy implementation.
- **Database**: Records persist until manually deleted.
- **Filesystem**: Uploads and logs persist until manually deleted or the instance is destroyed.

**Planned Work**:
- Configurable retention window (e.g., 30 days).
- Automated cleanup job (e.g., daily cron) to soft-delete or purge expired sessions.

### 3. Deletion capabilities
Users can delete sessions via the UI (or API `DELETE /api/sessions/{id}`).

#### Soft Delete (Default)
- **Action**: Sets `is_deleted=true` in the database.
- **Effect**: Session is hidden from lists and API access is blocked (404).
- **Data Persistence**: All data (DB rows + files) remains on disk.

#### Hard Delete (Manual / Admin)
- **Action**: `DELETE /api/sessions/{id}?hard=true`
- **Effect**:
  - Deletes the local filesystem directory `sessions/{id}/` (uploads + logs).
  - Updates DB state to `deleted=true` (but does **not** purge the DB row).
- **Gap**: This is not a "GDPR-style" full purge yet. The database row remains for audit metadata.

### 4. Third-party Sharing
- **OpenAI**: User data (prompts + uploaded text) is sent to OpenAI for processing. OpenAI's enterprise terms typically apply (zero retention for training), but this depends on the specific API agreement.
- **Web Search Providers**: If enabled, search queries are sent to external search engines (e.g., DuckDuckGo, Google, Bing via agents SDK).

### 5. Recommendations for Privacy Review
- **Disable Web Search** globally if third-party query leakage is unacceptable.
- **Disable Raw Logging** in production to minimize sensitive data footprint.
- **Implement Automated Purge** to meet retention obligations.
<!-- AI Generated Code by Deloitte + Cursor (END) -->

