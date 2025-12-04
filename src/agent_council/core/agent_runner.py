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

        # Extract token usage - check multiple possible locations
        usage_data = {}
        total_input = 0
        total_output = 0
        
        # Debug: Print all attributes of result to help diagnose
        # Uncomment for debugging: print(f"DEBUG: result attributes: {dir(result)}")
        # Uncomment for debugging: print(f"DEBUG: result type: {type(result)}")
        
        # Method 1: Check result.usage (direct attribute)
        if hasattr(result, 'usage') and result.usage:
            usage = result.usage
            def get(u, *keys):
                for k in keys:
                    v = getattr(u, k, None) if not isinstance(u, dict) else u.get(k)
                    if v is not None and v != 0:
                        return v
                return None
            
            prompt_tokens = get(usage, 'prompt_tokens', 'input_tokens', 'input')
            completion_tokens = get(usage, 'completion_tokens', 'output_tokens', 'output')
            if prompt_tokens is not None:
                total_input = prompt_tokens
            if completion_tokens is not None:
                total_output = completion_tokens
        
        # Method 2: Check result.items for individual usage (aggregate if needed)
        if (total_input == 0 and total_output == 0) and hasattr(result, 'items') and result.items:
            for item in result.items:
                # Check if item has usage
                if hasattr(item, 'usage') and item.usage:
                    usage = item.usage
                    def get(u, *keys):
                        for k in keys:
                            v = getattr(u, k, None) if not isinstance(u, dict) else u.get(k)
                            if v is not None and v != 0:
                                return v
                        return None
                    prompt_tokens = get(usage, 'prompt_tokens', 'input_tokens', 'input')
                    completion_tokens = get(usage, 'completion_tokens', 'output_tokens', 'output')
                    if prompt_tokens:
                        total_input += prompt_tokens
                    if completion_tokens:
                        total_output += completion_tokens
                
                # Also check for response objects within items
                if hasattr(item, 'response') and item.response:
                    resp = item.response
                    if hasattr(resp, 'usage') and resp.usage:
                        usage = resp.usage
                        def get(u, *keys):
                            for k in keys:
                                v = getattr(u, k, None) if not isinstance(u, dict) else u.get(k)
                                if v is not None and v != 0:
                                    return v
                            return None
                        prompt_tokens = get(usage, 'prompt_tokens', 'input_tokens', 'input')
                        completion_tokens = get(usage, 'completion_tokens', 'output_tokens', 'output')
                        if prompt_tokens:
                            total_input += prompt_tokens
                        if completion_tokens:
                            total_output += completion_tokens
        
        # Method 3: Check for summary or aggregated usage
        if (total_input == 0 and total_output == 0) and hasattr(result, 'summary'):
            summary = result.summary
            if hasattr(summary, 'usage') and summary.usage:
                usage = summary.usage
                def get(u, *keys):
                    for k in keys:
                        v = getattr(u, k, None) if not isinstance(u, dict) else u.get(k)
                        if v is not None and v != 0:
                            return v
                    return None
                prompt_tokens = get(usage, 'prompt_tokens', 'input_tokens', 'input')
                completion_tokens = get(usage, 'completion_tokens', 'output_tokens', 'output')
                if prompt_tokens:
                    total_input = prompt_tokens
                if completion_tokens:
                    total_output = completion_tokens
        
        # Method 4: Check runner for aggregated usage (if runner tracks it)
        if (total_input == 0 and total_output == 0) and runner and hasattr(runner, 'usage'):
            runner_usage = runner.usage
            if runner_usage:
                def get(u, *keys):
                    for k in keys:
                        v = getattr(u, k, None) if not isinstance(u, dict) else u.get(k)
                        if v is not None and v != 0:
                            return v
                    return None
                prompt_tokens = get(runner_usage, 'prompt_tokens', 'input_tokens', 'input')
                completion_tokens = get(runner_usage, 'completion_tokens', 'output_tokens', 'output')
                if prompt_tokens:
                    total_input = prompt_tokens
                if completion_tokens:
                    total_output = completion_tokens
        
        # Method 5: Try to access via __dict__ or inspect all attributes
        if (total_input == 0 and total_output == 0):
            # Try to find any attribute that might contain usage
            for attr_name in dir(result):
                if 'usage' in attr_name.lower() and not attr_name.startswith('_'):
                    try:
                        attr_value = getattr(result, attr_name)
                        if attr_value:
                            def get(u, *keys):
                                for k in keys:
                                    v = getattr(u, k, None) if not isinstance(u, dict) else u.get(k)
                                    if v is not None and v != 0:
                                        return v
                                return None
                            prompt_tokens = get(attr_value, 'prompt_tokens', 'input_tokens', 'input')
                            completion_tokens = get(attr_value, 'completion_tokens', 'output_tokens', 'output')
                            if prompt_tokens:
                                total_input = prompt_tokens
                            if completion_tokens:
                                total_output = completion_tokens
                            if total_input > 0 or total_output > 0:
                                break
                    except Exception:
                        continue
        
        # Build usage_data dict
        usage_data = {
            "input_tokens": total_input or 0,
            "output_tokens": total_output or 0,
            "total_tokens": (total_input or 0) + (total_output or 0),
        }
        
        # Log if requested
        if logger:
            # If we couldn't find usage and logger is enabled, log a warning
            if total_input == 0 and total_output == 0:
                # Try one more time: check if result has __dict__ with usage info
                if hasattr(result, '__dict__'):
                    result_dict = result.__dict__
                    for key, value in result_dict.items():
                        if 'usage' in key.lower() and value:
                            try:
                                if hasattr(value, 'prompt_tokens'):
                                    usage_data["input_tokens"] = getattr(value, 'prompt_tokens', 0) or 0
                                if hasattr(value, 'completion_tokens'):
                                    usage_data["output_tokens"] = getattr(value, 'completion_tokens', 0) or 0
                                if hasattr(value, 'total_tokens'):
                                    usage_data["total_tokens"] = getattr(value, 'total_tokens', 0) or 0
                                if usage_data["input_tokens"] > 0 or usage_data["output_tokens"] > 0:
                                    total_input = usage_data["input_tokens"]
                                    total_output = usage_data["output_tokens"]
                                    break
                            except Exception:
                                continue
            
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

