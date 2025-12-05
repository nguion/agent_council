#!/usr/bin/env python3
"""
Full Agent Council Flow.
Step 1: Input & Context
Step 2: Council Generation
Step 3: Interactive Editing
Step 4: Parallel Execution
Step 5: Peer Review & Final Synthesis
"""

import os
import sys
import json
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner

from agent_council.utils.file_ingestion import FileIngestor
from agent_council.utils.session_logger import SessionLogger
from agent_council.core.council_builder import CouncilBuilder
from agent_council.core.council_editor import CouncilEditor
from agent_council.core.council_runner import CouncilRunner
from agent_council.core.council_reviewer import CouncilReviewer
from agent_council.core.council_chairman import CouncilChairman
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

console = Console()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def display_header():
    console.print(Panel.fit(
        "[bold blue]Agent Council Builder[/bold blue]\n"
        "[italic]1. Input -> 2. Build -> 3. Edit -> 4. Execute -> 5. Synthesize[/italic]",
        border_style="blue"
    ))


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

    # --- STEP 1: Input & Context ---
    console.rule("[bold]Step 1: Input & Context[/bold]")
    
    question = Prompt.ask("\n[bold]Enter your core question/problem[/bold]", 
                         default="What are some realistic but novel ideas for Delta Airlines to differentiate in 2026 and increase profits?")
    
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
            meta = item['metadata']
            table.add_row(meta['filename'], meta['extension'], f"{meta['size_bytes']} bytes")
        console.print(table)
    else:
        console.print("[yellow]No context files provided. Proceeding with question only.[/yellow]")

    # --- STEP 2: Council Builder ---
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

    # --- STEP 3: Council Editor ---
    council_config = CouncilEditor.run_editor(council_config)

    # --- STEP 4: Execution ---
    clear_screen()
    display_header()
    console.rule("[bold]Step 4: Council Execution[/bold]")
    
    agents = council_config.get('agents', [])
    console.print(f"\n[bold]Ready to launch {len(agents)} agents in parallel.[/bold]")
    
    if not Confirm.ask("Start Execution?"):
        return

    # Progress dashboard for execution
    exec_status = {a.get('name', 'Unknown'): "Queued" for a in agents}
    final_results = {}
    with Live(build_status_table(exec_status, "Execution Progress"), refresh_per_second=8, console=console) as live:
        def exec_callback(name: str, status: str):
            # Ensure every status key is present
            if name not in exec_status:
                exec_status[name] = status
            else:
                exec_status[name] = status
            live.update(build_status_table(exec_status, "Execution Progress"))

        final_results = await CouncilRunner.execute_council(
            council_config, question, ingested_data, progress_callback=exec_callback, logger=logger
        )

    # Display Individual Results (TLDR only for terminal)
    if "error" in final_results:
        console.print(Panel(f"[red]Execution failed:[/red]\n{final_results['error']}", title="Failure"))
        return
    execution_results = final_results.get('execution_results', [])
    if not execution_results:
        console.print(Panel("[red]No execution results produced.[/red]", title="Failure"))
        return
    console.print("\n[bold]Step 4 Results (TLDRs):[/bold]")
    for res in execution_results:
        status_color = "green" if res['status'] == 'success' else "red"
        persona_preview = res.get('agent_persona', '')[:50] + "..."
        title = f"[{status_color}]{res['agent_name']} (Persona: {persona_preview})[/{status_color}]"
        preview = res.get('tldr', res['response'])[:400]
        console.print(Panel(preview, title=title, border_style=status_color))

    # --- STEP 5: Peer Review & Synthesis ---
    console.print("\n")
    console.rule("[bold]Step 5: Peer Review & Final Synthesis[/bold]")
    
    if not Confirm.ask("Proceed to Peer Review & Final Synthesis?"):
        return

    # 5a. Peer Review
    reviews = []
    peer_status = {r['agent_name']: "Pending" for r in execution_results}
    with Live(build_status_table(peer_status, "Peer Review Progress"), refresh_per_second=8, console=console) as live:
        def review_callback(name: str, status: str):
            if name not in peer_status:
                peer_status[name] = status
            else:
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
        sample = comments[0][:120] + ("..." if comments and len(comments[0]) > 120 else "") if comments else ""
        score_table.add_row(str(pid), f"{avg:.2f}" if scores else "—", str(len(scores)), sample)
    console.print(score_table)

    # 5b. Chairman Synthesis
    final_verdict = ""
    with console.status("[bold gold1]The Chairman is synthesizing the final verdict...[/bold gold1]"):
        final_verdict = await CouncilChairman.synthesize(question, execution_results, reviews, logger=logger)

    # Display Final Verdict
    clear_screen()
    display_header()
    console.rule("[bold gold1]THE CHAIRMAN'S VERDICT[/bold gold1]")
    console.print(Panel(final_verdict, title="Final Answer", border_style="gold1"))

    # Save Full Session
    final_results['peer_reviews'] = reviews
    final_results['chairman_verdict'] = final_verdict
    cost_breakdown = logger.get_cost_breakdown()
    final_results['tokens'] = {
        "input_tokens": logger.total_input_tokens,
        "output_tokens": logger.total_output_tokens,
        "total_tokens": logger.total_input_tokens + logger.total_output_tokens,
        "total_cost_usd": cost_breakdown["total_cost_usd"],
        "log_file": logger.path
    }
    
    output_file = "council_session_complete.json"
    with open(output_file, 'w') as f:
        json.dump(final_results, f, indent=2)
    
    # Persist summary at end of session log
    logger.finalize()
    
    console.print(f"\n[bold]Complete session results saved to:[/bold] [cyan]{output_file}[/cyan]")
    console.print(f"[bold]LLM token usage:[/bold] {logger.summary()}")
    console.print(f"[dim]Full log: {logger.path}[/dim]")

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
