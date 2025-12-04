"""
Session logger to capture prompts/responses and token usage for every LLM call.
Writes a markdown file per session and accumulates token totals.
"""

import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any


class SessionLogger:
    def __init__(self, output_dir: str = "logs"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.session_id = f"session_{ts}_{uuid.uuid4().hex[:6]}"
        self.path = os.path.join(self.output_dir, f"{self.session_id}.md")
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self._write_header()

    def _write_header(self):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(f"# LLM Session Log\n\n")
            f.write(f"- Session: {self.session_id}\n")
            f.write(f"- Started (UTC): {datetime.utcnow().isoformat()}\n\n")
            f.write("## Calls\n\n")

    def log_llm_call(
        self,
        stage: str,
        agent_name: str,
        prompt: str,
        response: str,
        usage: Optional[Dict[str, Any]] = None,
    ):
        in_tokens = usage.get("input_tokens", 0) if usage else 0
        out_tokens = usage.get("output_tokens", 0) if usage else 0
        # Ensure we have integers, not None
        in_tokens = int(in_tokens) if in_tokens else 0
        out_tokens = int(out_tokens) if out_tokens else 0
        self.total_input_tokens += in_tokens
        self.total_output_tokens += out_tokens

        with open(self.path, "a", encoding="utf-8") as f:
            f.write(f"### Stage: {stage} | Agent: {agent_name}\n\n")
            if in_tokens is not None or out_tokens is not None:
                f.write(f"- input_tokens: {in_tokens}\n")
                f.write(f"- output_tokens: {out_tokens}\n\n")
            f.write("**Prompt:**\n\n")
            f.write("```\n")
            f.write(prompt.strip() + "\n")
            f.write("```\n\n")
            f.write("**Response:**\n\n")
            f.write("```\n")
            f.write(response.strip() + "\n")
            f.write("```\n\n")

    def summary(self) -> str:
        return (
            f"Tokens — input: {self.total_input_tokens or 0}, "
            f"output: {self.total_output_tokens or 0}, "
            f"total: {(self.total_input_tokens or 0) + (self.total_output_tokens or 0)}"
        )


