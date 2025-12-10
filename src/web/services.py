"""
Service Layer Module.
Wraps core Agent Council functionality for use in web API without CLI dependencies.
"""

import asyncio
from typing import Dict, Any, List, Callable, Optional
from agent_council.utils.file_ingestion import FileIngestor
from agent_council.utils.session_logger import SessionLogger
from agent_council.core.council_builder import CouncilBuilder
from agent_council.core.council_runner import CouncilRunner
from agent_council.core.council_reviewer import CouncilReviewer
from agent_council.core.council_chairman import CouncilChairman


class AgentCouncilService:
    """Service layer for Agent Council operations."""
    
    @staticmethod
    def ingest_files(file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Ingest context files.
        
        Args:
            file_paths: List of file paths to ingest
            
        Returns:
            List of ingested data with metadata and content
        """
        return FileIngestor.ingest_paths(file_paths)
    
    @staticmethod
    async def build_council(
        question: str,
        ingested_data: List[Dict[str, Any]],
        logger: Optional[SessionLogger] = None
    ) -> Dict[str, Any]:
        """
        Build a council configuration using the Architect agent.
        
        Args:
            question: The user's question/problem
            ingested_data: List of ingested context files
            logger: Optional session logger
            
        Returns:
            Council configuration dict
        """
        return await CouncilBuilder.build_council(question, ingested_data, logger=logger)
    
    @staticmethod
    async def execute_council(
        council_config: Dict[str, Any],
        question: str,
        ingested_data: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[str, str], None]] = None,
        logger: Optional[SessionLogger] = None
    ) -> Dict[str, Any]:
        """
        Execute all agents in the council in parallel.
        
        Args:
            council_config: Council configuration
            question: The user's question
            ingested_data: List of ingested context files
            progress_callback: Optional callback for progress updates
            logger: Optional session logger
            
        Returns:
            Execution results dict
        """
        return await CouncilRunner.execute_council(
            council_config,
            question,
            ingested_data,
            progress_callback=progress_callback,
            logger=logger
        )
    
    @staticmethod
    async def run_peer_review(
        council_config: Dict[str, Any],
        question: str,
        execution_results: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[str, str], None]] = None,
        logger: Optional[SessionLogger] = None
    ) -> List[Dict[str, Any]]:
        """
        Run peer review process.
        
        Args:
            council_config: Council configuration
            question: The user's question
            execution_results: Results from council execution
            progress_callback: Optional callback for progress updates
            logger: Optional session logger
            
        Returns:
            List of peer review results
        """
        return await CouncilReviewer.run_peer_review(
            council_config,
            question,
            execution_results,
            progress_callback=progress_callback,
            logger=logger
        )
    
    @staticmethod
    async def synthesize_verdict(
        question: str,
        execution_results: List[Dict[str, Any]],
        peer_reviews: List[Dict[str, Any]],
        logger: Optional[SessionLogger] = None
    ) -> str:
        """
        Generate Chairman's final verdict.
        
        Args:
            question: The user's question
            execution_results: Results from council execution
            peer_reviews: Results from peer review
            logger: Optional session logger
            
        Returns:
            Final verdict as string
        """
        return await CouncilChairman.synthesize(
            question,
            execution_results,
            peer_reviews,
            logger=logger
        )
    
    @staticmethod
    def aggregate_reviews(
        execution_results: List[Dict[str, Any]],
        reviews: List[Dict[str, Any]]
    ) -> Dict[int, Dict[str, Any]]:
        """
        Aggregate structured peer-review scores by proposal_id.
        
        Args:
            execution_results: Results from council execution
            reviews: Results from peer review
            
        Returns:
            Aggregated scores dict keyed by proposal_id
        """
        agg = {}
        for res in execution_results:
            pid = res.get("proposal_id")
            if pid is not None:
                agg[pid] = {"scores": [], "comments": []}
        
        for rev in reviews:
            parsed = rev.get("parsed")
            if not parsed:
                continue
            per = parsed.get("per_proposal", [])
            for item in per:
                pid = item.get("proposal_id")
                if pid in agg:
                    score = item.get("score")
                    if isinstance(score, (int, float)):
                        agg[pid]["scores"].append(score)
                    agg[pid]["comments"].append(item.get("tldr") or "")
        
        return agg
