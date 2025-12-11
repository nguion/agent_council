# Agent Council

A modular, agentic framework for creating, customizing, and executing councils of specialized AI agents (powered by GPT-5.1) to solve complex problems in parallel.

## Features

*   **Multi-Step Workflow**:
    1.  **Ingest**: Accepts questions and context files (PDF, DOCX, TXT, MD, JSON, PY, CSV).
    2.  **Build**: Uses an Architect Agent to propose a diverse council of experts.
    3.  **Edit**: Interactively refine the council (add/remove/edit agents).
    4.  **Execute**: Runs all agents in parallel, aggregating their unique perspectives.
    5.  **Review**: Peer review and Chairman synthesis.
*   **High Modularity**: Agents, tools, and runners are decoupled and easy to extend.
*   **GPT-5.1 Integration**: Native support for reasoning effort configuration (`none`, `low`, `medium`, `high`).
*   **Cost & Token Tracking**: Real-time token usage monitoring and automatic cost calculation.
*   **CLI Interface**: Rich terminal UI for easy interaction.
*   **Web Interface**: Modern React-based web app with:
    - **Production-grade state management** with URL-based routing
    - **Multi-user support** - per-user session isolation with database-backed storage
    - **Session sidebar** - left panel shows all your sessions for quick navigation
    - **Session persistence** - resume sessions across browser restarts
    - **Shareable URLs** - send session links to colleagues (they must be the owner)
    - **Intelligent caching** - prevents accidental reruns of expensive operations
    - **Real-time progress tracking** during execution and review
    - **Session history** - browse, resume, and delete your past councils

---

## Quick Start

### Option 1: Web Interface (Recommended)

```bash
# Terminal 1 - Start Backend
./start_backend.sh

# Terminal 2 - Start Frontend
./start_frontend.sh
```

Open browser: **http://localhost:5173**

### Option 2: CLI Interface

```bash
python3 agentcouncil.py
```

---

## Installation & Setup

### Prerequisites

- Python 3.9+
- Node.js 16+ and npm (for web interface)
- OpenAI API key

### Quick Setup (CLI Only)

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy Bypass -File setup.ps1
```

**macOS / Linux:**
```bash
bash setup.sh
```

### Manual Setup

```bash
# 1. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. Install Python dependencies
pip install -r requirements.txt
pip install -e .

# 3. Set OpenAI API key
echo "OPENAI_API_KEY=sk-..." > .env
```

### Web Interface Setup

```bash
# 4. Install web dependencies
pip install -r requirements-web.txt

# 5. Install frontend dependencies
cd web-ui
npm install
cd ..

