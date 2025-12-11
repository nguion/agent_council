## GPT-5.1 Streaming Side Quest

Purpose: prove out terminal/UI streaming for GPT-5.1 responses without touching the existing Agent Council pipeline yet.

### What lives here
- `streaming_demo.py` – minimal Responses API streaming sample with inline docs.

### Why this is separate
- The main app uses the OpenAI Agents SDK (`AgentBuilder` + `Runner`) which does not surface token-level streaming.
- This demo shows the lower-level Responses API so we can copy the pattern into the UI (or wrap it in the runner later).

### Run it
```bash
cd STREAMING_TEST
OPENAI_API_KEY=sk-... python streaming_demo.py "Write a 2-line poem"
# add --debug-events to see all event types (useful for UI thinking traces)
```

### Wiring ideas for the UI
- Terminal: keep the print loop as-is; it renders `response.output_text.delta` chunks as they arrive.
- UI preview: pipe each delta to the UI state; when `--debug-events` is on, you can also surface non-text events (thinking/tool calls) in a sidebar.
- Metrics: the final response has `usage.input_tokens/output_tokens/total_tokens` ready for cost tracking.

### Notes
- Tested with the OpenAI Python SDK 1.30+ (Responses API). No extra deps beyond `openai` and stdlib.
- Model defaults to `gpt-5.1`, but the script accepts `--model` for quick comparisons.

