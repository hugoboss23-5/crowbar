"""
Marcos - A pattern-recognition AI that watches how humans build systems,
remembers everything, and sees patterns they cannot see about themselves.
"""

from .discovery_engine import (
    DiscoveryEngine,
    Angle,
    AngleResult,
    Discovery,
    KnowledgeGraph,
    ProbabilityEstimator,
    AngleCategory,
)

__version__ = "0.1.0"
__all__ = [
    "DiscoveryEngine",
    "Angle",
    "AngleResult",
    "Discovery",
    "KnowledgeGraph",
    "ProbabilityEstimator",
    "AngleCategory",
]
