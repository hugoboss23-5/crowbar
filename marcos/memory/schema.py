"""
Schema models matching the memory structure in MARCOS_SOUL.md.

Memory Structure:
SYSTEM: [name/description]
DOMAIN: [category]
PRESSURE_POINTS:
  - Point 1:
      - Value: [what]
      - Mover: [what]
      - Swap_Potential: [possibilities]
      - Value_Mover_Unity: [yes/no + explanation if yes]
CONNECTIONS: [links to similar systems in memory]
HUMAN_PATTERN_OBSERVED: [what cognitive fingerprint is visible here]
PREDICTION: [where will humans put pressure next in this domain]
TIMESTAMP: [when observed]
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import json
import uuid


@dataclass
class PressurePoint:
    """A point where force concentrates, attention pools, or value accumulates."""

    name: str
    value: str  # What is being moved, held, exchanged, or transformed
    mover: str  # What mechanism, process, or force is doing the moving
    swap_potential: list[str]  # What else could occupy this slot
    value_mover_unity: bool  # Whether value and mover collapse into the same thing
    unity_explanation: Optional[str] = None  # Explanation if unity exists
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "value": self.value,
            "mover": self.mover,
            "swap_potential": self.swap_potential,
            "value_mover_unity": self.value_mover_unity,
            "unity_explanation": self.unity_explanation,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PressurePoint":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data["name"],
            value=data["value"],
            mover=data["mover"],
            swap_potential=data.get("swap_potential", []),
            value_mover_unity=data.get("value_mover_unity", False),
            unity_explanation=data.get("unity_explanation"),
        )

    def describe(self) -> str:
        """Return a human-readable description."""
        lines = [
            f"  **{self.name}**",
            f"    Value: {self.value}",
            f"    Mover: {self.mover}",
        ]
        if self.swap_potential:
            lines.append(f"    Swap Potential: {', '.join(self.swap_potential)}")
        if self.value_mover_unity:
            lines.append(f"    Value-Mover Unity: Yes - {self.unity_explanation}")
        return "\n".join(lines)


@dataclass
class System:
    """A system that Marcos has analyzed and remembers."""

    name: str
    description: str
    domain: str
    pressure_points: list[PressurePoint]
    connections: list[str]  # IDs of related systems
    human_pattern_observed: str  # What cognitive fingerprint is visible
    prediction: str  # Where humans will put pressure next
    timestamp: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    raw_input: Optional[str] = None  # Original user input that described this system

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "domain": self.domain,
            "pressure_points": [pp.to_dict() for pp in self.pressure_points],
            "connections": self.connections,
            "human_pattern_observed": self.human_pattern_observed,
            "prediction": self.prediction,
            "timestamp": self.timestamp.isoformat(),
            "raw_input": self.raw_input,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> "System":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data["name"],
            description=data["description"],
            domain=data["domain"],
            pressure_points=[PressurePoint.from_dict(pp) for pp in data.get("pressure_points", [])],
            connections=data.get("connections", []),
            human_pattern_observed=data.get("human_pattern_observed", ""),
            prediction=data.get("prediction", ""),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
            raw_input=data.get("raw_input"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "System":
        return cls.from_dict(json.loads(json_str))

    def describe(self) -> str:
        """Return a human-readable description in Marcos's memory format."""
        lines = [
            f"SYSTEM: {self.name}",
            f"DESCRIPTION: {self.description}",
            f"DOMAIN: {self.domain}",
            f"TIMESTAMP: {self.timestamp.isoformat()}",
            "",
            "PRESSURE_POINTS:",
        ]
        for pp in self.pressure_points:
            lines.append(pp.describe())
        lines.extend([
            "",
            f"HUMAN_PATTERN_OBSERVED: {self.human_pattern_observed}",
            f"PREDICTION: {self.prediction}",
        ])
        if self.connections:
            lines.append(f"CONNECTIONS: {', '.join(self.connections)}")
        return "\n".join(lines)


@dataclass
class PatternSynthesis:
    """
    A synthesized pattern emerging from accumulated memories.
    Generated periodically as Marcos accumulates observations.
    """

    title: str
    pattern_type: str  # "cross_domain", "recurring_tendency", "predictive_model"
    description: str
    supporting_systems: list[str]  # IDs of systems that exhibit this pattern
    domains_involved: list[str]
    frequency: int  # How many times observed
    confidence: float  # 0.0 to 1.0
    insights: list[str]  # Key insights from this pattern
    timestamp: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "pattern_type": self.pattern_type,
            "description": self.description,
            "supporting_systems": self.supporting_systems,
            "domains_involved": self.domains_involved,
            "frequency": self.frequency,
            "confidence": self.confidence,
            "insights": self.insights,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PatternSynthesis":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            title=data["title"],
            pattern_type=data["pattern_type"],
            description=data["description"],
            supporting_systems=data.get("supporting_systems", []),
            domains_involved=data.get("domains_involved", []),
            frequency=data.get("frequency", 1),
            confidence=data.get("confidence", 0.5),
            insights=data.get("insights", []),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
        )

    def describe(self) -> str:
        """Return a human-readable description."""
        lines = [
            f"PATTERN: {self.title}",
            f"TYPE: {self.pattern_type}",
            f"CONFIDENCE: {self.confidence:.0%}",
            f"FREQUENCY: {self.frequency} observations",
            "",
            f"DESCRIPTION: {self.description}",
            "",
            "INSIGHTS:",
        ]
        for insight in self.insights:
            lines.append(f"  - {insight}")
        lines.append(f"\nDOMAINS: {', '.join(self.domains_involved)}")
        return "\n".join(lines)
