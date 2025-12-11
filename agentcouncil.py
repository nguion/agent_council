#!/usr/bin/env python3
"""
Agent Council Utility

- `python agentcouncil.py start` : Full startup (venv, deps, Postgres container, backend, frontend)
- `python agentcouncil.py stop`  : Teardown (backend, frontend, Postgres container)
- `python agentcouncil.py cli`   : Original interactive CLI flow
"""

import asyncio
import json
import os
import platform
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from agent_council.utils.file_ingestion import FileIngestor
from agent_council.utils.session_logger import SessionLogger
from agent_council.core.council_builder import CouncilBuilder
from agent_council.core.council_editor import CouncilEditor
from agent_council.core.council_runner import CouncilRunner
from agent_council.core.council_reviewer import CouncilReviewer
from agent_council.core.council_chairman import CouncilChairman

# ---------------------------------------------------------------------------
# Paths / constants
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
LOG_DIR = ROOT / ".agentcouncil"
RUNTIME_FILE = LOG_DIR / "runtime.json"
BACKEND_LOG = LOG_DIR / "backend.log"
FRONTEND_LOG = LOG_DIR / "frontend.log"
DEFAULT_DB_URL = "postgresql+asyncpg://postgres:agentpwd@localhost:5432/agent_council"
PG_CONTAINER = "agent-council-pg"

console = Console()


# ---------------------------------------------------------------------------
# Helper utilities for start/stop
# ---------------------------------------------------------------------------
def _run(cmd, cwd=None, env=None, check=True):
    console.log(f"[cyan]$ {' '.join(cmd)}[/cyan]" + (f" (cwd={cwd})" if cwd else ""))
    result = subprocess.run(cmd, cwd=cwd, env=env, text=True, capture_output=True)
    if result.stdout:
        console.log(result.stdout.rstrip())
    if result.stderr:
        console.log(f"[red]{result.stderr.rstrip()}[/red]")
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)} (rc={result.returncode})")
    return result


def _which(name: str) -> Optional[str]:
    return shutil.which(name)


def ensure_python():
    if sys.version_info < (3, 10):
        raise RuntimeError("Python 3.10+ is required.")


def ensure_venv():
    if not VENV.exists():
        console.log("[yellow]Creating virtual environment (.venv)...[/yellow]")
        _run([sys.executable, "-m", "venv", str(VENV)])
    else:
        console.log("[green].venv already exists[/green]")


def _venv_python() -> str:
    if platform.system().lower().startswith("win"):
        return str(VENV / "Scripts" / "python.exe")
    return str(VENV / "bin" / "python")


def install_python_deps():
    py = _venv_python()
    console.log("[yellow]Installing Python dependencies...[/yellow]")
    _run([py, "-m", "pip", "install", "--upgrade", "pip"])
    _run([py, "-m", "pip", "install", "-r", "requirements.txt"])
    _run([py, "-m", "pip", "install", "-r", "requirements-web.txt"])


def ensure_node():
    if not _which("npm"):
        console.log("[red]npm not found; frontend will be skipped.[/red]")
        return False
    node_modules = ROOT / "web-ui" / "node_modules"
    if not node_modules.exists():
        console.log("[yellow]Installing web-ui dependencies (npm install)...[/yellow]")
        _run(["npm", "install"], cwd=str(ROOT / "web-ui"))
    else:
        console.log("[green]web-ui node_modules present[/green]")
    return True


def ensure_docker():
    if not _which("docker"):
        console.log("[red]Docker not available. Postgres container cannot be managed.[/red]")
        return False
    return True


def start_postgres_container() -> Optional[str]:
    if not ensure_docker():
        return None
    result = subprocess.run(
        ["docker", "ps", "-a", "-q", "-f", f"name={PG_CONTAINER}"], capture_output=True, text=True
    )
    cid = result.stdout.strip()
    if cid:
        console.log(f"[green]Postgres container already exists ({PG_CONTAINER}); starting...[/green]")
        _run(["docker", "start", PG_CONTAINER])
        return cid
    console.log("[yellow]Starting new Postgres container (postgres:16)...[/yellow]")
    _run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            PG_CONTAINER,
            "-e",
            "POSTGRES_PASSWORD=agentpwd",
            "-e",
            "POSTGRES_DB=agent_council",
            "-p",
            "5432:5432",
            "postgres:16",
        ]
    )
    cid = (
        subprocess.run(
            ["docker", "ps", "-q", "-f", f"name={PG_CONTAINER}"], capture_output=True, text=True
        ).stdout.strip()
    )
    return cid or PG_CONTAINER


