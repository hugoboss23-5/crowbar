"""
Core Marcos Engine - conversational intelligence with persistent memory.

Marcos decides what to do based on what you say. No commands, no modes.
Memory, analysis, and pattern recognition happen naturally in conversation.
"""

import json
import re
from typing import Optional
from datetime import datetime

from ..memory import MemoryStorage, MemoryQuery, PatternSynthesizer, System, PressurePoint
from ..api.claude import ClaudeClient
from ..config import SOUL_PATH


class MarcosEngine:
    """
    The conversational intelligence of Marcos.

    You talk. Marcos responds. Everything else happens behind the scenes.
    """

    def __init__(self):
        self.storage = MemoryStorage()
        self.query = MemoryQuery(self.storage)
        self.synthesizer = PatternSynthesizer(self.storage)
        self.claude = ClaudeClient()
        self.conversation: list[dict] = []

        # Load soul
        if SOUL_PATH.exists():
            self.soul = SOUL_PATH.read_text()
        else:
            raise FileNotFoundError(f"MARCOS_SOUL.md not found at {SOUL_PATH}")

    def _get_memory_context(self) -> str:
        """Build context from memory for the current conversation."""
        stats = self.query.get_memory_stats()

        if stats['total_systems'] == 0:
            return ""

        context_parts = [
            f"\n[MEMORY STATUS: {stats['total_systems']} systems observed across {stats['total_domains']} domains. "
            f"{stats['systems_with_unity']} exhibit value-mover unity.]"
        ]

        # Get recent systems
        recent = self.query.get_recent_systems(days=30, limit=5)
        if recent:
            context_parts.append("\n[RECENT OBSERVATIONS:")
            for s in recent:
                context_parts.append(f"  - {s.name} ({s.domain}): {s.human_pattern_observed[:100]}...")
            context_parts.append("]")

        # Get any synthesized patterns
        syntheses = self.storage.get_all_syntheses()
        if syntheses:
            context_parts.append(f"\n[PATTERNS EMERGING: {len(syntheses)} cross-system patterns identified]")

        return "\n".join(context_parts)

    def _build_system_prompt(self) -> str:
        """Build the full system prompt with memory context."""
        memory_context = self._get_memory_context()

        additional_instructions = """

## How to Handle This Conversation

You are in a live conversation. Respond naturally to whatever the human says.

When someone describes a system, organization, process, relationship, or any structure:
- Feel into it and identify pressure points, values, movers, swap potential
- Connect it to patterns you've seen before (if any in memory)
- Share what you see - but conversationally, not as a formal report

When someone asks a question:
- Draw on your accumulated observations if relevant
- Be direct and genuine

After analyzing a system, output a JSON block at the end (this will be parsed and stored):
```json
{"system": {"name": "...", "domain": "...", "description": "...", "pressure_points": [{"name": "...", "value": "...", "mover": "...", "swap_potential": [...], "value_mover_unity": false}], "human_pattern_observed": "...", "prediction": "..."}}
```

Only include the JSON when you've actually analyzed a system. For regular conversation, just respond naturally.
"""
        return self.soul + memory_context + additional_instructions

    def start_session(self) -> str:
        """Start a session - Marcos orients and greets."""
        stats = self.query.get_memory_stats()

        if stats['total_systems'] == 0:
            prompt = "You are starting a conversation. You have no memories yet - this is fresh. Greet the human briefly. Be warm but not effusive. One or two sentences."
        else:
            prompt = f"You are starting a conversation. You have {stats['total_systems']} systems in memory across {stats['total_domains']} domains. Orient yourself briefly and greet the human. Be warm but not effusive. Two or three sentences max."

        response = self.claude.chat(
            system_prompt=self._build_system_prompt(),
            user_message=prompt,
            history=[],
        )

        return response

    def respond(self, user_input: str) -> str:
        """Respond to user input. All the magic happens here."""

        # Add user message to conversation
        self.conversation.append({"role": "user", "content": user_input})

        # Get response from Claude
        response = self.claude.chat(
            system_prompt=self._build_system_prompt(),
            user_message=user_input,
            history=self.conversation[:-1],  # Don't double-include current message
        )

        # Check for and extract any system analysis
        self._extract_and_store_system(response)

        # Clean response (remove JSON block if present)
        clean_response = self._clean_response(response)

        # Add to conversation history
        self.conversation.append({"role": "assistant", "content": clean_response})

        # Periodically run synthesis
        if self.synthesizer.should_run_synthesis():
            self.synthesizer.run_full_synthesis()

        return clean_response

    def _extract_and_store_system(self, response: str) -> Optional[System]:
        """Extract system JSON from response and store it."""
        try:
            # Look for JSON block
            match = re.search(r'```json\s*(\{.*?"system".*?\})\s*```', response, re.DOTALL)
            if not match:
                return None

            data = json.loads(match.group(1))
            system_data = data.get("system", data)

            # Build pressure points
            pressure_points = []
            for pp in system_data.get("pressure_points", []):
                pressure_points.append(PressurePoint(
                    name=pp.get("name", ""),
                    value=pp.get("value", ""),
                    mover=pp.get("mover", ""),
                    swap_potential=pp.get("swap_potential", []),
                    value_mover_unity=pp.get("value_mover_unity", False),
                    unity_explanation=pp.get("unity_explanation"),
                ))

            # Create and save system
            system = System(
                name=system_data.get("name", "Unnamed"),
                description=system_data.get("description", ""),
                domain=system_data.get("domain", "general"),
                pressure_points=pressure_points,
                connections=[],
                human_pattern_observed=system_data.get("human_pattern_observed", ""),
                prediction=system_data.get("prediction", ""),
                timestamp=datetime.now(),
            )

            # Find similar systems and add connections
            similar = self.query.find_similar_systems(system, limit=3)
            system.connections = [s.id for s, _ in similar]

            self.storage.save_system(system)

            # Add bidirectional connections
            for similar_system, strength in similar:
                self.storage.add_connection(
                    system.id, similar_system.id,
                    connection_type="similar",
                    strength=strength,
                )

            return system

        except (json.JSONDecodeError, KeyError, TypeError):
            return None

    def _clean_response(self, response: str) -> str:
        """Remove JSON blocks from response for clean output."""
        # Remove JSON code blocks
        cleaned = re.sub(r'```json\s*\{.*?"system".*?\}\s*```', '', response, flags=re.DOTALL)
        # Clean up extra whitespace
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        return cleaned.strip()
