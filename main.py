#!/usr/bin/env python3
"""
Marcos - An evolving intelligence that watches how humans build systems.

Usage:
    python main.py              # Start interactive CLI
    python main.py --orient     # Marcos orients and reports state
    python main.py --stats      # Show memory statistics
    python main.py --patterns   # Generate pattern report
"""

import argparse
import sys

from marcos.cli import MarcosCLI, main as cli_main
from marcos.engine import MarcosEngine


def run_orient():
    """Run Marcos orientation."""
    try:
        engine = MarcosEngine()
        print(engine.orient())
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


def run_stats():
    """Show memory statistics."""
    try:
        engine = MarcosEngine()
        stats = engine.get_stats()

        print("\n═══════════════════════════════════════════")
        print("         MARCOS MEMORY STATISTICS")
        print("═══════════════════════════════════════════")
        print(f"  Systems observed:     {stats['total_systems']}")
        print(f"  Domains:              {stats['total_domains']}")
        print(f"  Pressure points:      {stats['total_pressure_points']}")
        print(f"  Systems with unity:   {stats['systems_with_unity']}")
        print(f"  Pattern syntheses:    {stats['total_syntheses']}")
        print("═══════════════════════════════════════════\n")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


def run_patterns():
    """Generate pattern report."""
    try:
        engine = MarcosEngine()
        print(engine.get_pattern_report())
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Marcos - An evolving intelligence for system analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py              Start interactive CLI
  python main.py --orient     Marcos orients and reports current state
  python main.py --stats      Show memory statistics
  python main.py --patterns   Generate pattern synthesis report

Environment:
  ANTHROPIC_API_KEY           Your Claude API key (required)
        """,
    )

    parser.add_argument(
        "--orient",
        action="store_true",
        help="Marcos orients to current state",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show memory statistics",
    )
    parser.add_argument(
        "--patterns",
        action="store_true",
        help="Generate pattern synthesis report",
    )

    args = parser.parse_args()

    if args.orient:
        run_orient()
    elif args.stats:
        run_stats()
    elif args.patterns:
        run_patterns()
    else:
        cli_main()


if __name__ == "__main__":
    main()