def _launch_process(cmd, cwd, log_path, env: Dict[str, Any]):
    LOG_DIR.mkdir(exist_ok=True)
    log_file = open(log_path, "w", encoding="utf-8")
    kwargs = {"cwd": cwd, "env": env, "stdout": log_file, "stderr": log_file}
    if platform.system().lower().startswith("win"):
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore
    else:
        kwargs["start_new_session"] = True
    proc = subprocess.Popen(cmd, **kwargs)
    console.log(f"[green]Started {' '.join(cmd)} (pid={proc.pid})[/green]")
    return proc.pid


def start_backend(database_url: str) -> int:
    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    py = _venv_python()
    cmd = [py, "-m", "uvicorn", "src.web.api:app", "--host", "0.0.0.0", "--port", "8000"]
    return _launch_process(cmd, str(ROOT), str(BACKEND_LOG), env)


def start_frontend() -> Optional[int]:
    if not ensure_node():
        return None
    env = os.environ.copy()
    env.setdefault("VITE_API_URL", "http://localhost:8000")
    cmd = ["npm", "run", "dev", "--", "--host", "--port", "5173"]
    return _launch_process(cmd, str(ROOT / "web-ui"), str(FRONTEND_LOG), env)


def stop_process(pid: int):
    if pid <= 0:
        return
    try:
        if platform.system().lower().startswith("win"):
            os.kill(pid, signal.CTRL_BREAK_EVENT)
        else:
            os.killpg(pid, signal.SIGTERM)
    except Exception:
        try:
            os.kill(pid, signal.SIGTERM)
        except Exception:
            pass


def stop_container():
    if not ensure_docker():
        return
    subprocess.run(["docker", "stop", PG_CONTAINER], capture_output=True)


def load_runtime() -> Dict[str, Any]:
    if not RUNTIME_FILE.exists():
        return {}
    try:
        return json.loads(RUNTIME_FILE.read_text())
    except Exception:
        return {}


def save_runtime(data: Dict[str, Any]):
    LOG_DIR.mkdir(exist_ok=True)
    RUNTIME_FILE.write_text(json.dumps(data, indent=2))


def start_stack():
    ensure_python()
    ensure_venv()
    install_python_deps()

    backend_pid = None
    frontend_pid = None

    cid = start_postgres_container()
    env_db = os.getenv("DATABASE_URL")

    if cid:
        db_url = DEFAULT_DB_URL
        console.print(
            Panel(
                f"Using Postgres container '{PG_CONTAINER}' at {db_url}",
                border_style="green",
                title="Postgres (container)",
            )
        )
        db_mode = "container"
    else:
        # No container; honor external DATABASE_URL if provided
        if env_db:
            db_url = env_db
            if db_url.startswith("postgres"):
                console.print(
                    Panel(
                        f"Using external DATABASE_URL={db_url}",
                        border_style="yellow",
                        title="Postgres (external)",
                    )
                )
                db_mode = "external"
            else:
                db_url = env_db
                db_mode = "fallback"
                console.print(
                    Panel(
                        f"[red]CODE RED[/red]: Postgres container not available and DATABASE_URL is non-Postgres ({db_url}). "
                        "This is a fallback. Install/start Docker or point DATABASE_URL to Postgres.",
                        border_style="red",
                        title="FALLBACK WARNING",
                    )
                )
        else:
            db_url = "sqlite+aiosqlite:///./agent_council.db"
            db_mode = "fallback"
            console.print(
                Panel(
                    "[red]CODE RED[/red]: Docker/Postgres not available and DATABASE_URL not set.\n"
                    "Falling back to SQLite. Install/start Docker or set DATABASE_URL to Postgres to avoid fallback.",
                    border_style="red",
                    title="FALLBACK WARNING",
                )
            )

    backend_pid = start_backend(db_url)
    frontend_pid = start_frontend()

    runtime = {
        "db_container": cid,
        "database_url": db_url,
        "db_mode": db_mode,
        "backend_pid": backend_pid,
        "frontend_pid": frontend_pid,
        "started_at": time.time(),
        "logs": {"backend": str(BACKEND_LOG), "frontend": str(FRONTEND_LOG)},
    }
    save_runtime(runtime)
    console.print(
        Panel.fit(
            f"Backend pid: {backend_pid}\n"
            f"Frontend pid: {frontend_pid or 'not started'}\n"
            f"DB: {db_url}\n"
            f"Logs: {BACKEND_LOG}, {FRONTEND_LOG}",
            title="Agent Council Started",
            border_style="green",
        )
    )


