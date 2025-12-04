"""
Utility to condense large prompts when we hit context/token limits.
Splits the prompt into chunks, summarizes each, and stitches them back.
"""

from typing import Optional
from openai import OpenAI


def _summarize_chunk(client: OpenAI, chunk: str, logger=None, stage: str = "condense") -> str:
    """Summarize a chunk to ~50% length without losing key info."""
    messages = [
        {
            "role": "system",
            "content": (
                "You are a careful summarizer. Condense the provided text to about 50% "
                "of its length without losing critical facts, entities, numbers, or relationships. "
                "Do not add new information."
            ),
        },
        {"role": "user", "content": chunk},
    ]
    model_name = "gpt-5.1"
    resp = client.chat.completions.create(
        model=model_name,
        messages=messages,
        max_tokens=800,
        temperature=0.1,
    )
    summary = resp.choices[0].message.content
    if logger:
        usage = getattr(resp, "usage", None)
        usage_data = {
            "input_tokens": getattr(usage, "prompt_tokens", 0) if usage else 0,
            "output_tokens": getattr(usage, "completion_tokens", 0) if usage else 0,
            "total_tokens": getattr(usage, "total_tokens", 0) if usage else 0,
        }
        logger.log_llm_call(
            stage=stage, 
            agent_name="CondenseAgent", 
            prompt=chunk, 
            response=summary, 
            usage=usage_data,
            model=model_name
        )
    return summary


def condense_prompt(prompt: str, logger=None, stage: str = "condense") -> str:
    """
    Condense a large prompt by summarizing it in two halves.
    Returns the condensed prompt (original if summarization fails).
    """
    try:
        client = OpenAI()
        # Split into two halves to reduce context per call
        mid = len(prompt) // 2
        part1 = prompt[:mid]
        part2 = prompt[mid:]
        summary1 = _summarize_chunk(client, part1, logger=logger, stage=f"{stage}:part1")
        summary2 = _summarize_chunk(client, part2, logger=logger, stage=f"{stage}:part2")
        condensed = summary1.strip() + "\n\n" + summary2.strip()
        # One more light squeeze if still very long
        if len(condensed) > len(prompt) * 0.75:
            condensed = _summarize_chunk(client, condensed, logger=logger, stage=f"{stage}:final")
        return condensed
    except Exception:
        return prompt


