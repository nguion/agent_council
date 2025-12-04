# Agent Council

A modular, agentic framework for creating, customizing, and executing councils of specialized AI agents to solve complex problems in parallel. Powered by GPT-5.1 and the OpenAI Agents SDK.

## Overview

Agent Council automates the process of gathering diverse expert perspectives on a complex problem. Instead of a single model response, it:
1.  **Ingests Context**: Reads your documents (PDF, DOCX, TXT, MD) to understand the background.
2.  **Builds a Council**: Automatically proposes a team of specialized agents (personas) tailored to the specific question.
3.  **Executes in Parallel**: Runs each agent simultaneously to generate independent, well-reasoned answers.
4.  **Peer Reviews**: Agents critique each other's work to identify strengths and weaknesses.
5.  **Synthesizes**: A "Chairman" agent aggregates all insights into a final, comprehensive verdict.

## Features

-   **Adaptive Council Generation**: The system "architects" the perfect team for your specific query (e.g., a legal expert, a financial analyst, and a creative strategist for a business problem).
-   **Human-in-the-Loop**: Interactively edit, add, or remove agents before execution.
-   **Multi-Modal Context**: seamlessly ingest text and documents.
-   **Parallel Execution**: Agents run concurrently for speed.
-   **Peer Review System**: Automated scoring and critique improves reliability.
-   **Rich Terminal UI**: Interactive, beautiful CLI experience.
-   **GPT-5.1 Powered**: Leverages advanced reasoning capabilities (configurable effort: `low`, `medium`, `high`).

## Prerequisites

-   **Python 3.10+**
-   **OpenAI API Key** (with access to GPT-5.1 or compatible models)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repo-url>
    cd agent_council
    ```

2.  **Set up a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    pip install -e .
    ```

4.  **Configure Environment:**
    Create a `.env` file in the project root and add your API key:
    ```env
    OPENAI_API_KEY=sk-...
    ```

## Usage

Run the interactive council session:

```bash
python3 run_council.py
```

### The 5-Step Flow

1.  **Input**: Enter your core question and drag-and-drop context files.
2.  **Build**: The Architect Agent analyzes the request and proposes a council.
3.  **Edit**: Review the proposed agents. You can edit their instructions, change their reasoning effort, or add/remove members.
4.  **Execute**: Watch as agents process the task in real-time.
5.  **Synthesize**: Review the peer feedback and read the Chairman's final verdict.

## Project Structure

```text
src/agent_council/
├── core/               # Core logic for agents and council management
│   ├── agent_builder.py    # Factory for creating individual agents
│   ├── council_builder.py  # Architect agent logic
│   ├── council_editor.py   # Interactive CLI for council modification
│   ├── council_runner.py   # Parallel execution engine
│   ├── council_reviewer.py # Peer review system
│   └── council_chairman.py # Synthesis logic
└── utils/              # Helper utilities
    ├── file_ingestion.py   # Document parsing
    └── session_logger.py   # Logging and token tracking
```

## Configuration

You can manually create agents using the `AgentBuilder` in your own scripts (see `examples/simple_test.py`):

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

## Outputs

-   **Console**: Real-time progress tables and TLDR summaries.
-   **Session JSON**: `council_session_complete.json` contains the full interaction, including all agent responses, peer reviews, scores, and the final verdict.
-   **Logs**: Detailed markdown logs are saved in the `logs/` directory for debugging and audit.

## For AI Agents

See [.agents](.agents) for a machine-readable description of this repository's capabilities and entry points.
