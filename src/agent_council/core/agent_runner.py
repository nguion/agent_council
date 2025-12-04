"""Agent runner utilities - execute agents and handle results."""

import asyncio
from typing import Optional
from agents import Agent, Runner
from .agent_builder import AgentBuilder
from agent_council.utils.context_condense import condense_prompt


async def run_agent(
    agent: Agent,
    query: str,
    runner: Optional[Runner] = None,
    max_turns: int = 10,
    verbose: bool = True,
    logger=None,
    stage: str = "",
    return_full: bool = False
):
    """
    Run an agent with a query and return the response.
    
    Args:
        agent: The agent to run
        query: The query/prompt for the agent
        runner: Optional runner instance (creates one if not provided)
        max_turns: Maximum number of turns
        verbose: Whether to print progress
    
    Returns:
        The agent's response as a string
    """
    if runner is None:
        runner = AgentBuilder.create_runner()
    
    if verbose:
        print(f"🤖 {agent.name}: Processing query...")
        print(f"📝 Query: {query}\n")
    
    try:
        try:
            result = await runner.run(agent, query, max_turns=max_turns)
        except Exception as e:
            # Attempt context condensation on length/context errors, then retry once
            err_msg = str(e).lower()
            if "context" in err_msg or "token" in err_msg or "max" in err_msg:
                if verbose:
                    print("⚠️ Context too large, condensing and retrying...")
                condensed_query = condense_prompt(query, logger=logger, stage=f"{stage}:condense")
                result = await runner.run(agent, condensed_query, max_turns=max_turns)
                query = condensed_query  # so we log what we actually sent
            else:
                raise
        
        # Extract response text
        if hasattr(result, 'output') and result.output:
            response = result.output
        elif hasattr(result, 'final_output'):
            response = result.final_output
        else:
            # Try to extract from RunResult string representation
            result_str = str(result)
            if "Final output (str):" in result_str:
                # Extract the actual output from the RunResult string
                parts = result_str.split("Final output (str):")
                if len(parts) > 1:
                    response = parts[1].strip().split("\n")[0].strip()
                else:
                    response = result_str
            else:
                response = result_str
        
        # Extract tool usage if present
        tools_used = []
        try:
            items = getattr(result, "items", None)
            if items:
                for it in items:
                    name = getattr(it, "tool_name", None) or getattr(it, "tool", None)
                    if name:
                        tools_used.append(name)
        except Exception:
            tools_used = []

        # Extract token usage from result.context_wrapper.usage (per OpenAI Agents SDK docs)
        usage_data = {}
        total_input = 0
        total_output = 0
        
        # Method 1: Check result.context_wrapper.usage (correct path per SDK documentation)
        if hasattr(result, 'context_wrapper') and hasattr(result.context_wrapper, 'usage'):
            usage = result.context_wrapper.usage
            # SDK provides these attributes directly
            total_input = getattr(usage, 'input_tokens', 0) or 0
            total_output = getattr(usage, 'output_tokens', 0) or 0
        
        # Build usage_data dict
        usage_data = {
            "input_tokens": int(total_input) if total_input else 0,
            "output_tokens": int(total_output) if total_output else 0,
            "total_tokens": int(total_input + total_output) if (total_input or total_output) else 0,
        }
        
        # Log if requested
        if logger:
            logger.log_llm_call(
                stage=stage or "unspecified",
                agent_name=getattr(agent, "name", "unknown"),
                prompt=query,
                response=response,
                usage=usage_data
            )

        if verbose:
            print("✅ Response received\n")
            if usage_data.get('total_tokens', 0) > 0:
                print(f"📊 Tokens: Input={usage_data.get('input_tokens', 0)}, Output={usage_data.get('output_tokens', 0)}, Total={usage_data.get('total_tokens', 0)}")
                print()
        
        if return_full:
            return response, usage_data if 'usage_data' in locals() else {}, tools_used
        return response
    
    except Exception as e:
        if verbose:
            print(f"❌ Error: {e}\n")
        raise


def run_agent_sync(
    agent: Agent,
    query: str,
    runner: Optional[Runner] = None,
    max_turns: int = 10,
    verbose: bool = True
) -> str:
    """Synchronous wrapper for run_agent."""
    return asyncio.run(run_agent(agent, query, runner, max_turns, verbose))

