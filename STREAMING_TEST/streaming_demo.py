#!/usr/bin/env python
"""
Streaming demo for GPT-5.1 using the Responses API.

Goals:
- Show how to stream text to the terminal (and later the UI).
- Keep everything self-contained so the pattern is easy to copy into the
  Agent Council codebase or other scripts.

How this relates to the repo:
- The main app uses the OpenAI Agents SDK (`AgentBuilder` / `Runner`) which
  wraps model calls but does not expose token streaming.
- This script demonstrates direct `responses.stream` usage so we can wire a
  streaming experience into the UI or CLI without changing the existing agent
  pipeline yet.

Usage:
  OPENAI_API_KEY=sk-... python streaming_demo.py "Write a 2-line poem"

Flags:
-m / --model               Model name (default: gpt-5.1)
-t / --temperature         Temperature for the response (default: 0.6)
-k / --max-output-tokens   Max output tokens (default: 400)
-d / --debug-events        Log every event type (good for UI wiring)

Notes:
- Requires openai >= 1.30 and Python 3.9+.
- For "thinking" style traces in a UI, enable --debug-events and capture the
  event stream; only `response.output_text.delta` is rendered to stdout here.
"""

import argparse
import os
import sys
from typing import Iterable, Optional

from openai import OpenAI


def require_api_key() -> str:
    """Return the API key or exit with a helpful error."""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        msg = (
            "OPENAI_API_KEY is missing. Export it or place it in a .env file.\n"
            "Example:\n"
            '  export OPENAI_API_KEY="sk-..."\n'
            "  python streaming_demo.py \"hello\""
        )
        raise SystemExit(msg)
    return key


def stream_response(
    question: str,
    *,
    model: str = "gpt-5.1",
    temperature: float = 0.6,
    max_output_tokens: int = 400,
    debug_events: bool = False,
) -> str:
    """
    Stream a response from GPT-5.1 to stdout and return the final text.

    The OpenAI Responses API emits typed events; we print only text deltas
    for a smooth user-facing stream, but `--debug-events` will log the raw
    event types so we can observe "thinking" phases and wire them into the UI.
    """
    client = OpenAI(api_key=require_api_key())

    print(f"Model: {model}")
    print(f"Question: {question}")
    print("\n--- streaming output ---\n")

    collected_chunks: list[str] = []

    # responses.stream() yields low-latency events; no need to set stream=True.
    with client.responses.stream(
        model=model,
        input=[{"role": "user", "content": question}],
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    ) as stream:
        for event in stream:
            if event.type == "response.output_text.delta":
                chunk: Optional[str] = getattr(event, "delta", None)
                if chunk:
                    collected_chunks.append(chunk)
                    print(chunk, end="", flush=True)
            elif debug_events:
                # Useful when designing UI hooks for "thinking" or tool calls.
                printable = getattr(event, "type", "unknown")
                detail = getattr(event, "delta", "") or getattr(event, "event", "")
                print(f"\n[debug] {printable}: {detail}", flush=True)

        # Gather the final aggregated response and usage for logging/metrics.
        final_response = stream.get_final_response()

    print("\n\n--- completed ---\n")

    full_text = getattr(final_response, "output_text", "") or "".join(collected_chunks)
    usage = getattr(final_response, "usage", None)
    if usage:
        # usage fields: input_tokens/output_tokens/total_tokens
        print(
            f"Tokens → input={usage.input_tokens}, "
            f"output={usage.output_tokens}, total={usage.total_tokens}"
        )

    return full_text


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GPT-5.1 streaming demo")
    parser.add_argument("question", help="Prompt to send to the model")
    parser.add_argument("-m", "--model", default="gpt-5.1", help="Model name")
    parser.add_argument(
        "-t",
        "--temperature",
        type=float,
        default=0.6,
        help="Sampling temperature",
    )
    parser.add_argument(
        "-k",
        "--max-output-tokens",
        type=int,
        default=400,
        help="Maximum tokens the model may return",
    )
    parser.add_argument(
        "-d",
        "--debug-events",
        action="store_true",
        help="Print every streaming event (good for UI wiring)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    try:
        stream_response(
            args.question,
            model=args.model,
            temperature=args.temperature,
            max_output_tokens=args.max_output_tokens,
            debug_events=args.debug_events,
        )
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

