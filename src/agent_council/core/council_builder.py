"""
Council Builder Module.
Uses an LLM agent to analyze a query and context, then proposes a council of agents.
"""

import json
from typing import List, Dict, Any
from .agent_config import AgentConfig, ReasoningEffort, Verbosity
from .agent_builder import AgentBuilder
from .agent_runner import run_agent

class CouncilBuilder:
    """Manages the creation of agent councils."""

    SYSTEM_INSTRUCTIONS = """
    You are the Council Builder. Your goal is to analyze a user's problem and background context, 
    then design a "Council" of specialized AI agents to solve it from diverse perspectives.

    INPUT:
    1. User Question/Goal
    2. Context Documents (if any)

    OUTPUT:
    You must return ONLY a valid JSON object containing a list of agents. 
    Do not include markdown formatting like ```json ... ```. Just the raw JSON string.
    
    Structure:
    {
        "council_name": "Name of this group",
        "strategy_summary": "Brief explanation of why these agents (council members) were chosen",
        "agents": [
            {
                "name": "AgentName",
                "persona": "Detailed persona description (WHO they are)",
                "reasoning_effort": "medium", 
                "enable_web_search": true/false
            },
            ...
        ]
    }

    GUIDELINES:
    - Choose a well rounded set of agents (3-5 council members recommended) with distinct, complementary perspectives relevant to the specific problem.
    - DEFINE THE PERSONA, NOT THE TASK. The task will be assigned later. Focus on "Who this agent is", "What is their background/expertise", "What is their bias/perspective".
    - For example: "You are a veteran Financial Analyst with 20 years of experience in the X industry. You focus purely on numbers, margins, and shareholder value. You are skeptical of unproven innovations."
    - Set 'enable_web_search' to true if the persona needs current real-world data, unless they are purely theoretical/abstract (like emboding a prominent/notable entrepreneur or philosopher or researcher) this should be true.
    - Set 'reasoning_effort' to 'high' for complex analytical personas, 'medium' for general ones.
    """

    @classmethod
    async def build_council(cls, question: str, context_data: List[Dict[str, Any]], logger=None) -> Dict[str, Any]:
        """
        Generates a council configuration based on the question and context.
        """
        
        # Prepare context string
        context_str = ""
        if context_data:
            context_str += "\n\n=== SUPPORTING CONTEXT ===\n"
            for item in context_data:
                meta = item['metadata']
                context_str += f"\n--- File: {meta['filename']} ---\n"
                content = item['content']
                # Removed hard truncation: rely on condense_prompt in agent_runner if limits hit
                context_str += content
        
        full_prompt = f"""
        USER QUESTION: {question}
        
        {context_str}
        
        Based on the above, design the perfect Agent Council. Return strictly JSON.
        """

        # Create the builder agent
        config = AgentConfig(
            name="CouncilBuilder",
            instructions=cls.SYSTEM_INSTRUCTIONS,
            reasoning_effort=ReasoningEffort.HIGH, # Needs to think deeply about architecture
            verbosity=Verbosity.LOW # We want strict JSON
        )
        
        agent = AgentBuilder.create(config)
        
        # Run agent
        # We use a loop to retry if JSON parsing fails (simple robustness)
        max_retries = 2
        last_error = None
        
        for _ in range(max_retries):
            try:
                response_text, _, _ = await run_agent(
                    agent, full_prompt, verbose=False,
                    logger=logger, stage="council_builder",
                    return_full=True
                )
                
                # Clean up potential markdown code blocks if the model ignores instructions
                cleaned_text = response_text.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.startswith("```"):
                    cleaned_text = cleaned_text[3:]
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]
                
                data = json.loads(cleaned_text)
                return data
                
            except json.JSONDecodeError as e:
                last_error = e
                print(f"JSON Parse Error in Council Builder: {e}. Retrying...")
                full_prompt += "\n\nPREVIOUS ATTEMPT FAILED. RETURN ONLY RAW VALID JSON."
            except Exception as e:
                last_error = e
                print(f"Error in Council Builder: {e}")
        
        # If we get here, it failed
        return {
            "error": f"Failed to generate valid council JSON after retries. Last error: {last_error}",
            "raw_response": response_text if 'response_text' in locals() else "No response"
        }

