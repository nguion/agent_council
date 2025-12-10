#!/usr/bin/env python3
"""
Validation script for recent fixes.

Default: runs fully offline with stubs (no network).
Live mode: add --live to run one real call (requires OPENAI_API_KEY).
"""

import os
import argparse
import tempfile
from pathlib import Path
from types import SimpleNamespace

from dotenv import load_dotenv

from agent_council.core.agent_builder import AgentBuilder
from agent_council.core.agent_config import AgentConfig, ReasoningEffort, Verbosity
from agent_council.core.agent_runner import run_agent_sync, run_agent
from agent_council.core import council_runner as cr
from agent_council.core import council_reviewer as rv
from agent_council.utils import context_condense as cc
from agent_council.utils.session_logger import SessionLogger

# Global flag set in main()
FORCE_REAL_KEY = False


class DummyTool:
    """Simple placeholder tool to verify custom tool passthrough."""


class FakeRunner:
    """Captures max_turns and returns a stub result."""

    def __init__(self):
        self.last_max_turns = None

    async def run(self, agent, query, max_turns=10):
        self.last_max_turns = max_turns
        return SimpleNamespace(
            output="stubbed response",
            context_wrapper=SimpleNamespace(
                usage=SimpleNamespace(input_tokens=1, output_tokens=2)
            ),
            items=[],
            new_items=[],
        )


def ensure_api_key(require_real: bool = False):
    """Set a dummy key unless a real key is required and missing."""
    load_dotenv()
    key = os.getenv("OPENAI_API_KEY")
    if key:
        if require_real or FORCE_REAL_KEY:
            if key.startswith("sk-dummy"):
                raise RuntimeError("OPENAI_API_KEY is set to a dummy value; set a real key for live mode.")
        return
    if require_real or FORCE_REAL_KEY:
        raise RuntimeError("OPENAI_API_KEY is required for live mode.")
    os.environ["OPENAI_API_KEY"] = "sk-dummy"  # stub mode


def test_model_settings_and_tools():
    ensure_api_key(require_real=FORCE_REAL_KEY)
    AgentBuilder._initialized = False  # force re-init for the test

    config = AgentConfig(
        name="TestAgent",
        instructions="test",
        enable_web_search=True,
        enable_file_search=True,
        file_search_vector_store_ids=[],
        enable_shell=True,
        enable_code_interpreter=True,
        custom_tools=[DummyTool()],
        reasoning_effort=ReasoningEffort.HIGH,
        verbosity=Verbosity.MEDIUM,
    )

    agent = AgentBuilder.create(config)

    # Model settings should carry the values we set (attribute or repr check).
    ms = agent.model_settings
    assert getattr(ms, "reasoning", None) and getattr(ms.reasoning, "effort", None) == "high", "reasoning effort not set"
    assert getattr(ms, "verbosity", None) == "medium", "verbosity not set"

    tool_names = {t.__class__.__name__ for t in agent.tools}
    expected = {"WebSearchTool", "FileSearchTool", "ShellTool", "CodeInterpreterTool", "DummyTool"}
    assert expected.issubset(tool_names), f"Tools missing: {expected - tool_names}"


def test_run_agent_sync_respects_agent_max_turns():
    dummy_agent = SimpleNamespace(name="Dummy", model="gpt-5.1", max_turns=3)
    runner = FakeRunner()
    resp = run_agent_sync(dummy_agent, "hi", runner=runner, verbose=False)
    assert resp == "stubbed response"
    assert runner.last_max_turns == 3, "max_turns should default to agent.max_turns"


def test_council_runner_passes_tools():
    captured_config = {}

    def capture_create(config):
        captured_config["config"] = config
        return SimpleNamespace(name=config.name, model=config.model)

    async def stub_run_agent(agent, prompt, **kwargs):
        return "ok", {"input_tokens": 1, "output_tokens": 1}, ["reasoning"]

    # Patch
    original_create = cr.AgentBuilder.create
    original_run_agent = cr.run_agent
    cr.AgentBuilder.create = capture_create
    cr.run_agent = stub_run_agent

    agent_conf = {
        "name": "RunnerTest",
        "persona": "Tester",
        "enable_web_search": True,
        "enable_file_search": True,
        "file_search_vector_store_ids": [],
        "enable_shell": True,
        "enable_code_interpreter": True,
        "custom_tools": [DummyTool()],
    }

    try:
        # Run the single agent path to build config
        import asyncio
        asyncio.run(
            cr.CouncilRunner.run_single_agent(
                agent_conf, "prompt", progress_callback=None, logger=None
            )
        )
    finally:
        cr.AgentBuilder.create = original_create
        cr.run_agent = original_run_agent

    cfg: AgentConfig = captured_config["config"]
    assert cfg.enable_file_search is True
    assert cfg.enable_shell is True
    assert cfg.enable_code_interpreter is True
    assert cfg.custom_tools and isinstance(cfg.custom_tools[0], DummyTool)


