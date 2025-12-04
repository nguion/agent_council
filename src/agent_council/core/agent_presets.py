"""Pre-configured agent presets for common use cases."""

from .agent_config import AgentConfig, ReasoningEffort, Verbosity


def research_agent(name: str = "ResearchAgent") -> AgentConfig:
    """Agent optimized for research with web search."""
    return AgentConfig(
        name=name,
        instructions=(
            "You are a research assistant with web access. "
            "Search for current information and provide comprehensive, well-sourced answers."
        ),
        enable_web_search=True,
        reasoning_effort=ReasoningEffort.MEDIUM,
        verbosity=Verbosity.MEDIUM
    )


def coding_agent(name: str = "CodingAgent") -> AgentConfig:
    """Agent optimized for coding tasks."""
    return AgentConfig(
        name=name,
        instructions=(
            "You are a coding assistant. Write clean, efficient code. "
            "Test your solutions and explain your approach."
        ),
        enable_shell=True,
        enable_code_interpreter=True,
        reasoning_effort=ReasoningEffort.HIGH,
        verbosity=Verbosity.LOW
    )


def quick_agent(name: str = "QuickAgent") -> AgentConfig:
    """Fast agent for simple queries."""
    return AgentConfig(
        name=name,
        instructions="You are a helpful assistant. Provide concise, accurate answers.",
        reasoning_effort=ReasoningEffort.NONE,
        verbosity=Verbosity.LOW
    )


def analysis_agent(name: str = "AnalysisAgent") -> AgentConfig:
    """Agent for deep analysis and reasoning."""
    return AgentConfig(
        name=name,
        instructions=(
            "You are an analytical assistant. Think deeply about problems, "
            "consider multiple perspectives, and provide thorough analysis."
        ),
        enable_web_search=True,
        enable_file_search=True,
        reasoning_effort=ReasoningEffort.HIGH,
        verbosity=Verbosity.HIGH
    )


def general_agent(name: str = "GeneralAgent") -> AgentConfig:
    """General-purpose agent with balanced settings."""
    return AgentConfig(
        name=name,
        instructions="You are a helpful AI assistant.",
        enable_web_search=True,
        reasoning_effort=ReasoningEffort.MEDIUM,
        verbosity=Verbosity.LOW
    )

