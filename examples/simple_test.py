#!/usr/bin/env python3
"""Clean, simple agent test script."""

from agent_council.core.agent_config import AgentConfig, ReasoningEffort
from agent_council.core.agent_builder import AgentBuilder
from agent_council.core.agent_runner import run_agent_sync


def main():
    """Test agent with web search and reasoning."""
    
    # Create configuration
    config = AgentConfig(
        name="ResearchAgent",
        instructions=(
            "You are a research assistant with web access and enhanced reasoning. "
            "Use web search for current information. Think through problems carefully."
        ),
        enable_web_search=True,
        reasoning_effort=ReasoningEffort.MEDIUM
    )
    
    # Create and run agent
    agent = AgentBuilder.create(config)
    response = run_agent_sync(
        agent,
        "What are the latest developments in artificial intelligence?",
        verbose=True
    )
    
    print("=" * 70)
    print("Response:")
    print("=" * 70)
    print(response)
    print("=" * 70)


if __name__ == "__main__":
    main()

