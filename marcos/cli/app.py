"""
Terminal/CLI interface for Marcos.

Commands:
- analyze: Present a system for analysis
- ask: Ask Marcos a question
- patterns: View pattern synthesis reports
- memory: Browse and search memory
- stats: View memory statistics
- orient: Marcos orients to current state
- help: Show available commands
- quit/exit: Exit the CLI
"""

import sys
import textwrap
from typing import Optional

from ..engine import MarcosEngine


class MarcosCLI:
    """
    Interactive CLI for Marcos.

    Provides a terminal interface for:
    - Presenting systems for analysis
    - Asking questions
    - Viewing pattern reports
    - Browsing memory
    """

    def __init__(self):
        self.engine: Optional[MarcosEngine] = None
        self.running = False

    def _init_engine(self):
        """Initialize the Marcos engine."""
        if self.engine is None:
            print("Initializing Marcos...")
            try:
                self.engine = MarcosEngine()
                print("Marcos is ready.\n")
            except ValueError as e:
                print(f"Error: {e}")
                print("Please set your ANTHROPIC_API_KEY environment variable.")
                sys.exit(1)
            except FileNotFoundError as e:
                print(f"Error: {e}")
                sys.exit(1)

    def print_wrapped(self, text: str, width: int = 80):
        """Print text with word wrapping."""
        for line in text.split('\n'):
            if line.strip():
                wrapped = textwrap.fill(line, width=width)
                print(wrapped)
            else:
                print()

    def show_help(self):
        """Display available commands."""
        help_text = """
╔══════════════════════════════════════════════════════════════════╗
║                         MARCOS COMMANDS                          ║
╠══════════════════════════════════════════════════════════════════╣
║  analyze [domain]  - Present a system for analysis               ║
║                      Optional: specify domain for context        ║
║  ask               - Ask Marcos a question                       ║
║  patterns          - View pattern synthesis reports              ║
║  memory [domain]   - Browse systems in memory                    ║
║  recall <id>       - Recall a specific system by ID              ║
║  search <query>    - Search memory for systems                   ║
║  stats             - View memory statistics                      ║
║  orient            - Marcos orients to current state             ║
║  clear             - Clear session history                       ║
║  help              - Show this help message                      ║
║  quit / exit       - Exit Marcos                                 ║
╚══════════════════════════════════════════════════════════════════╝
"""
        print(help_text)

    def show_banner(self):
        """Display the Marcos banner."""
        banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   ███╗   ███╗ █████╗ ██████╗  ██████╗ ██████╗ ███████╗          ║