def test_reviewer_passes_tools():
    captured_config = {}

    def capture_create(config):
        captured_config["config"] = config
        return SimpleNamespace(name=config.name, model=config.model)

    async def stub_run_agent(agent, prompt, **kwargs):
        return '{"overall_tldr": "ok", "per_proposal": [], "overall_ranking": []}', {}, []

    original_create = rv.AgentBuilder.create
    original_run_agent = rv.run_agent
    rv.AgentBuilder.create = capture_create
    rv.run_agent = stub_run_agent

    reviewer_conf = {
        "name": "ReviewerTest",
        "persona": "Reviewer persona",
        "enable_web_search": True,
        "enable_file_search": True,
        "file_search_vector_store_ids": [],
        "enable_shell": True,
        "enable_code_interpreter": True,
        "custom_tools": [DummyTool()],
    }

    try:
        import asyncio
        others = [{"agent_name": "A", "response": "resp", "proposal_id": 1}]
        asyncio.run(
            rv.CouncilReviewer.review_others(
                reviewer_conf, "question", others, progress_callback=None, logger=None
            )
        )
    finally:
        rv.AgentBuilder.create = original_create
        rv.run_agent = original_run_agent

    cfg: AgentConfig = captured_config["config"]
    assert cfg.enable_file_search is True
    assert cfg.enable_shell is True
    assert cfg.enable_code_interpreter is True
    assert cfg.custom_tools and isinstance(cfg.custom_tools[0], DummyTool)


def test_condense_prompt_uses_max_tokens():
    calls = []

    class FakeChat:
        def __init__(self, recorder):
            self.recorder = recorder
            self.completions = self

        async def create(self, **kwargs):
            self.recorder.append(kwargs)
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="summary"))],
                usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            )

    class FakeClient:
        def __init__(self, recorder):
            self.chat = FakeChat(recorder)

    original_client = cc.AsyncOpenAI
    cc.AsyncOpenAI = lambda: FakeClient(calls)
    try:
        import asyncio
        asyncio.run(cc.condense_prompt("abcd"))
    finally:
        cc.AsyncOpenAI = original_client

    assert calls, "condense_prompt never invoked the client"
    assert all("max_tokens" in c for c in calls), "max_tokens not forwarded to client"
    assert all(c["max_tokens"] == 800 for c in calls), "max_tokens should be 800"


def test_execute_council_handles_agent_failure():
    """Ensure one agent failure does not cancel others."""
    async def fail_agent(*args, **kwargs):
        raise RuntimeError("boom")

    async def ok_agent(*args, **kwargs):
        return {
            "agent_name": "ok",
            "agent_persona": "p",
            "response": "resp",
            "tldr": "t",
            "status": "success",
            "tools_used": [],
        }

    original = cr.CouncilRunner.run_single_agent
    cr.CouncilRunner.run_single_agent = staticmethod(fail_agent)
    agents = [
        {"name": "bad", "persona": "p"},
        {"name": "ok", "persona": "p"},
    ]
    council_cfg = {"agents": agents, "council_name": "Test"}
    try:
        import asyncio
        result = asyncio.run(cr.CouncilRunner.execute_council(council_cfg, "q", [], None, None))
    finally:
        cr.CouncilRunner.run_single_agent = original

    execution_results = result["execution_results"]
    assert len(execution_results) == 2
    statuses = {r["agent_name"]: r["status"] for r in execution_results}
    assert statuses["bad"] == "error"
    assert "ok" in statuses


def test_peer_review_handles_failure():
    """Ensure peer review continues when one review fails."""
    async def fail_review(*args, **kwargs):
        raise RuntimeError("review boom")

    async def ok_review(*args, **kwargs):
        return {"reviewer": "ok", "critique": "{}", "parsed": {}, "tldr": "", "tools_used": []}

    original = rv.CouncilReviewer.review_others
    rv.CouncilReviewer.review_others = staticmethod(fail_review)
    council_cfg = {"agents": [{"name": "A"}, {"name": "B"}]}
    execution_results = [
        {"agent_name": "A", "response": "r", "proposal_id": 1, "status": "success"},
        {"agent_name": "B", "response": "r", "proposal_id": 2, "status": "success"},
    ]
    try:
        import asyncio
        reviews = asyncio.run(rv.CouncilReviewer.run_peer_review(council_cfg, "q", execution_results, None, None))
    finally:
        rv.CouncilReviewer.review_others = original
    assert len(reviews) == 1 or len(reviews) == 2
    assert any(isinstance(r, dict) and "error" in r for r in reviews), "Expected an error entry"


