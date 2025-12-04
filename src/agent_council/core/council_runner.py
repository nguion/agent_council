"""
Council Runner Module.
Orchestrates the parallel execution of the agent council.
"""

import asyncio
import json
from typing import Dict, Any, List, Callable
from .agent_config import AgentConfig, ReasoningEffort
from .agent_builder import AgentBuilder
from .agent_runner import run_agent

class CouncilRunner:
    """Executes the council agents in parallel."""

    @staticmethod
    def make_tldr(text: str, max_len: int = 240) -> str:
        """Create a lightweight TLDR without extra model calls."""
        clean = text.strip().replace("\n", " ")
        if len(clean) <= max_len:
            return clean
        return clean[: max_len - 3].rstrip() + "..."

    @staticmethod
    async def run_single_agent(
        agent_config: Dict[str, Any], 
        prompt: str,
        progress_callback: Callable[[str, str], None] = None,
        logger=None
    ) -> Dict[str, Any]:
        """
        Builds and runs a single agent.
        Returns a dict with the agent's identity, response, and TLDR.
        """
        agent_name = agent_config.get('name', 'Unknown Agent')
        if progress_callback:
            progress_callback(agent_name, "Initializing...")

        try:
            effort_str = agent_config.get('reasoning_effort', 'medium').lower()
            effort_enum = ReasoningEffort.MEDIUM
            if effort_str == 'high': effort_enum = ReasoningEffort.HIGH
            elif effort_str == 'low': effort_enum = ReasoningEffort.LOW
            elif effort_str == 'none': effort_enum = ReasoningEffort.NONE

            # Standardized Task Instruction with TLDR request
            STANDARD_TASK = (
                "YOUR JOB: Completely, comprehensively, and accurately use the tools at your disposal "
                "to fully and thoroughly answer the user's query.\n\n"
                "FORMAT REQUIREMENT: Start your response with a 'TLDR:' section (max 2-3 sentences) "
                "summarizing your key points, followed by your full detailed response.\n\n"
            )

            # Agent Persona
            persona = agent_config.get('persona', 'You are a helpful assistant.')
            full_instructions = f"{STANDARD_TASK}YOUR PERSONA: {persona}"

            # Build the agent
            config = AgentConfig(
                name=agent_name,
                instructions=full_instructions,
                enable_web_search=agent_config.get('enable_web_search', False),
                reasoning_effort=effort_enum
            )
            
            agent = AgentBuilder.create(config)
            
            if progress_callback:
                progress_callback(agent_name, "Thinking & Searching...")

            # Run the agent
            response_text, usage_data, tools_used = await run_agent(
                agent, prompt, verbose=False,
                logger=logger, stage=f"execution:{agent_name}",
                return_full=True
            )
            
            if progress_callback:
                progress_callback(agent_name, "Done")

            # Extract TLDR if present
            tldr = "No TLDR provided."
            if "TLDR:" in response_text:
                parts = response_text.split("TLDR:", 1)[1]
                # Split by double newline to get just the first paragraph/block
                tldr = parts.split("\n\n", 1)[0].strip()
            elif "**TLDR:**" in response_text:
                parts = response_text.split("**TLDR:**", 1)[1]
                tldr = parts.split("\n\n", 1)[0].strip()
            else:
                tldr = CouncilRunner.make_tldr(response_text)

            return {
                "agent_name": config.name,
                "agent_persona": agent_config.get('persona', 'Participant'),
                "response": response_text,
                "tldr": tldr,
                "status": "success",
                "tools_used": tools_used or []
            }
            
        except Exception as e:
            if progress_callback:
                progress_callback(agent_name, "Failed")
            return {
                "agent_name": agent_name,
                "agent_persona": agent_config.get('persona', 'Participant'),
                "response": str(e),
                "tldr": "Execution failed.",
                "status": "error",
                "tools_used": []
            }

    @classmethod
    async def execute_council(
        cls, 
        council_config: Dict[str, Any], 
        question: str, 
        context_data: List[Dict[str, Any]],
        progress_callback: Callable[[str, str], None] = None,
        logger=None
    ) -> Dict[str, Any]:
        """
        Runs all agents in the council in parallel.
        """
        agents_data = council_config.get('agents', [])
        if not agents_data:
            return {"error": "No agents found in council configuration."}

        # Prepare the full prompt
        context_str = ""
        if context_data:
            context_str += "\n\n=== BACKGROUND CONTEXT ===\n"
            for item in context_data:
                meta = item['metadata']
                context_str += f"\n--- Source: {meta['filename']} ---\n"
                content = item['content']
                if len(content) > 15000:
                    content = content[:15000] + "... [truncated]"
                context_str += content
        
        full_prompt = f"""
        QUESTION: {question}

        {context_str}

        Please answer the question based on your role and the provided context.
        """

        if progress_callback:
            progress_callback("ALL", f"Starting execution for {len(agents_data)} agents...")
            for a in agents_data:
                progress_callback(a.get('name', 'Unknown'), "Queued")

        # Create tasks for all agents
        tasks = [
            cls.run_single_agent(agent_conf, full_prompt, progress_callback, logger) 
            for agent_conf in agents_data
        ]
        
        # Run them all at once
        results = await asyncio.gather(*tasks)

        # Assign stable proposal_ids (1-based) for downstream review/ranking
        for idx, r in enumerate(results, start=1):
            r["proposal_id"] = idx
        
        final_output = {
            "council_name": council_config.get('council_name', 'Unnamed Council'),
            "original_question": question,
            "execution_results": results
        }
        
        return final_output
