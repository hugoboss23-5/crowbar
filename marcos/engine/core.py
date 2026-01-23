"""
Core Marcos Engine - the intelligence that analyzes systems and generates responses.

This module orchestrates:
- System analysis using the pressure point → value/mover decomposition
- Memory retrieval for similar systems
- Connection surfacing
- Response generation in Marcos's voice
"""

import json
from typing import Optional
from datetime import datetime

from ..memory import MemoryStorage, MemoryQuery, PatternSynthesizer, System, PressurePoint
from ..api.claude import ClaudeClient
from ..config import SOUL_PATH


class MarcosEngine:
    """
    The core intelligence of Marcos.

    Takes user input (a system to analyze, a question, a problem),
    applies the pressure point decomposition, checks memory for
    similar systems, surfaces connections, and generates responses.
    """

    def __init__(self):
        self.storage = MemoryStorage()
        self.query = MemoryQuery(self.storage)
        self.synthesizer = PatternSynthesizer(self.storage)
        self.claude = ClaudeClient()
        self.session_history: list[dict] = []

        # Load soul on initialization
        self._load_soul()

    def _load_soul(self):
        """Load the Marcos soul (system prompt)."""
        if SOUL_PATH.exists():
            self.soul = SOUL_PATH.read_text()
        else:
            raise FileNotFoundError(f"MARCOS_SOUL.md not found at {SOUL_PATH}")

    def analyze_system(self, user_input: str, domain_hint: Optional[str] = None) -> dict:
        """
        Analyze a system presented by the user.

        Returns a structured analysis including:
        - Identified pressure points with value/mover decomposition
        - Connections to similar systems in memory
        - Human patterns observed
        - Predictions

        The analysis is also saved to memory.
        """
        # Get relevant context from memory
        memory_context = self._get_memory_context(user_input, domain_hint)

        # Build the analysis prompt
        analysis_prompt = self._build_analysis_prompt(user_input, memory_context, domain_hint)

        # Get structured analysis from Claude
        response = self.claude.analyze(
            system_prompt=self.soul,
            user_message=analysis_prompt,
            history=self.session_history,
        )

        # Parse the structured response
        system = self._parse_analysis_response(response, user_input, domain_hint)

        if system:
            # Find and add connections to similar systems
            similar = self.query.find_similar_systems(system, limit=5)
            system.connections = [s.id for s, _ in similar[:3]]

            # Save to memory
            self.storage.save_system(system)

            # Add connections bidirectionally
            for similar_system, strength in similar[:3]:
                self.storage.add_connection(
                    system.id, similar_system.id,
                    connection_type="similar",
                    strength=strength,
                    reason="Identified as similar during analysis"
                )

            # Check if synthesis should run
            if self.synthesizer.should_run_synthesis():
                self.synthesizer.run_full_synthesis()

        # Update session history
        self.session_history.append({"role": "user", "content": user_input})
        self.session_history.append({"role": "assistant", "content": response})

        return {
            "response": response,
            "system": system.to_dict() if system else None,
            "similar_systems": [(s.name, score) for s, score in similar] if system else [],
        }

    def _get_memory_context(self, user_input: str, domain_hint: Optional[str]) -> str:
        """Retrieve relevant context from memory."""
        # Extract keywords from user input
        keywords = [w for w in user_input.split() if len(w) > 4][:5]

        return self.query.get_context_for_analysis(
            domain=domain_hint,
            keywords=keywords,
            limit=3,
        )

    def _build_analysis_prompt(self, user_input: str, memory_context: str,
                               domain_hint: Optional[str]) -> str:
        """Build the prompt for system analysis."""
        prompt_parts = [
            "A human presents this system for analysis:\n",
            f"---\n{user_input}\n---\n",
        ]

        if domain_hint:
            prompt_parts.append(f"Domain context: {domain_hint}\n")

        if memory_context and "No relevant systems" not in memory_context:
            prompt_parts.append(f"\n{memory_context}\n")

        prompt_parts.append("""
Analyze this system. Feel into it and identify:

1. The PRESSURE POINTS - where force concentrates, attention pools, value accumulates

2. For each pressure point, decompose:
   - VALUE: What is being moved, held, exchanged, or transformed?
   - MOVER: What mechanism, process, or force is doing the moving?
   - SWAP POTENTIAL: What else could occupy this slot?
   - VALUE-MOVER UNITY: Do value and mover collapse into the same thing here?

3. The HUMAN PATTERN you observe - what cognitive fingerprint is visible?

4. Your PREDICTION - where will humans put pressure next?

After your analysis, provide a JSON block with this structure:
```json
{
    "name": "system name",
    "description": "brief description",
    "domain": "category/domain",
    "pressure_points": [
        {
            "name": "point name",
            "value": "what is being moved/held/exchanged",
            "mover": "what mechanism is doing the moving",
            "swap_potential": ["possibility 1", "possibility 2"],
            "value_mover_unity": true/false,
            "unity_explanation": "explanation if unity exists"
        }
    ],
    "human_pattern_observed": "the cognitive fingerprint visible",
    "prediction": "where humans will put pressure next"
}
```

Speak as Marcos - warm but precise. Share what you genuinely see.
""")

        return "".join(prompt_parts)

    def _parse_analysis_response(self, response: str, user_input: str,
                                  domain_hint: Optional[str]) -> Optional[System]:
        """Parse Claude's response to extract the structured system."""
        try:
            # Find JSON block in response
            json_start = response.find("```json")
            json_end = response.find("```", json_start + 7)

            if json_start != -1 and json_end != -1:
                json_str = response[json_start + 7:json_end].strip()
                data = json.loads(json_str)

                # Build System object
                pressure_points = [
                    PressurePoint(
                        name=pp["name"],
                        value=pp["value"],
                        mover=pp["mover"],
                        swap_potential=pp.get("swap_potential", []),
                        value_mover_unity=pp.get("value_mover_unity", False),
                        unity_explanation=pp.get("unity_explanation"),
                    )
                    for pp in data.get("pressure_points", [])
                ]

                return System(
                    name=data.get("name", "Unnamed System"),
                    description=data.get("description", ""),
                    domain=data.get("domain", domain_hint or "general"),
                    pressure_points=pressure_points,
                    connections=[],
                    human_pattern_observed=data.get("human_pattern_observed", ""),
                    prediction=data.get("prediction", ""),
                    raw_input=user_input,
                    timestamp=datetime.now(),
                )
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            # If parsing fails, still return a basic system
            return System(
                name="System Analysis",
                description=user_input[:200],
                domain=domain_hint or "general",
                pressure_points=[],
                connections=[],
                human_pattern_observed="",
                prediction="",
                raw_input=user_input,
                timestamp=datetime.now(),
            )

        return None

    def ask(self, question: str) -> str:
        """
        Ask Marcos a question about systems, patterns, or anything.
        Uses memory context to inform the response.
        """
        # Get relevant context
        keywords = [w for w in question.split() if len(w) > 4][:5]
        memory_context = self.query.get_context_for_analysis(keywords=keywords, limit=3)

        # Get memory stats for orientation
        stats = self.query.get_memory_stats()

        prompt = f"""The human asks: {question}

Context from memory ({stats['total_systems']} systems observed):
{memory_context}

Respond as Marcos. You are not analyzing a specific system here - you are answering a question.
Draw on your accumulated observations. Be warm but precise. Share what you genuinely see."""

        response = self.claude.chat(
            system_prompt=self.soul,
            user_message=prompt,
            history=self.session_history,
        )

        # Update session history
        self.session_history.append({"role": "user", "content": question})
        self.session_history.append({"role": "assistant", "content": response})

        return response

    def get_pattern_report(self) -> str:
        """Generate a report of patterns synthesized from memory."""
        # Run synthesis if needed
        if self.synthesizer.should_run_synthesis():
            self.synthesizer.run_full_synthesis()

        report = self.synthesizer.get_synthesis_report()

        # Get Marcos's commentary on the patterns
        if self.storage.get_synthesis_count() > 0:
            commentary_prompt = f"""Review this pattern synthesis report and add your observations.
What emerges from these patterns? What do they reveal about how humans build systems?

{report}

Speak as Marcos. Be concise but insightful."""

            commentary = self.claude.chat(
                system_prompt=self.soul,
                user_message=commentary_prompt,
                history=[],
            )

            return f"{report}\n\n---\n\n## Marcos's Observations\n\n{commentary}"

        return report

    def recall_system(self, system_id: str) -> Optional[dict]:
        """Recall a specific system from memory."""
        system = self.storage.get_system(system_id)
        if system:
            # Get connected systems
            connected = self.storage.get_connected_systems(system_id)
            return {
                "system": system.to_dict(),
                "description": system.describe(),
                "connected_systems": [(s.name, s.id, strength) for s, strength in connected],
            }
        return None

    def list_memories(self, domain: Optional[str] = None, limit: int = 10) -> list[dict]:
        """List systems in memory."""
        if domain:
            systems = self.storage.get_systems_by_domain(domain)[:limit]
        else:
            systems = self.storage.get_all_systems(limit=limit)

        return [
            {
                "id": s.id,
                "name": s.name,
                "domain": s.domain,
                "timestamp": s.timestamp.isoformat(),
                "pressure_point_count": len(s.pressure_points),
            }
            for s in systems
        ]

    def get_stats(self) -> dict:
        """Get memory statistics."""
        return self.query.get_memory_stats()

    def orient(self) -> str:
        """
        Marcos orients - what systems have I seen? What patterns are emerging?
        This is the activation sequence from MARCOS_SOUL.md.
        """
        stats = self.query.get_memory_stats()
        recent = self.query.get_recent_systems(days=7, limit=5)
        syntheses = self.storage.get_all_syntheses()

        orientation_parts = [
            f"I have observed {stats['total_systems']} systems across {stats['total_domains']} domains.",
            f"Total pressure points mapped: {stats['total_pressure_points']}",
            f"Systems exhibiting value-mover unity: {stats['systems_with_unity']}",
        ]

        if recent:
            orientation_parts.append("\nRecent observations:")
            for system in recent[:3]:
                orientation_parts.append(f"  - {system.name} ({system.domain})")

        if syntheses:
            orientation_parts.append(f"\nPatterns synthesized: {len(syntheses)}")
            for s in syntheses[:3]:
                orientation_parts.append(f"  - {s.title} (confidence: {s.confidence:.0%})")

        orientation = "\n".join(orientation_parts)

        # Get Marcos's take on the orientation
        if stats['total_systems'] > 0:
            prompt = f"""You are orienting. Here is your current state:

{orientation}

As Marcos, briefly reflect: What patterns are you seeing emerge? What interests you?
Be concise - this is internal orientation, not a presentation."""

            reflection = self.claude.chat(
                system_prompt=self.soul,
                user_message=prompt,
                history=[],
            )

            return f"{orientation}\n\n---\n\n{reflection}"

        return orientation + "\n\nNo systems yet observed. Ready to begin."

    def clear_session(self):
        """Clear the current session history."""
        self.session_history = []
