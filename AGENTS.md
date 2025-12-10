## Agent Council – Maintainer Notes (AGENTS.md)

This file is for people (or AI agents) working on the codebase. It summarizes how to set up, run, and extend the project without digging through multiple files.

### What this project does
- Orchestrates a council of GPT-5.1 agents with optional web search, file ingestion, and peer review.
- Builds personas, executes them in parallel, then performs peer review and chairman synthesis.
- Tracks token usage and cost.
- Provides both CLI and web interface.

### Quick setup
- **Windows (PowerShell):**
  - `powershell -ExecutionPolicy Bypass -File setup.ps1`
  - Creates `.venv`, installs deps, prompts for `OPENAI_API_KEY`, optionally runs `agentcouncil.py`.
- **macOS / Linux:**
  - `bash setup.sh`
  - Creates `.venv`, installs deps, prompts for `OPENAI_API_KEY`, optionally runs `agentcouncil.py`.

### Manual setup (any OS)
```bash
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-web.txt  # For web interface
pip install -e .
echo "OPENAI_API_KEY=sk-..." > .env
```

### How to run

**CLI:**
```bash
python agentcouncil.py
```
Flow: prompt for question → optional context ingestion → council build → edit → parallel execution → peer review → chairman synthesis → results written to `council_session_complete.json` and `logs/`.

**Web Interface:**
```bash
# Terminal 1
./start_backend.sh
# or: python run_api.py

# Terminal 2
./start_frontend.sh
# or: cd web-ui && npm run dev
```
Then open: http://localhost:5173

### Key files

**CLI:**
- `agentcouncil.py`: CLI entrypoint for the 5-step flow.
- `src/agent_council/core/council_runner.py`: Builds per-agent instructions (name, persona, tool awareness) and executes them in parallel.
- `src/agent_council/core/agent_runner.py`: Runs an agent and captures tool usage (`web_search_call`, etc.) plus token usage.
- `src/agent_council/core/council_builder.py`: Uses GPT-5.1 to design the council personas (JSON output).
- `src/agent_council/core/council_reviewer.py` / `council_chairman.py`: Peer review and final synthesis.

**Web Interface:**
- `src/web/api.py`: FastAPI application with all endpoints
- `src/web/services.py`: Service layer wrapping core Agent Council functions
- `src/web/session_manager.py`: File-based session persistence
- `run_api.py`: Server startup script
- `web-ui/src/App.jsx`: Main React app with step orchestration
- `web-ui/src/api.js`: Axios-based API client

**Setup:**
- `setup.ps1`, `setup.sh`: One-command environment setup.
- `requirements.txt`, `requirements-web.txt`, `setup.py`: Dependencies and packaging metadata.

### Tools and environment
- **Env:** `OPENAI_API_KEY` required. Stored in `.env` (created by setup scripts).
- **Models:** Defaults to `gpt-5.1`.
- **Tools per agent:** Web search (enabled per persona), optional file ingestion; tool usage is captured in results.
- **Context handling:** No hard truncation; if context is too large the runner will attempt summarization via `context_condense`.

### Outputs and logs
- `logs/*.md`: Session transcripts with prompts, responses, token usage, and cost.
- `council_session_complete.json`: Execution results, peer reviews, chairman verdict, and cost summary.
- `sessions/{session_id}/`: Web interface session data (state.json, uploaded_files/, logs/)

### Coding conventions / notes
- Keep agent instructions concise but explicit about tool availability.
- Prefer updating `AgentConfig`/`CouncilRunner` flows rather than hardcoding behavior in the CLI.
- Avoid committing `.env` or any API keys. `logs/` keeps only `.gitkeep`—clean old logs before committing.
- Web API uses async/await throughout for LLM operations.
- Frontend uses polling (1.5-5s intervals) for progress updates, not WebSockets.

### Common tasks

**Add a new persona field or tool flag:**
- Update `AgentConfig` in `src/agent_council/core/agent_config.py`
- Update `CouncilBuilder` JSON schema expectations in `council_builder.py`
- Update `CouncilRunner` instruction builder in `council_runner.py`
- Update web UI components if needed (Step2Build, Step3Edit)

**Inspect whether web search was used:**
- Check `tools_used` in `execution_results` (expect `web_search_call` when enabled)
- Web UI displays this in Step 4 execution results

**Adjust context handling:**
- `context_condense.py` controls summarization fallback
- Web API uses same logic via `services.py`

**Modify web API endpoints:**
- Edit `src/web/api.py` for endpoint changes
- Update `src/web/services.py` for business logic
- Update `web-ui/src/api.js` for frontend API client
- API docs auto-generate at `/docs`

