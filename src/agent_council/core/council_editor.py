"""
Council Editor Module.
Provides interactive functions to edit, add, or remove agents from the council configuration.
"""

from typing import Dict, Any, List
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

console = Console()

class CouncilEditor:
    """Interactive editor for the agent council configuration."""

    @staticmethod
    def display_agents(agents: List[Dict[str, Any]]):
        """Show the current list of agents in a table."""
        table = Table(title="Current Council Composition", show_lines=True)
        table.add_column("#", justify="right", style="cyan", no_wrap=True)
        table.add_column("Name", style="green")
        table.add_column("Persona Preview", style="magenta")
        table.add_column("Web Search", justify="center")
        table.add_column("Reasoning", justify="center")

        for i, agent in enumerate(agents, 1):
            table.add_row(
                str(i),
                agent.get('name', 'Unknown'),
                agent.get('persona', 'No persona')[:50] + "...",
                "Yes" if agent.get('enable_web_search') else "No",
                agent.get('reasoning_effort', 'medium')
            )
        
        console.print(table)

    @classmethod
    def edit_agent(cls, agent: Dict[str, Any]) -> Dict[str, Any]:
        """Interactively edit a single agent."""
        console.print(f"\n[bold]Editing Agent: {agent.get('name')}[/bold]")
        
        # Edit Name
        new_name = Prompt.ask("Name", default=agent.get('name'))
        agent['name'] = new_name
        
        # Edit Persona (show preview first)
        current_persona = agent.get('persona', '')
        console.print(f"\n[dim]Current Persona:[/dim]\n{current_persona[:200]}...")
        if Confirm.ask("Edit full persona description?"):
            console.print("[green]Enter new persona (Enter 'END' on a new line to finish):[/green]")
            lines = []
            while True:
                line = input()
                if line.strip() == 'END':
                    break
                lines.append(line)
            if lines:
                agent['persona'] = "\n".join(lines)
        
        # Edit Settings
        agent['enable_web_search'] = Confirm.ask("Enable Web Search?", default=agent.get('enable_web_search', False))
        
        reasoning = Prompt.ask(
            "Reasoning Effort", 
            choices=["none", "low", "medium", "high"], 
            default=agent.get('reasoning_effort', 'medium')
        )
        agent['reasoning_effort'] = reasoning
        
        return agent

    @classmethod
    def add_agent(cls) -> Dict[str, Any]:
        """Create a new agent from scratch."""
        console.print("\n[bold]Adding New Agent[/bold]")
        
        name = Prompt.ask("Agent Name")
        
        console.print("[green]Enter Persona Description (Enter 'END' on a new line to finish):[/green]")
        lines = []
        while True:
            line = input()
            if line.strip() == 'END':
                break
            lines.append(line)
        persona = "\n".join(lines)
        
        enable_web = Confirm.ask("Enable Web Search?", default=True)
        reasoning = Prompt.ask("Reasoning Effort", choices=["none", "low", "medium", "high"], default="medium")
        
        return {
            "name": name,
            "persona": persona,
            "enable_web_search": enable_web,
            "reasoning_effort": reasoning
        }

    @classmethod
    def run_editor(cls, council_config: Dict[str, Any]) -> Dict[str, Any]:
        """Main loop for the editor."""
        agents = council_config.get('agents', [])
        
        while True:
            console.clear()
            console.rule("[bold blue]Step 3: Council Editor[/bold blue]")
            cls.display_agents(agents)
            
            console.print("\n[bold]Options:[/bold]")
            console.print("[E]dit Agent  [D]elete Agent  [A]dd Agent  [C]ontinue (Finalize)")
            
            choice = Prompt.ask("Choose an action", choices=["e", "d", "a", "c"], default="c").lower()
            
            if choice == "c":
                if not agents:
                    if not Confirm.ask("[red]The council is empty. Are you sure you want to continue?[/red]"):
                        continue
                break
            
            elif choice == "a":
                new_agent = cls.add_agent()
                agents.append(new_agent)
                console.print("[green]Agent added![/green]")
                
            elif choice == "d":
                if not agents:
                    console.print("[red]No agents to delete.[/red]")
                    Prompt.ask("Press Enter")
                    continue
                    
                idx = Prompt.ask("Enter agent # to delete", default="1")
                try:
                    idx = int(idx)
                    if 1 <= idx <= len(agents):
                        removed = agents.pop(idx-1)
                        console.print(f"[yellow]Removed {removed['name']}[/yellow]")
                    else:
                        console.print("[red]Invalid number.[/red]")
                except ValueError:
                    console.print("[red]Invalid input.[/red]")
                
            elif choice == "e":
                if not agents:
                    console.print("[red]No agents to edit.[/red]")
                    Prompt.ask("Press Enter")
                    continue
                    
                idx = Prompt.ask("Enter agent # to edit", default="1")
                try:
                    idx = int(idx)
                    if 1 <= idx <= len(agents):
                        agents[idx-1] = cls.edit_agent(agents[idx-1])
                        console.print("[green]Agent updated![/green]")
                    else:
                        console.print("[red]Invalid number.[/red]")
                except ValueError:
                    console.print("[red]Invalid input.[/red]")
            
            # Pause briefly to let user see confirmation message
            if choice != 'c':
                import time
                time.sleep(0.5)

        council_config['agents'] = agents
        return council_config