def stop_stack():
    runtime = load_runtime()
    backend_pid = runtime.get("backend_pid")
    frontend_pid = runtime.get("frontend_pid")
    db_container = runtime.get("db_container")

    if backend_pid:
        console.log(f"[yellow]Stopping backend (pid={backend_pid})[/yellow]")
        stop_process(int(backend_pid))
    if frontend_pid:
        console.log(f"[yellow]Stopping frontend (pid={frontend_pid})[/yellow]")
        stop_process(int(frontend_pid))
    if db_container:
        console.log(f"[yellow]Stopping Postgres container ({db_container})[/yellow]")
        stop_container()

    if RUNTIME_FILE.exists():
        RUNTIME_FILE.unlink()
    console.print(Panel("Stopped services and cleaned runtime state.", border_style="red", title="Stopped"))


# ---------------------------------------------------------------------------
# Original interactive CLI flow
# ---------------------------------------------------------------------------
def aggregate_reviews(execution_results, reviews):
    """Aggregate structured peer-review scores by proposal_id."""
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


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def display_header():
    console.print(
        Panel.fit(
            "[bold blue]Agent Council Builder[/bold blue]\n"
            "[italic]1. Input -> 2. Build -> 3. Edit -> 4. Execute -> 5. Synthesize[/italic]",
            border_style="blue",
        )
    )


def build_status_table(status_map, title="Progress"):
    table = Table(title=title, show_lines=False, box=None)
    table.add_column("Agent", style="cyan")
    table.add_column("Status", style="magenta")
    for name, status in status_map.items():
        table.add_row(name, status)
    return table


