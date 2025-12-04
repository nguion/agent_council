## Agent Council – Maintainer Notes (AGENTS.md)

This file is for people (or AI agents) working on the codebase. It summarizes how to set up, run, and extend the project without digging through multiple files.

### What this project does
- Orchestrates a council of GPT-5.1 agents with optional web search, file ingestion, and peer review.
- Builds personas, executes them in parallel, then performs peer review and chairman synthesis.
- Tracks token usage and cost.

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
pip install -e .
echo "OPENAI_API_KEY=sk-..." > .env
```

### How to run
```bash
python agentcouncil.py
```
Flow: prompt for question → optional context ingestion → council build → edit → parallel execution → peer review → chairman synthesis → results written to `council_session_complete.json` and `logs/`.

### Key files
- `agentcouncil.py`: CLI entrypoint for the 5-step flow.
- `src/agent_council/core/council_runner.py`: Builds per-agent instructions (name, persona, tool awareness) and executes them in parallel.
- `src/agent_council/core/agent_runner.py`: Runs an agent and captures tool usage (`web_search_call`, etc.) plus token usage.
- `src/agent_council/core/council_builder.py`: Uses GPT-5.1 to design the council personas (JSON output).
- `src/agent_council/core/council_reviewer.py` / `council_chairman.py`: Peer review and final synthesis.
- `setup.ps1`, `setup.sh`: One-command environment setup.
- `requirements.txt`, `setup.py`: Dependencies and packaging metadata.

### Tools and environment
- **Env:** `OPENAI_API_KEY` required. Stored in `.env` (created by setup scripts).
- **Models:** Defaults to `gpt-5.1`.
- **Tools per agent:** Web search (enabled per persona), optional file ingestion; tool usage is captured in results.
- **Context handling:** No hard truncation; if context is too large the runner will attempt summarization via `context_condense`.

### Outputs and logs
- `logs/*.md`: Session transcripts with prompts, responses, token usage, and cost.
- `council_session_complete.json`: Execution results, peer reviews, chairman verdict, and cost summary.

### Coding conventions / notes
- Keep agent instructions concise but explicit about tool availability.
- Prefer updating `AgentConfig`/`CouncilRunner` flows rather than hardcoding behavior in the CLI.
- Avoid committing `.env` or any API keys. `logs/` keeps only `.gitkeep`—clean old logs before committing.

### Common tasks
- **Add a new persona field or tool flag:** update `AgentConfig`, `CouncilBuilder` JSON schema expectations, and `CouncilRunner` instruction builder.
- **Inspect whether web search was used:** check `tools_used` in `execution_results` (expect `web_search_call` when enabled).
- **Adjust context handling:** `context_condense.py` controls summarization fallback.