# 6. Verify setup
python3 test_setup.py
```

---

## Usage

### Web Interface

The web interface provides a guided 5-step workflow with session persistence and URL-based navigation.

#### Quick Workflow

1. **Start both servers** (see Quick Start above)
2. **Open** http://localhost:5173
3. **Enter your question** (example pre-filled)
4. **Upload files** (optional) via drag-and-drop
5. **Build Council** - AI designs specialized agents
6. **Edit agents** (optional) - refine, add, remove
7. **Execute** - Watch agents work in parallel
8. **Peer Review** - Agents critique each other
9. **Final Verdict** - Chairman synthesizes answer
10. **Download** - Get complete session as JSON

**Expected time:** 3-5 minutes | **Cost:** $0.05-$0.15

#### Session Management

The application features a **three-panel layout** for efficient session management:

```
┌─────────────────┬──────────────────────────┬─────────────────┐
│ Your Sessions   │   Main Workflow          │ Session Details │
│ (Left Panel)    │   (Steps 1-5)            │ (Right Panel)   │
├─────────────────┼──────────────────────────┼─────────────────┤
│ My Sessions [+] │                          │ Question: ...   │
│ 3 sessions      │  [Current step view]     │ Council: ...    │
│                 │                          │ Cost: $0.234    │
│ ✓ Complete 2h   │                          │ Tokens: 20.8K   │
│ Strategy for... │                          │                 │
│ [trash]         │                          │                 │
└─────────────────┴──────────────────────────┴─────────────────┘
```

**Left Sidebar (Your Sessions):**
- All your sessions in one place
- Quick navigation - click any session to resume
- Delete sessions - hover and click trash icon
- See status at a glance (color-coded badges)
- Track costs per session
- Auto-refreshes every 10 seconds

**Features:**
- **View all sessions**: Check the left sidebar or navigate to /sessions
- **Resume sessions**: Click any session in the sidebar to continue where you left off
- **Delete sessions**: Hover over a session and click the trash icon (soft delete - files preserved)
- **Create sessions**: Click the [+] button in sidebar header
- **Navigate safely**: Use browser back/forward buttons - sessions auto-save
- **Refresh anytime**: All progress is persisted on the backend
- **Privacy**: You see only your own sessions - cannot access others' data

#### Example Questions

✅ **Good**: "What are 5 data-driven strategies to reduce customer churn for B2B SaaS companies with 50-200 employees?"

❌ **Too vague**: "How to get more customers?"

#### Best Practices

**Council Size:**
- **Small (2-3 agents)**: Quick, focused problems
- **Medium (4-6 agents)**: Complex problems, multiple perspectives  
- **Large (7+ agents)**: Very complex, strategic decisions

**Reasoning Effort:**
- **Low**: Simple analysis (~10s per agent)
- **Medium**: Balanced analysis (~30s per agent)
- **High**: Deep strategic thinking (~60s+ per agent)

**Web Search:**
- Enable for: current events, statistics, research
- Disable for: internal company data, hypothetical scenarios

**File Uploads:**
- Use PDFs for reports, whitepapers
- Use CSVs for data, tables
- Use TXT/MD for notes, documentation
- Keep files under 10MB each

### CLI Interface

```bash
python3 agentcouncil.py
```

**5-Step Flow:**
1. Input question + optional context files
2. Build council personas (automatic)
3. Edit council (add/remove/edit personas)
4. Execute agents in parallel (live table)
5. Peer review + chairman synthesis (scores + final answer)

---

## Project Structure

```
Agent_Council/
├── src/
│   ├── agent_council/          # Core logic
│   │   ├── core/
│   │   │   ├── agent_builder.py
│   │   │   ├── agent_config.py
│   │   │   ├── agent_runner.py
│   │   │   ├── council_builder.py
│   │   │   ├── council_editor.py
│   │   │   ├── council_runner.py
│   │   │   ├── council_reviewer.py
│   │   │   └── council_chairman.py
│   │   └── utils/
│   │       ├── file_ingestion.py
│   │       ├── session_logger.py
│   │       └── context_condense.py
│   └── web/                    # Web API (FastAPI)
│       ├── api.py
│       ├── services.py
│       └── session_manager.py
├── web-ui/                     # Frontend (React + Vite)
│   └── src/
│       ├── components/
│       ├── steps/
│       ├── api.js
│       └── App.jsx
├── agentcouncil.py             # CLI entrypoint
├── run_api.py                  # Web API server
├── start_backend.sh            # Backend startup script
├── start_frontend.sh           # Frontend startup script
└── test_setup.py               # Setup verification
```

---

## Configuration

### Manual Agent Creation

```python
from agent_council.core.agent_builder import AgentBuilder
from agent_council.core.agent_config import AgentConfig