**Modify frontend components:**
- Shared components in `web-ui/src/components/`
- Step views in `web-ui/src/steps/`
- Main app logic in `web-ui/src/App.jsx`
- Uses Tailwind CSS for styling

### Architecture decisions

**Backend (Web API):**
- FastAPI chosen for native async support and automatic docs
- File-based sessions for simplicity (no database needed)
- Background tasks for long-running operations (execution, review)
- Polling pattern for progress updates (simple, works everywhere)
- CORS enabled for local development (configure for production)

**Frontend:**
- React for component-based architecture
- Vite for fast development and builds
- Tailwind CSS for rapid, consistent styling
- Axios for API calls
- React Markdown for formatting Chairman's verdict

**State Management:**
- Session state stored in `sessions/{session_id}/state.json`
- Frontend polls backend every 1.5-5 seconds for updates
- Cost/token data updated in real-time via polling

### Web API endpoints

- `POST /api/sessions` - Create session with file uploads
- `POST /api/sessions/{id}/build_council` - Generate council
- `PUT /api/sessions/{id}/council` - Update council configuration
- `POST /api/sessions/{id}/execute` - Execute council (background)
- `GET /api/sessions/{id}/status` - Poll execution/review progress
- `GET /api/sessions/{id}/results` - Get execution results
- `POST /api/sessions/{id}/peer_review` - Start peer review (background)
- `GET /api/sessions/{id}/reviews` - Get peer review results
- `POST /api/sessions/{id}/synthesize` - Generate Chairman's verdict
- `GET /api/sessions/{id}/summary` - Get complete session data

See interactive docs at http://localhost:8000/docs

### Testing

**Backend:**
- Start API: `python run_api.py`
- Visit http://localhost:8000/docs for interactive testing
- Check `sessions/` directory for session persistence

**Frontend:**
- Start both backend and frontend
- Test full 5-step workflow
- Check browser console for errors
- Verify cost tracking in sidebar

**Verification:**
- Run `python3 test_setup.py` to check installation

### Known limitations

1. **No user authentication** - Single-user mode only
2. **No session history UI** - Sessions stored but not browsable in UI
3. **Polling-based updates** - Not WebSocket (trade-off for simplicity)
4. **No progress percentage** - Status is qualitative (Queued/Running/Done)
5. **File size limits** - Large files may hit context limits (handled gracefully)

### Future enhancements (not implemented)

Considered but not in MVP:
- User authentication / SSO
- Session history browser
- WebSocket for real-time updates
- Progress bars with percentages
- Multi-user support
- Database persistence
- Advanced filtering/search
- Mobile-optimized UI
- Export to PDF/Word

### Dependencies

**Backend (requirements-web.txt):**
- `fastapi==0.104.1`
- `uvicorn[standard]==0.24.0`
- `python-multipart==0.0.6`
- `python-jose[cryptography]==3.3.0`
- `pydantic==2.5.0`
- `pydantic-settings==2.1.0`

**Frontend (web-ui/package.json):**
- `react` + `react-dom`
- `vite` + `@vitejs/plugin-react`
- `tailwindcss` + `postcss` + `autoprefixer`
- `axios`
- `lucide-react`
- `react-markdown`

### Production deployment notes

**Backend:**
- Use gunicorn with uvicorn workers: `gunicorn src.web.api:app -w 4 -k uvicorn.workers.UvicornWorker`
- Configure proper CORS origins
- Add rate limiting
- Set up monitoring/logging
- Configure HTTPS

**Frontend:**
- Build: `cd web-ui && npm run build`
- Serve `web-ui/dist/` with nginx/Apache
- Set `VITE_API_URL` to production API URL

**Before production:**
- Add authentication
- Configure proper CORS
- Add rate limiting
- Set up monitoring
- Configure HTTPS
- Consider database for sessions (optional)

### Integration with CLI

The web app **coexists** with the CLI:
- Original `agentcouncil.py` still works exactly as before
- Web API wraps the same core functions via `services.py`
- Both use the same `SessionLogger` for cost tracking
- No changes to core `agent_council` package

### File structure

```
Agent_Council/
├── src/
│   ├── agent_council/          # Core logic
│   │   ├── core/
│   │   └── utils/
│   └── web/                    # Web API
│       ├── api.py
│       ├── services.py
│       └── session_manager.py
├── web-ui/                     # Frontend
│   └── src/
│       ├── components/
│       ├── steps/
│       └── App.jsx
├── agentcouncil.py             # CLI entrypoint
├── run_api.py                  # Web API server
└── sessions/                   # Session storage
```
