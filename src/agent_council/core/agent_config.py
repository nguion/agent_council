"""Agent configuration module - defines configuration structure."""

from dataclasses import dataclass, field
from typing import List, Optional, Literal
from enum import Enum


class ReasoningEffort(str, Enum):
    """Reasoning effort levels for GPT-5.1."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Verbosity(str, Enum):
    """Response verbosity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class AgentConfig:
    """Configuration for creating an agent."""
    
    name: str
    model: str = "gpt-5.1"
    instructions: str = "You are a helpful AI assistant."
    
    # Tools
    enable_web_search: bool = False
    enable_file_search: bool = False
    enable_shell: bool = False
    enable_code_interpreter: bool = False
    custom_tools: List = field(default_factory=list)
    
    # Model settings
    reasoning_effort: ReasoningEffort = ReasoningEffort.MEDIUM
    verbosity: Verbosity = Verbosity.LOW
    
    # Advanced
    max_turns: int = 10
    disable_tracing: bool = True
    
    def __post_init__(self):
        """Validate configuration."""
        if not self.name:
            raise ValueError("Agent name is required")
        if not any([self.enable_web_search, self.enable_file_search, 
                   self.enable_shell, self.enable_code_interpreter, self.custom_tools]):
            # No tools specified - that's okay, agent can work without tools
            pass