config = AgentConfig(
    name="Analyst",
    enable_web_search=True,
    reasoning_effort="medium"
)
agent = AgentBuilder.create(config)
```

---

## Outputs & Logging

### CLI Outputs
- `logs/*.md`: Full transcripts with token usage and cost per call
- `council_session_complete.json`: Complete results, peer reviews, verdict, and cost breakdown

### Web Interface Outputs
- `sessions/{session_id}/`: Session data directory
  - `state.json`: Session state
  - `uploaded_files/`: Your uploaded files
  - `logs/`: LLM call logs
- Download session JSON from the web interface

### Cost Tracking
- Real-time token usage (input/output)
- Automatic cost calculation (GPT-5.1, GPT-4o, etc.)
- Detailed breakdown per agent and total session cost
- Displayed in CLI tables and web sidebar

---

## Performance & Costs

### Timing
- Council Building: 10-30 seconds
- Execution (4 agents): 30-60 seconds
- Peer Review: 30-60 seconds
- Chairman Verdict: 15-30 seconds
- **Total:** 2-4 minutes end-to-end

### Costs (GPT-5.1)
- Simple question: $0.05 - $0.15
- With context files: $0.15 - $0.50
- Complex scenario: $0.50 - $1.00

---

## Troubleshooting

### Backend Won't Start

**Missing dependencies:**
```bash
pip install -r requirements-web.txt
```

**Missing API key:**
```bash
echo "OPENAI_API_KEY=sk-..." > .env
```

**Missing greenlet (database dependency):**
```bash
pip install greenlet
```

**Port 8000 in use:**
```bash
lsof -ti:8000 | xargs kill -9
```

**Database initialization:**
- SQLite database (`agent_council.db`) auto-creates on first startup
- If issues, delete `agent_council.db` and restart backend

### Frontend Won't Start

**Missing dependencies:**
```bash
cd web-ui
rm -rf node_modules package-lock.json
npm install
```

**Missing .env:**
```bash
cd web-ui
echo "VITE_API_URL=http://localhost:8000" > .env
```

**Port 5173 in use:**
```bash
lsof -ti:5173 | xargs kill -9
```

### General Issues

**Verify setup:**
```bash
python3 test_setup.py
```

**Check API connection:**
```bash
curl http://localhost:8000/api/health
```

**View API docs:**
http://localhost:8000/docs

---

## Production Deployment

### Backend

```bash
# Using gunicorn (recommended)
pip install gunicorn
gunicorn src.web.api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Or using uvicorn directly
uvicorn src.web.api:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend

```bash
cd web-ui
npm run build
# Serve web-ui/dist/ with nginx/Apache or:
npm install -g serve
serve -s dist -p 3000
```

### Environment Variables

- **Backend:** `OPENAI_API_KEY` in `.env`
- **Frontend:** `VITE_API_URL` in `web-ui/.env`

---

## API Reference (Web Interface)

See interactive docs: http://localhost:8000/docs

**Key Endpoints:**
- `POST /api/sessions` - Create session
- `POST /api/sessions/{id}/build_council` - Build council
- `PUT /api/sessions/{id}/council` - Update council
- `POST /api/sessions/{id}/execute` - Execute council
- `GET /api/sessions/{id}/status` - Get progress
- `POST /api/sessions/{id}/peer_review` - Run peer review
- `POST /api/sessions/{id}/synthesize` - Generate verdict
- `GET /api/sessions/{id}/summary` - Get complete session

---

## File Support

- PDF documents (.pdf)
- Word documents (.docx)
- Text files (.txt, .md)
- Code files (.py, .js, etc.)
- Data files (.json, .csv)

---

## Tips

✓ Keep both terminals open when using web interface
✓ Watch sidebar for real-time cost tracking (web)
✓ Try default question first to see full flow
✓ Upload files for richer agent responses
✓ Edit agents to customize perspectives
✓ Download session JSON to keep results

---

## System Requirements

- Python 3.9+
- Node.js 16+ (for web interface)
- 8GB RAM minimum
- OpenAI API key with credits
- Modern browser (for web interface)
- SQLite (included) or PostgreSQL (for production multi-user deployment)

---

## Getting Help

1. Run `python3 test_setup.py` to verify setup
2. Check terminal outputs for error messages
3. Review API docs at http://localhost:8000/docs
4. Ensure API key is valid and has credits

## Documentation

For maintainer notes, architecture details, and technical implementation, see **[AGENTS.md](AGENTS.md)**

---

**Version:** 1.0.0 | **Last Updated:** December 10, 2025
