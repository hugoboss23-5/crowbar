"""
Marcos - conversational interface.

No commands. No menus. Just talk to Marcos.
"""

import sys
from ..engine import MarcosEngine


def main():
    """Run Marcos."""
    print()
    print("  MARCOS")
    print("  ──────")
    print()

    try:
        engine = MarcosEngine()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Let Marcos orient and greet
    greeting = engine.start_session()
    print(f"Marcos: {greeting}")
    print()

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue

            if user_input.lower() in ('quit', 'exit', 'bye'):
                print()
                print("Marcos: I'll remember. Until next time.")
                print()
                break

            print()
            response = engine.respond(user_input)
            print(f"Marcos: {response}")
            print()

        except KeyboardInterrupt:
            print()
            print()
            print("Marcos: I'll remember. Until next time.")
            print()
            break
        except EOFError:
            break


if __name__ == "__main__":
    main()
