"""
Session logger to capture prompts/responses and token usage for every LLM call.
Writes a markdown file per session and accumulates token totals and costs.
"""

import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any


# Pricing per million tokens (as of December 2024/January 2025)
# Source: https://openai.com/api/pricing/
MODEL_PRICING = {
    # GPT-5 Series
    "gpt-5.1": {"input": 1.25, "output": 10.00},
    "gpt-5": {"input": 1.25, "output": 10.00},  # Alias
    "gpt-5-mini": {"input": 0.25, "output": 2.00},
    "gpt-5-nano": {"input": 0.05, "output": 0.40},
    "gpt-5-pro": {"input": 15.00, "output": 120.00},
    
    # GPT-4 Series
    "gpt-4.1": {"input": 2.00, "output": 8.00},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
    "gpt-4o": {"input": 2.50, "output": 10.00},  # Estimated, may vary
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-4": {"input": 30.00, "output": 60.00},
    
    # GPT-3.5 Series
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    
    # Default fallback (GPT-4o pricing as conservative estimate)
    "default": {"input": 2.50, "output": 10.00},
}


def get_model_pricing(model: str) -> Dict[str, float]:
    """Get pricing for a model, with fallback to default."""
    model_lower = model.lower()
    # Try exact match first
    if model_lower in MODEL_PRICING:
        return MODEL_PRICING[model_lower]
    # Try partial match (e.g., "gpt-5.1" matches "gpt-5.1")
    for key, pricing in MODEL_PRICING.items():
        if key in model_lower or model_lower in key:
            return pricing
    # Fallback to default
    return MODEL_PRICING["default"]


def calculate_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    """Calculate cost in USD for given tokens and model."""
    pricing = get_model_pricing(model)
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost


class SessionLogger:
    def __init__(self, output_dir: str = "logs"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.session_id = f"session_{ts}_{uuid.uuid4().hex[:6]}"
        self.path = os.path.join(self.output_dir, f"{self.session_id}.md")
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
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
        model: Optional[str] = None,
        tools_used: Optional[Any] = None,
        error: bool = False,
    ):
        in_tokens = usage.get("input_tokens", 0) if usage else 0
        out_tokens = usage.get("output_tokens", 0) if usage else 0
        # Ensure we have integers, not None
        in_tokens = int(in_tokens) if in_tokens else 0
        out_tokens = int(out_tokens) if out_tokens else 0
        self.total_input_tokens += in_tokens
        self.total_output_tokens += out_tokens
        
        # Calculate cost for this call
        model_name = model or "default"
        call_cost = calculate_cost(in_tokens, out_tokens, model_name)
        self.total_cost += call_cost

        with open(self.path, "a", encoding="utf-8") as f:
            status = "ERROR" if error else "OK"
            f.write(f"### Stage: {stage} | Agent: {agent_name} | Status: {status}\n\n")
            f.write(f"- Model: {model_name}\n")
            if in_tokens is not None or out_tokens is not None:
                f.write(f"- input_tokens: {in_tokens:,}\n")
                f.write(f"- output_tokens: {out_tokens:,}\n")
                f.write(f"- Cost: ${call_cost:.6f}\n")
            if tools_used:
                f.write(f"- tools_used: {tools_used}\n")
            f.write("\n**Prompt:**\n\n")
            f.write("```\n")
            f.write(prompt.strip() + "\n")
            f.write("```\n\n")
            f.write("**Response:**\n\n")
            f.write("```\n")
            f.write(response.strip() + "\n")
            f.write("```\n\n")

    def finalize(self):
        """Write a session summary to the log file."""
        total_tokens = (self.total_input_tokens or 0) + (self.total_output_tokens or 0)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write("## Summary\n\n")
            f.write(
                f"- input_tokens: {self.total_input_tokens or 0:,}\n"
                f"- output_tokens: {self.total_output_tokens or 0:,}\n"
                f"- total_tokens: {total_tokens:,}\n"
                f"- total_cost_usd: ${self.total_cost:.6f}\n\n"
            )

    def summary(self) -> str:
        total_tokens = (self.total_input_tokens or 0) + (self.total_output_tokens or 0)
        return (
            f"Tokens — input: {self.total_input_tokens or 0:,}, "
            f"output: {self.total_output_tokens or 0:,}, "
            f"total: {total_tokens:,} | "
            f"Cost: ${self.total_cost:.4f}"
        )
    
    def get_cost_breakdown(self) -> Dict[str, Any]:
        """Get detailed cost breakdown."""
        return {
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost_usd": round(self.total_cost, 6),
        }


