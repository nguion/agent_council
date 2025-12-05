"""
Council Reviewer Module.
Handles peer review and critique among council members.
"""

import asyncio
import json
from typing import Dict, Any, List, Callable
from .agent_config import AgentConfig, ReasoningEffort
from .agent_builder import AgentBuilder
from .agent_runner import run_agent

class CouncilReviewer:
    """Manages the peer review process."""

    @staticmethod
    async def review_others(
        reviewer_config: Dict[str, Any], 
        question: str, 
        other_responses: List[Dict[str, Any]],
        progress_callback: Callable[[str, str], None] = None,
        logger=None
    ) -> Dict[str, Any]:
        """
        A single agent reviews the anonymous responses of others.
        """
        reviewer_name = reviewer_config.get('name', 'Unknown')
        if progress_callback:
            progress_callback(reviewer_name, "Reviewing...")

        try:
            persona = reviewer_config.get('persona', 'Reviewer')
            
            # Prepare anonymous input with stable proposal IDs (from execution phase)
            others_text = ""
            for res in other_responses:
                pid = res.get('proposal_id', 0)
                others_text += f"\n\n--- PROPOSAL #{pid} ---\n{res['response']}\n"

            prompt = f"""
            ORIGINAL QUESTION: {question}

            YOUR PERSONA: {persona}

            TASK: 
            You have received {len(other_responses)} proposals from other anonymous council members. 
            Review them critically based strictly on YOUR persona and expertise.

            {others_text}

            OUTPUT INSTRUCTIONS:
            Return ONLY valid JSON (no markdown). Schema:
            {{
              "overall_tldr": "string, max 2 sentences",
              "per_proposal": [
                {{
                  "proposal_id": <int matching the #'s above>,
                  "score": <int 1-5, 5 = best>,
                  "strengths": "string, well-reasoned",
                  "weaknesses": "string, well-reasoned",
                  "gaps_risks": "string, well-reasoned",
                  "tldr": "1-2 sentence summary of your critique"
                }},
                ...
              ],
              "overall_ranking": [<proposal_id best to worst>]
            }}

            RULES:
            - JSON only. No extra text.
            - Ensure strengths/weaknesses/gaps are well thought-out
            - Ranking must reference the proposal_id values above.
            """
            
            # Build reviewer agent
            effort_str = reviewer_config.get('reasoning_effort', 'medium').lower()
            effort = ReasoningEffort.MEDIUM
            if effort_str == 'high':
                effort = ReasoningEffort.HIGH
            elif effort_str == 'low':
                effort = ReasoningEffort.LOW
            elif effort_str == 'none':
                effort = ReasoningEffort.NONE
            
            config = AgentConfig(
                name=f"Reviewer-{reviewer_name}",
                instructions=f"You are {reviewer_name}. {persona}",
                reasoning_effort=effort,
                verbosity='low', # concise critique
                enable_web_search=reviewer_config.get('enable_web_search', False),
                enable_file_search=reviewer_config.get('enable_file_search', False),
                file_search_vector_store_ids=reviewer_config.get('file_search_vector_store_ids', []),
                enable_shell=reviewer_config.get('enable_shell', False),
                enable_code_interpreter=reviewer_config.get('enable_code_interpreter', False),
                custom_tools=reviewer_config.get('custom_tools', []),
            )
            agent = AgentBuilder.create(config)
            
            critique, usage_data, tools_used = await run_agent(
                agent, prompt, verbose=False,
                logger=logger, stage=f"peer_review:{reviewer_name}",
                return_full=True
            )
            
            if progress_callback:
                progress_callback(reviewer_name, "Critique Complete")

            # Parse JSON output
            parsed = None
            tldr = "No TLDR provided."
            try:
                parsed = json.loads(critique)
                tldr = parsed.get("overall_tldr", tldr)
            except Exception:
                # fall back to TLDR extraction from text if misformatted
                if "TLDR:" in critique:
                    parts = critique.split("TLDR:", 1)[1]
                    tldr = parts.split("\n\n", 1)[0].strip()
                elif "**TLDR:**" in critique:
                    parts = critique.split("**TLDR:**", 1)[1]
                    tldr = parts.split("\n\n", 1)[0].strip()

            return {
                "reviewer": reviewer_name,
                "critique": critique,
                "tldr": tldr,
                "parsed": parsed,
                "tools_used": tools_used or []
            }

        except Exception as e:
            if progress_callback:
                progress_callback(reviewer_name, "Review Failed")
            return {"reviewer": reviewer_config.get('name'), "error": str(e)}

    @classmethod
    async def run_peer_review(
        cls, 
        council_config: Dict[str, Any], 
        question: str, 
        execution_results: List[Dict[str, Any]],
        progress_callback: Callable[[str, str], None] = None,
        logger=None
    ) -> List[Dict[str, Any]]:
        """
        Orchestrates parallel peer reviews.
        """
        tasks = []
        task_reviewers = []
        agents_map = {a['name']: a for a in council_config.get('agents', [])}
        
        for result in execution_results:
            agent_name = result['agent_name']
            agent_conf = agents_map.get(agent_name)
            
            if not agent_conf: 
                continue

            # Filter out their own response
            others = [r for r in execution_results if r['agent_name'] != agent_name]
            
            if others:
                if progress_callback:
                    other_names = ", ".join([o['agent_name'] for o in others])
                    progress_callback(agent_name, f"Will review: {other_names}")
                tasks.append(cls.review_others(agent_conf, question, others, progress_callback, logger))
                task_reviewers.append(agent_name)
        
        raw_reviews = await asyncio.gather(*tasks, return_exceptions=True)
        reviews = []
        for idx, r in enumerate(raw_reviews):
            if isinstance(r, Exception):
                reviewer_name = task_reviewers[idx] if idx < len(task_reviewers) else f"Reviewer-{idx+1}"
                reviews.append({"reviewer": reviewer_name, "error": str(r)})
            else:
                reviews.append(r)
        return reviews
