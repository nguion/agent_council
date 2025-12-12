"""Agent builder module - creates configured agents."""

import os
import subprocess
from typing import Optional

from dotenv import load_dotenv

# Import agents SDK
try:
    from agents import (
        Agent,
        CodeInterpreterTool,
        FileSearchTool,
        ModelSettings,
        Runner,
        ShellTool,
        WebSearchTool,
        set_default_openai_key,
        set_tracing_disabled,
    )
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False
    Agent = None

from .agent_config import AgentConfig, ReasoningEffort, Verbosity


class AgentBuilder:
    """Builder for creating configured agents."""
    
    _initialized = False
    
    @classmethod
    def initialize(cls, api_key: Optional[str] = None, disable_tracing: bool = True):
        """Initialize the agent builder with API key."""
        if cls._initialized:
            return
        
        if not AGENTS_AVAILABLE:
            raise ImportError(
                "agents package not found. Install with: pip install openai-agents"
            )
        
        load_dotenv()
        key = api_key or os.getenv('OPENAI_API_KEY')
        if not key:
            raise ValueError("OPENAI_API_KEY not found. Set it in .env or pass as parameter.")
        
        set_default_openai_key(key)
        if disable_tracing:
            set_tracing_disabled(True)
        
        cls._initialized = True
    
    @classmethod
    def create(cls, config: AgentConfig) -> Agent:
        """Create an agent from configuration."""
        if not cls._initialized:
            cls.initialize(disable_tracing=config.disable_tracing)
        
        def default_shell_executor(command: str) -> str:
            """Simple shell executor used by ShellTool."""
            completed = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
            )
            output = completed.stdout or ""
            if completed.stderr:
                output += f"\nSTDERR:\n{completed.stderr}"
            return output.strip()
        
        # Build tools list
        tools = []
        if config.enable_web_search:
            tools.append(WebSearchTool())
        if config.enable_file_search:
            tools.append(FileSearchTool(vector_store_ids=config.file_search_vector_store_ids))
        if config.enable_shell:
            tools.append(ShellTool(executor=default_shell_executor))
        if config.enable_code_interpreter:
            tools.append(CodeInterpreterTool(tool_config={}))
        tools.extend(config.custom_tools)
        
        # Create model settings
        reasoning_effort = (
            config.reasoning_effort.value
            if isinstance(config.reasoning_effort, ReasoningEffort)
            else str(config.reasoning_effort)
        )
        verbosity_level = (
            config.verbosity.value
            if isinstance(config.verbosity, Verbosity)
            else str(config.verbosity)
        )
        model_settings = ModelSettings(
            reasoning={"effort": reasoning_effort},
            verbosity=verbosity_level,
        )
        
        # Create agent
        agent = Agent(
            name=config.name,
            model=config.model,
            instructions=config.instructions,
            tools=tools,
            model_settings=model_settings
        )
        
        return agent
    
    @classmethod
    def create_runner(cls) -> Runner:
        """Create a runner for executing agents."""
        if not cls._initialized:
            cls.initialize()
        return Runner()