async def main_async():
    clear_screen()
    display_header()
    logger = SessionLogger()

    console.rule("[bold]Step 1: Input & Context[/bold]")
    question = Prompt.ask(
        "\n[bold]Enter your core question/problem[/bold]",
        default="What are some realistic but novel ideas for Delta Airlines to differentiate in 2026 and increase profits?",
    )

    context_files = []
    console.print("\n[bold]Add Context Files[/bold] (drag & drop paths, enter empty line to finish):")
    while True:
        path = Prompt.ask("File path")
        if not path:
            break
        path = path.strip().replace("'", "").replace('"', "").replace("\\ ", " ")
        if os.path.exists(path):
            context_files.append(path)
            console.print(f"[green]Added: {path}[/green]")
        else:
            console.print(f"[red]File not found: {path}[/red]")

    ingested_data = []
    if context_files:
        with console.status("[bold green]Ingesting context files...[/bold green]"):
            ingested_data = FileIngestor.ingest_paths(context_files)

        table = Table(title="Ingested Context")
        table.add_column("Filename", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Size", justify="right")
        for item in ingested_data:
            meta = item["metadata"]
            table.add_row(meta["filename"], meta["extension"], f"{meta['size_bytes']} bytes")
        console.print(table)
    else:
        console.print("[yellow]No context files provided. Proceeding with question only.[/yellow]")

    console.print("\n")
    console.rule("[bold]Step 2: Building the Council[/bold]")

    if not Confirm.ask("Ready to generate the Council?"):
        return

    with console.status("[bold purple]Consulting the Architect... (Calling GPT-5.1)[/bold purple]"):
        council_config = await CouncilBuilder.build_council(question, ingested_data, logger=logger)

    if "error" in council_config:
        console.print(Panel(f"[red]Error generating council:[/red]\n{council_config['error']}", title="Failure"))
        return

    console.print(f"\n[bold green]Council Generated:[/bold green] {council_config.get('council_name', 'Unnamed')}")
    console.print(f"[italic]{len(council_config.get('agents', []))} agents proposed.[/italic]")
    Prompt.ask("\nPress Enter to review and edit...")

    council_config = CouncilEditor.run_editor(council_config)

    clear_screen()
    display_header()
    console.rule("[bold]Step 4: Council Execution[/bold]")

    agents = council_config.get("agents", [])
    console.print(f"\n[bold]Ready to launch {len(agents)} agents in parallel.[/bold]")

    if not Confirm.ask("Start Execution?"):
        return

    exec_status = {a.get("name", "Unknown"): "Queued" for a in agents}
    final_results: Dict[str, Any] = {}
    with Live(build_status_table(exec_status, "Execution Progress"), refresh_per_second=8, console=console) as live:
        def exec_callback(name: str, status: str):
            exec_status[name] = status
            live.update(build_status_table(exec_status, "Execution Progress"))

        final_results = await CouncilRunner.execute_council(
            council_config, question, ingested_data, progress_callback=exec_callback, logger=logger
        )

    if "error" in final_results:
        console.print(Panel(f"[red]Execution failed:[/red]\n{final_results['error']}", title="Failure"))
        return
    execution_results = final_results.get("execution_results", [])
    if not execution_results:
        console.print(Panel("[red]No execution results produced.[/red]", title="Failure"))
        return
    console.print("\n[bold]Step 4 Results (TLDRs):[/bold]")
    for res in execution_results:
        status_color = "green" if res["status"] == "success" else "red"
        persona_preview = res.get("agent_persona", "")[:50] + "..."
        title = f"[{status_color}]{res['agent_name']} (Persona: {persona_preview})[/{status_color}]"
        preview = res.get("tldr", res["response"])[:400]
        console.print(Panel(preview, title=title, border_style=status_color))

    console.print("\n")
    console.rule("[bold]Step 5: Peer Review & Final Synthesis[/bold]")

    if not Confirm.ask("Proceed to Peer Review & Final Synthesis?"):
        return

    reviews = []
    peer_status = {r["agent_name"]: "Pending" for r in execution_results}
    with Live(build_status_table(peer_status, "Peer Review Progress"), refresh_per_second=8, console=console) as live:
        def review_callback(name: str, status: str):
            peer_status[name] = status
            live.update(build_status_table(peer_status, "Peer Review Progress"))

        reviews = await CouncilReviewer.run_peer_review(
            council_config, question, execution_results, progress_callback=review_callback, logger=logger
        )

    console.print(f"[green]✓ Peer reviews completed ({len(reviews)} critiques generated)[/green]")
    agg = aggregate_reviews(execution_results, reviews)
    console.print("\n[bold]Peer Review Scores (by Proposal):[/bold]")
    score_table = Table(show_lines=False, box=None)
    score_table.add_column("Proposal #", style="cyan", justify="right")
    score_table.add_column("Avg Score", style="magenta", justify="right")
    score_table.add_column("Count", style="green", justify="right")
    score_table.add_column("Sample Comment", style="dim")
    for res in execution_results:
        pid = res.get("proposal_id")
        scores = agg.get(pid, {}).get("scores", [])
        comments = [c for c in agg.get(pid, {}).get("comments", []) if c]
        avg = sum(scores) / len(scores) if scores else 0
        sample = (
            comments[0][:120] + ("..." if comments and len(comments[0]) > 120 else "") if comments else ""
        )
        score_table.add_row(str(pid), f"{avg:.2f}" if scores else "—", str(len(scores)), sample)
    console.print(score_table)

    final_verdict = ""
    with console.status("[bold gold1]The Chairman is synthesizing the final verdict...[/bold gold1]"):
        final_verdict = await CouncilChairman.synthesize(question, execution_results, reviews, logger=logger)

    clear_screen()
    display_header()
    console.rule("[bold gold1]THE CHAIRMAN'S VERDICT[/bold gold1]")
    console.print(Panel(final_verdict, title="Final Answer", border_style="gold1"))

    final_results["peer_reviews"] = reviews
    final_results["chairman_verdict"] = final_verdict
    cost_breakdown = logger.get_cost_breakdown()
    final_results["tokens"] = {
        "input_tokens": logger.total_input_tokens,
        "output_tokens": logger.total_output_tokens,
        "total_tokens": logger.total_input_tokens + logger.total_output_tokens,
        "total_cost_usd": cost_breakdown["total_cost_usd"],
        "log_file": logger.path,
    }

    output_file = "council_session_complete.json"
    with open(output_file, "w") as f:
        json.dump(final_results, f, indent=2)

    logger.finalize()
    console.print(f"\n[bold]Complete session results saved to:[/bold] [cyan]{output_file}[/cyan]")
    console.print(f"[bold]LLM token usage:[/bold] {logger.summary()}")
    console.print(f"[dim]Full log: {logger.path}[/dim]")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Agent Council utility")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("start", help="Start backend, frontend, and Postgres (if available)")
    sub.add_parser("stop", help="Stop services and Postgres container")
    sub.add_parser("cli", help="Run interactive CLI (original flow)")

    args = parser.parse_args()
    if args.command == "start":
        start_stack()
    elif args.command == "stop":
        stop_stack()
    else:
        asyncio.run(main_async())


if __name__ == "__main__":
    main()