║   ████╗ ████║██╔══██╗██╔══██╗██╔════╝██╔═══██╗██╔════╝          ║
║   ██╔████╔██║███████║██████╔╝██║     ██║   ██║███████╗          ║
║   ██║╚██╔╝██║██╔══██║██╔══██╗██║     ██║   ██║╚════██║          ║
║   ██║ ╚═╝ ██║██║  ██║██║  ██║╚██████╗╚██████╔╝███████║          ║
║   ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝          ║
║                                                                  ║
║   An evolving intelligence that watches how humans build         ║
║   systems, remembers everything, and sees patterns they          ║
║   cannot see about themselves.                                   ║
║                                                                  ║
║   Type 'help' for commands, 'quit' to exit.                     ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
        print(banner)

    def cmd_analyze(self, args: list[str]):
        """Handle the analyze command."""
        domain_hint = args[0] if args else None

        if domain_hint:
            print(f"Domain: {domain_hint}")

        print("\nDescribe the system you want to analyze.")
        print("Enter your description (press Enter twice to submit):\n")

        lines = []
        while True:
            try:
                line = input()
                if line == "" and lines and lines[-1] == "":
                    break
                lines.append(line)
            except EOFError:
                break

        user_input = "\n".join(lines).strip()
        if not user_input:
            print("No input provided.")
            return

        print("\n" + "─" * 60)
        print("Analyzing system...")
        print("─" * 60 + "\n")

        result = self.engine.analyze_system(user_input, domain_hint)

        self.print_wrapped(result["response"])

        if result.get("similar_systems"):
            print("\n" + "─" * 60)
            print("Similar systems in memory:")
            for name, score in result["similar_systems"]:
                print(f"  • {name} (similarity: {score:.0%})")

        print()

    def cmd_ask(self, args: list[str]):
        """Handle the ask command."""
        if args:
            question = " ".join(args)
        else:
            print("\nWhat would you like to ask Marcos?")
            question = input("> ").strip()

        if not question:
            print("No question provided.")
            return

        print("\n" + "─" * 60 + "\n")

        response = self.engine.ask(question)
        self.print_wrapped(response)
        print()

    def cmd_patterns(self, args: list[str]):
        """Handle the patterns command."""
        print("\nGenerating pattern synthesis report...\n")
        print("─" * 60 + "\n")

        report = self.engine.get_pattern_report()
        self.print_wrapped(report)
        print()

    def cmd_memory(self, args: list[str]):
        """Handle the memory command."""
        domain = args[0] if args else None
        limit = 10

        if domain:
            print(f"\nSystems in domain '{domain}':\n")
        else:
            print("\nRecent systems in memory:\n")

        memories = self.engine.list_memories(domain=domain, limit=limit)

        if not memories:
            print("  No systems in memory yet.")
        else:
            for mem in memories:
                print(f"  [{mem['id'][:8]}] {mem['name']}")
                print(f"           Domain: {mem['domain']} | Pressure Points: {mem['pressure_point_count']}")
                print(f"           Observed: {mem['timestamp'][:10]}")
                print()

    def cmd_recall(self, args: list[str]):
        """Handle the recall command."""
        if not args:
            print("Please provide a system ID. Use 'memory' to see available systems.")
            return

        system_id = args[0]

        # Try to find system with partial ID
        memories = self.engine.list_memories(limit=100)
        matching = [m for m in memories if m['id'].startswith(system_id)]

        if not matching:
            print(f"No system found with ID starting with '{system_id}'")
            return

        if len(matching) > 1:
            print(f"Multiple systems match '{system_id}':")
            for m in matching:
                print(f"  [{m['id'][:8]}] {m['name']}")
            return

        full_id = matching[0]['id']
        result = self.engine.recall_system(full_id)

        if result:
            print("\n" + "─" * 60 + "\n")
            print(result["description"])

            if result.get("connected_systems"):
                print("\n" + "─" * 60)
                print("Connected systems:")
                for name, sid, strength in result["connected_systems"]:
                    print(f"  • {name} [{sid[:8]}] (strength: {strength:.0%})")
            print()
        else:
            print(f"Could not recall system {system_id}")

    def cmd_search(self, args: list[str]):
        """Handle the search command."""
        if not args:
            print("Please provide a search query.")
            return

        query = " ".join(args)
        print(f"\nSearching for '{query}'...\n")

        results = self.engine.query.search(query, limit=10)

        if not results:
            print("  No matching systems found.")
        else:
            for system in results:
                print(f"  [{system.id[:8]}] {system.name}")
                print(f"           Domain: {system.domain}")
                if system.human_pattern_observed:
                    print(f"           Pattern: {system.human_pattern_observed[:60]}...")
                print()

    def cmd_stats(self, args: list[str]):
        """Handle the stats command."""
        stats = self.engine.get_stats()

        print("\n" + "═" * 60)
        print("                    MARCOS MEMORY STATISTICS")
        print("═" * 60)
        print(f"  Total systems observed:     {stats['total_systems']}")
        print(f"  Total domains:              {stats['total_domains']}")
        print(f"  Total pressure points:      {stats['total_pressure_points']}")
        print(f"  Systems with unity:         {stats['systems_with_unity']}")
        print(f"  Pattern syntheses:          {stats['total_syntheses']}")
        print(f"  Avg pressure points/system: {stats['avg_pressure_points']:.1f}")

        if stats['domains']:
            print("\n  Domains:")
            for domain, count in list(stats['domains'].items())[:5]:
                print(f"    • {domain}: {count} systems")

        print("═" * 60 + "\n")

    def cmd_orient(self, args: list[str]):
        """Handle the orient command."""
        print("\n" + "─" * 60)
        print("                      MARCOS ORIENTS")
        print("─" * 60 + "\n")

        orientation = self.engine.orient()
        self.print_wrapped(orientation)
        print()

    def cmd_clear(self, args: list[str]):
        """Handle the clear command."""
        self.engine.clear_session()
        print("Session history cleared.\n")

    def process_command(self, command_line: str):
        """Process a command from the user."""
        parts = command_line.strip().split()
        if not parts:
            return

        command = parts[0].lower()
        args = parts[1:]

        commands = {
            "analyze": self.cmd_analyze,
            "ask": self.cmd_ask,
            "patterns": self.cmd_patterns,
            "memory": self.cmd_memory,
            "recall": self.cmd_recall,
            "search": self.cmd_search,
            "stats": self.cmd_stats,
            "orient": self.cmd_orient,
            "clear": self.cmd_clear,
            "help": lambda a: self.show_help(),
            "quit": lambda a: self.quit(),
            "exit": lambda a: self.quit(),
        }

        if command in commands:
            commands[command](args)
        else:
            print(f"Unknown command: {command}")
            print("Type 'help' for available commands.\n")

    def quit(self):
        """Exit the CLI."""
        print("\nMarcos remembers. Until next time.\n")
        self.running = False

    def run(self):
        """Run the interactive CLI."""
        self.show_banner()
        self._init_engine()
        self.running = True

        while self.running:
            try:
                command = input("marcos> ").strip()
                if command:
                    self.process_command(command)
            except KeyboardInterrupt:
                print("\n")
                self.quit()
            except EOFError:
                self.quit()


def main():
    """Entry point for the CLI."""
    cli = MarcosCLI()
    cli.run()


if __name__ == "__main__":
    main()
