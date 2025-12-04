"""
Council Chairman Module.
Synthesizes the final response from agent outputs and peer critiques.
"""

import asyncio
from typing import Dict, Any, List
from .agent_config import AgentConfig, ReasoningEffort, Verbosity
from .agent_builder import AgentBuilder
from .agent_runner import run_agent

class CouncilChairman:
    """The final decision maker who synthesizes the council's work."""

    CHAIRMAN_INSTRUCTIONS = """
    You are the Council Chairman. You preside over a council of specialized AI experts.
    
    YOUR GOAL:
    Synthesize the "Ultimate Best Response" to the user's question by integrating the diverse 
    perspectives, proposals, and critiques from your council members.

    PROCESS:
    1. Read the Original Question.
    2. Analyze the Proposals from your council members.
    3. Consider the Peer Critiques (where members pointed out flaws in each other's work).
    4. Filter out noise, weak arguments, or hallucinations identified by peers.
    5. Elevate the strongest, most novel, and most realistic ideas.
    6. Draft a cohesive, authoritative final answer.

    TONE:
    Professional, decisive, comprehensive, and nuanced. You are the unified voice of the council.
    DO NOT invent new ideas not present in the council's work unless necessary to bridge gaps.
    DO NOT simply summarize agent-by-agent. Create a unified narrative.
    """

    @staticmethod
    def _truncate_for_token_limit(text: str, max_chars: int = 10000) -> str:
        """Simple truncation to prevent context overflow."""
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "... [truncated]"

    @classmethod
    async def synthesize(
        cls, 
        question: str, 
        execution_results: List[Dict[str, Any]], 
        peer_reviews: List[Dict[str, Any]],
        logger=None
    ) -> str:
        """
        Runs the Chairman agent to produce the final output.
        """
        
        # 1. Aggregate Proposals (anonymized by proposal_id)
        proposals_text = "\n=== COUNCIL PROPOSALS (Anonymized) ===\n"
        for res in execution_results:
            pid = res.get('proposal_id', 0)
            # Summarize/truncate if very long
            content = cls._truncate_for_token_limit(res['response'], max_chars=8000)
            proposals_text += f"\n--- Proposal #{pid} ---\n{content}\n"

        # 2. Aggregate Critiques (structured, anonymized)
        critiques_text = "\n=== PEER REVIEW SCORES & FEEDBACK (Anonymized) ===\n"
        for idx, review in enumerate(peer_reviews, start=1):
            parsed = review.get('parsed')
            if parsed:
                # Drop reviewer identity for anonymity
                parsed_clean = dict(parsed)
                parsed_clean.pop("reviewer", None)
                critiques_text += f"\n[Review {idx}]\n{parsed_clean}\n"
            else:
                critiques_text += f"\n[Review {idx}] (unstructured)\n{review.get('critique', '')}\n"

        # 3. Construct Prompt
        full_prompt = f"""
        USER QUESTION: {question}

        {proposals_text}

        {critiques_text}

        Based on the above proposals and rigorous peer critiques, formulate the final answer.
        """

        # 4. Run Chairman
        config = AgentConfig(
            name="CouncilChairman",
            instructions=cls.CHAIRMAN_INSTRUCTIONS,
            reasoning_effort=ReasoningEffort.HIGH,
            verbosity=Verbosity.HIGH, # Comprehensive output
            enable_web_search=False # Pure synthesis
        )
        
        agent = AgentBuilder.create(config)
        
        print("👑 The Chairman is synthesizing the final verdict...")
        final_response, _, tools_used = await run_agent(
            agent, full_prompt, verbose=False,
            logger=logger, stage="chairman",
            return_full=True
        )
        
        return final_response

