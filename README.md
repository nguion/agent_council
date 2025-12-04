# Agent Council

A modular, agentic framework for creating, customizing, and executing councils of specialized AI agents (powered by GPT-5.1) to solve complex problems in parallel.

## Features

*   **Multi-Step Workflow**:
    1.  **Ingest**: Accepts questions and context files (PDF, DOCX, TXT, MD).
    2.  **Build**: Uses an Architect Agent to propose a diverse council of experts.
    3.  **Edit**: Interactively refine the council (add/remove/edit agents).
    4.  **Execute**: Runs all agents in parallel, aggregating their unique perspectives.
*   **High Modularity**: Agents, tools, and runners are decoupled and easy to extend.
*   **GPT-5.1 Integration**: Native support for reasoning effort configuration (`none`, `low`, `medium`, `high`).
*   **CLI Interface**: Rich terminal UI for easy interaction.

## Installation & Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Set your API key in `.env`:
```bash
OPENAI_API_KEY=sk-...
```

## Usage (5-step flow)

```bash
python3 test_flow_full.py
```

Steps:
1) Input question + optional context files (pdf, docx, txt, md).  
2) Build council personas (automatic).  
3) Edit council (add/remove/edit personas).  
4) Execute agents in parallel (live table).  
5) Peer review + chairman synthesis (scores + final answer).

### Project Structure

```
src/agent_council/
├── core/               # Core logic
│   ├── agent_builder.py
│   ├── agent_config.py
│   ├── agent_runner.py
│   ├── council_builder.py
│   ├── council_editor.py
│   └── council_runner.py
└── utils/              # Utilities
    ├── file_ingestion.py
    ├── session_logger.py
    └── context_condense.py
```

## Configuration

You can manually create agents using the `AgentBuilder`:

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

## Outputs & Logging
- `logs/` (markdown): every prompt/response + token counts (per run).  
- `council_session_complete.json`: full results, peer review scores, chairman verdict, token totals.  
- Progress tables show live status; TLDRs printed for quick inspection.

## Notes for Agentic Tools
- `a.agents` provides a minimal descriptor: entrypoint `python3 test_flow_full.py`, requires `OPENAI_API_KEY`.
- Tools enabled per persona: web search can be toggled; tool usage is recorded in outputs.

