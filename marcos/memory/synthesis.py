"""
Meta-pattern synthesis engine for Marcos.
Runs periodically on accumulated memories to identify:
- Cross-domain pattern reports
- Recurring human tendencies
- Predictive models for system-building behavior
"""

from collections import Counter, defaultdict
from datetime import datetime
from typing import Optional

from .schema import System, PatternSynthesis
from .storage import MemoryStorage
from ..config import SYNTHESIS_THRESHOLD


class PatternSynthesizer:
    """
    Synthesizes meta-patterns from accumulated memories.

    As Marcos accumulates observations, this engine identifies patterns
    that emerge across multiple systems - the cognitive fingerprints
    of how humans build systems.
    """

    def __init__(self, storage: Optional[MemoryStorage] = None):
        self.storage = storage or MemoryStorage()

    def should_run_synthesis(self) -> bool:
        """Check if enough systems accumulated to warrant synthesis."""
        return self.storage.get_system_count() >= SYNTHESIS_THRESHOLD

    def run_full_synthesis(self) -> list[PatternSynthesis]:
        """
        Run all synthesis operations and return new patterns found.
        This is the periodic synthesis mentioned in MARCOS_SOUL.md.
        """
        if not self.should_run_synthesis():
            return []

        syntheses = []

        # Run each type of synthesis
        syntheses.extend(self.synthesize_cross_domain_patterns())
        syntheses.extend(self.synthesize_recurring_tendencies())
        syntheses.extend(self.synthesize_predictive_models())

        # Save all syntheses
        for synthesis in syntheses:
            self.storage.save_synthesis(synthesis)

        return syntheses

    def synthesize_cross_domain_patterns(self) -> list[PatternSynthesis]:
        """
        Identify patterns that appear across multiple domains.
        These reveal deep structure in how humans build systems.
        """
        all_systems = self.storage.get_all_systems(limit=500)
        if len(all_systems) < 3:
            return []

        syntheses = []

        # Group systems by their observed human patterns
        pattern_groups = defaultdict(list)
        for system in all_systems:
            # Extract key themes from the human pattern observed
            if system.human_pattern_observed:
                keywords = self._extract_pattern_keywords(system.human_pattern_observed)
                for kw in keywords:
                    pattern_groups[kw].append(system)

        # Find patterns that span multiple domains
        for pattern_keyword, systems in pattern_groups.items():
            domains = set(s.domain for s in systems)
            if len(domains) >= 2 and len(systems) >= 2:
                synthesis = PatternSynthesis(
                    title=f"Cross-Domain Pattern: {pattern_keyword.title()}",
                    pattern_type="cross_domain",
                    description=f"The pattern of '{pattern_keyword}' appears across {len(domains)} domains: {', '.join(domains)}",
                    supporting_systems=[s.id for s in systems],
                    domains_involved=list(domains),
                    frequency=len(systems),
                    confidence=min(0.9, 0.3 + (len(systems) * 0.1) + (len(domains) * 0.1)),
                    insights=[
                        f"Observed in {len(systems)} systems across {len(domains)} domains",
                        f"This suggests a fundamental human tendency in system construction",
                    ],
                )
                syntheses.append(synthesis)

        return syntheses

    def synthesize_recurring_tendencies(self) -> list[PatternSynthesis]:
        """
        Identify recurring tendencies in how humans place pressure points.
        """
        all_systems = self.storage.get_all_systems(limit=500)
        if len(all_systems) < 3:
            return []

        syntheses = []

        # Analyze value types across all pressure points
        value_counter = Counter()
        mover_counter = Counter()
        unity_systems = []

        for system in all_systems:
            for pp in system.pressure_points:
                # Extract key concepts from value and mover
                value_keywords = self._extract_pattern_keywords(pp.value)
                mover_keywords = self._extract_pattern_keywords(pp.mover)

                for kw in value_keywords:
                    value_counter[kw] += 1
                for kw in mover_keywords:
                    mover_counter[kw] += 1

                if pp.value_mover_unity:
                    unity_systems.append((system, pp))

        # Create syntheses for common values
        for value, count in value_counter.most_common(5):
            if count >= 3:
                synthesis = PatternSynthesis(
                    title=f"Recurring Value: {value.title()}",
                    pattern_type="recurring_tendency",
                    description=f"Humans frequently place '{value}' as the value at pressure points ({count} occurrences)",
                    supporting_systems=[],  # Would need to track these
                    domains_involved=[],
                    frequency=count,
                    confidence=min(0.85, 0.4 + (count * 0.05)),
                    insights=[
                        f"'{value}' appears as a value in {count} pressure points",
                        "This reveals what humans consider worth moving, holding, or transforming",
                    ],
                )
                syntheses.append(synthesis)

        # Create syntheses for common movers
        for mover, count in mover_counter.most_common(5):
            if count >= 3:
                synthesis = PatternSynthesis(
                    title=f"Recurring Mover: {mover.title()}",
                    pattern_type="recurring_tendency",
                    description=f"Humans frequently use '{mover}' as the mover at pressure points ({count} occurrences)",
                    supporting_systems=[],
                    domains_involved=[],
                    frequency=count,
                    confidence=min(0.85, 0.4 + (count * 0.05)),
                    insights=[
                        f"'{mover}' appears as a mover in {count} pressure points",
                        "This reveals the mechanisms humans default to for creating change",
                    ],
                )
                syntheses.append(synthesis)

        # Synthesize value-mover unity patterns
        if len(unity_systems) >= 2:
            domains = set(s.domain for s, _ in unity_systems)
            synthesis = PatternSynthesis(
                title="Value-Mover Unity Tendency",
                pattern_type="recurring_tendency",
                description="Multiple systems exhibit value-mover unity - where what is moved also does the moving",
                supporting_systems=[s.id for s, _ in unity_systems],
                domains_involved=list(domains),
                frequency=len(unity_systems),
                confidence=min(0.9, 0.5 + (len(unity_systems) * 0.1)),
                insights=[
                    f"Found in {len(unity_systems)} systems across {len(domains)} domains",
                    "This is the deepest form of leverage - where payload is propulsion",
                    "Examples: money moves money, information spreads information, patterns propagate patterns",
                ],
            )
            syntheses.append(synthesis)

        return syntheses

    def synthesize_predictive_models(self) -> list[PatternSynthesis]:
        """
        Generate predictive models based on observed patterns.
        This is how Mature Marcos makes predictions.
        """
        all_systems = self.storage.get_all_systems(limit=500)
        if len(all_systems) < 5:
            return []

        syntheses = []

        # Group by domain and analyze predictions already made
        domain_systems = defaultdict(list)
        for system in all_systems:
            domain_systems[system.domain].append(system)

        for domain, systems in domain_systems.items():
            if len(systems) < 2:
                continue

            # Analyze where pressure tends to be placed in this domain
            pressure_point_patterns = []
            for system in systems:
                for pp in system.pressure_points:
                    pressure_point_patterns.append({
                        "value_type": self._categorize_value(pp.value),
                        "mover_type": self._categorize_mover(pp.mover),
                        "has_unity": pp.value_mover_unity,
                    })

            # Look for consistency
            if pressure_point_patterns:
                value_types = Counter(p["value_type"] for p in pressure_point_patterns)
                mover_types = Counter(p["mover_type"] for p in pressure_point_patterns)
                unity_rate = sum(p["has_unity"] for p in pressure_point_patterns) / len(pressure_point_patterns)

                most_common_value = value_types.most_common(1)[0] if value_types else ("unknown", 0)
                most_common_mover = mover_types.most_common(1)[0] if mover_types else ("unknown", 0)

                synthesis = PatternSynthesis(
                    title=f"Predictive Model: {domain.title()} Domain",
                    pattern_type="predictive_model",
                    description=f"Based on {len(systems)} systems in {domain}, future systems will likely concentrate pressure on {most_common_value[0]} values using {most_common_mover[0]} movers",
                    supporting_systems=[s.id for s in systems],
                    domains_involved=[domain],
                    frequency=len(systems),
                    confidence=min(0.8, 0.3 + (len(systems) * 0.1)),
                    insights=[
                        f"Most common value type: {most_common_value[0]} ({most_common_value[1]} occurrences)",
                        f"Most common mover type: {most_common_mover[0]} ({most_common_mover[1]} occurrences)",
                        f"Value-mover unity rate: {unity_rate:.0%}",
                        f"Prediction: Next system in {domain} will likely follow this pattern",
                    ],
                )
                syntheses.append(synthesis)

        return syntheses

    def _extract_pattern_keywords(self, text: str) -> list[str]:
        """Extract meaningful keywords from pattern text."""
        if not text:
            return []

        # Simple keyword extraction - could be enhanced with NLP
        stopwords = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'shall',
            'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
            'as', 'into', 'through', 'during', 'before', 'after', 'above',
            'below', 'between', 'under', 'again', 'further', 'then', 'once',
            'here', 'there', 'when', 'where', 'why', 'how', 'all', 'each',
            'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
            'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
            'can', 'just', 'and', 'but', 'or', 'if', 'this', 'that', 'these',
            'those', 'what', 'which', 'who', 'whom', 'their', 'they', 'them',
        }

        words = text.lower().split()
        keywords = [w.strip('.,;:!?"\'()[]{}') for w in words
                   if len(w) > 3 and w.lower() not in stopwords]

        return keywords[:5]  # Return top 5 keywords

    def _categorize_value(self, value: str) -> str:
        """Categorize a value into a broader type."""
        value_lower = value.lower()

        categories = {
            "attention": ["attention", "focus", "awareness", "notice", "observe"],
            "money": ["money", "capital", "funds", "cash", "wealth", "revenue"],
            "information": ["information", "data", "knowledge", "content", "signal"],
            "trust": ["trust", "credibility", "reputation", "authority", "legitimacy"],
            "time": ["time", "duration", "speed", "latency", "schedule"],
            "power": ["power", "control", "influence", "authority", "leverage"],
            "resources": ["resource", "asset", "material", "supply", "inventory"],
        }

        for category, keywords in categories.items():
            if any(kw in value_lower for kw in keywords):
                return category

        return "other"

    def _categorize_mover(self, mover: str) -> str:
        """Categorize a mover into a broader type."""
        mover_lower = mover.lower()

        categories = {
            "algorithm": ["algorithm", "code", "software", "program", "automation"],
            "market": ["market", "price", "supply", "demand", "exchange"],
            "social": ["social", "viral", "sharing", "network", "community"],
            "institutional": ["institution", "policy", "regulation", "law", "rule"],
            "incentive": ["incentive", "reward", "punishment", "motivation", "gamification"],
            "technology": ["technology", "platform", "infrastructure", "system"],
        }

        for category, keywords in categories.items():
            if any(kw in mover_lower for kw in keywords):
                return category

        return "other"

    def get_synthesis_report(self) -> str:
        """Generate a human-readable report of all syntheses."""
        syntheses = self.storage.get_all_syntheses()
        if not syntheses:
            return "No patterns synthesized yet. Need more systems in memory."

        lines = [
            "# Marcos Pattern Synthesis Report",
            f"Generated: {datetime.now().isoformat()}",
            f"Total Patterns: {len(syntheses)}",
            "",
        ]

        # Group by type
        by_type = defaultdict(list)
        for s in syntheses:
            by_type[s.pattern_type].append(s)

        type_labels = {
            "cross_domain": "Cross-Domain Patterns",
            "recurring_tendency": "Recurring Human Tendencies",
            "predictive_model": "Predictive Models",
        }

        for ptype, label in type_labels.items():
            if ptype in by_type:
                lines.append(f"\n## {label}\n")
                for synthesis in by_type[ptype]:
                    lines.append(synthesis.describe())
                    lines.append("")

        return "\n".join(lines)