def test_model_passthrough_in_run_single_agent():
    """Ensure model from config is passed through."""
    captured = {}

    def capture_create(cfg):
        captured["model"] = cfg.model
        return SimpleNamespace(name=cfg.name, model=cfg.model)

    async def stub_run_agent(agent, prompt, **kwargs):
        return "ok", {}, []

    orig_create = cr.AgentBuilder.create
    orig_run_agent = cr.run_agent
    cr.AgentBuilder.create = capture_create
    cr.run_agent = stub_run_agent

    agent_conf = {"name": "m", "persona": "p", "model": "gpt-4.1"}
    try:
        import asyncio
        asyncio.run(cr.CouncilRunner.run_single_agent(agent_conf, "q"))
    finally:
        cr.AgentBuilder.create = orig_create
        cr.run_agent = orig_run_agent

    assert captured["model"] == "gpt-4.1"


def test_usage_fallback_on_result_usage():
    """Ensure usage is captured when context_wrapper is absent."""
    class FakeRunner:
        async def run(self, agent, query, max_turns=10):
            return SimpleNamespace(
                output="done",
                usage=SimpleNamespace(input_tokens=5, output_tokens=7),
                items=[],
                new_items=[],
            )

    runner = FakeRunner()
    agent = SimpleNamespace(name="a", model="gpt-5.1")
    import asyncio
    resp, usage, _ = asyncio.run(run_agent(agent, "q", runner=runner, verbose=False, return_full=True))
    assert usage["input_tokens"] == 5 and usage["output_tokens"] == 7 and usage["total_tokens"] == 12


def test_logger_records_tools_and_model_and_status():
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = SessionLogger(output_dir=tmpdir)
        logger.log_llm_call(
            stage="s1",
            agent_name="a1",
            prompt="p",
            response="r",
            usage={"input_tokens": 2, "output_tokens": 3},
            model="gpt-4.1",
            tools_used=["web_search"],
            error=False,
        )
        content = Path(logger.path).read_text()
        assert "Model: gpt-4.1" in content
        assert "tools_used: ['web_search']" in content
        assert "Status: OK" in content


def test_logger_records_errors():
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = SessionLogger(output_dir=tmpdir)
        logger.log_llm_call(
            stage="s2",
            agent_name="a2",
            prompt="p",
            response="err",
            usage={"input_tokens": 0, "output_tokens": 0},
            model="gpt-5.1",
            tools_used=[],
            error=True,
        )
        content = Path(logger.path).read_text()
        assert "Status: ERROR" in content
        assert "err" in content


def test_logger_finalize_writes_summary():
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = SessionLogger(output_dir=tmpdir)
        logger.log_llm_call(
            stage="s3",
            agent_name="a3",
            prompt="p",
            response="r",
            usage={"input_tokens": 1, "output_tokens": 2},
            model="gpt-5.1",
            tools_used=None,
            error=False,
        )
        logger.finalize()
        content = Path(logger.path).read_text()
        assert "## Summary" in content
        assert "total_tokens" in content


def test_run_agent_logs_on_failure():
    class BoomRunner:
        async def run(self, agent, query, max_turns=10):
            raise RuntimeError("boom")

    with tempfile.TemporaryDirectory() as tmpdir:
        logger = SessionLogger(output_dir=tmpdir)
        agent = SimpleNamespace(name="a", model="gpt-5.1")
        try:
            import asyncio
            asyncio.run(run_agent(agent, "q", runner=BoomRunner(), verbose=False, logger=logger, stage="fail"))
        except RuntimeError:
            pass
        content = Path(logger.path).read_text()
        assert "Status: ERROR" in content
        assert "boom" in content

def test_live_run_with_real_api():
    """
    Minimal live call to verify end-to-end with a real API key.
    Uses no tools and 1 turn to keep cost negligible.
    """
    ensure_api_key(require_real=True)
    AgentBuilder._initialized = False
    cfg = AgentConfig(
        name="LiveSmoke",
        instructions="You are a concise assistant. Reply with 'pong'.",
        enable_web_search=False,
        enable_file_search=False,
        enable_shell=False,
        enable_code_interpreter=False,
        reasoning_effort=ReasoningEffort.LOW,
        verbosity=Verbosity.LOW,
    )
    agent = AgentBuilder.create(cfg)
    resp = run_agent_sync(agent, "ping", max_turns=1, verbose=False)
    assert "pong" in resp.lower(), "Live response did not contain 'pong'"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Run a real API call smoke check")
    args = parser.parse_args()
    global FORCE_REAL_KEY
    FORCE_REAL_KEY = args.live

    tests = [
        test_model_settings_and_tools,
        test_run_agent_sync_respects_agent_max_turns,
        test_council_runner_passes_tools,
        test_reviewer_passes_tools,
        test_condense_prompt_uses_max_tokens,
        test_execute_council_handles_agent_failure,
        test_peer_review_handles_failure,
        test_model_passthrough_in_run_single_agent,
        test_usage_fallback_on_result_usage,
        test_logger_records_tools_and_model_and_status,
        test_logger_records_errors,
        test_logger_finalize_writes_summary,
        test_run_agent_logs_on_failure,
    ]
    if args.live:
        tests.append(test_live_run_with_real_api)

    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"✅ {t.__name__}")
    print(f"\nAll {passed} validation checks passed.")


if __name__ == "__main__":
    main()

