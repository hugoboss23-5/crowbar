"""
Discovery Engine for Marcos

Makes breakthroughs inevitable through systematic angle exhaustion.
Instead of trying one approach and giving up, it generates enough different
angles/perspectives that discovery becomes statistically guaranteed.

Core Math:
    P(breakthrough) = 1 - (1 - p)^n

    where:
        p = estimated probability that a single angle yields a discovery
        n = number of angles generated

    To find the right number of angles:
        n = log(1 - target_confidence) / log(1 - p)
"""

from __future__ import annotations

import logging
import math
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Iterator, Optional

logger = logging.getLogger(__name__)


class AngleCategory(Enum):
    """Categories of angles for generating diverse perspectives on a problem."""

    TEMPORAL = "temporal"       # Time-based patterns, sequences, correlations with events
    STRUCTURAL = "structural"   # Format, encoding, nesting, length patterns
    RELATIONAL = "relational"   # Connections to other data, networks, similarities
    SEMANTIC = "semantic"       # Meaning, language, cultural context, selection significance
    META = "meta"               # Who made this, why, what are they hiding, what changed
    SOURCE = "source"           # Human intel, archives, existing tools, communities
    TECHNICAL = "technical"     # Algorithms, methods, edge cases, combined techniques
    INVERSE = "inverse"         # What would make this unsolvable, what assumptions are wrong


class DiscoveryState(Enum):
    """State of the discovery process."""

    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    SOLVED = "solved"
    EXHAUSTED = "exhausted"


@dataclass
class Angle:
    """
    An angle is a specific frame/perspective on a problem.

    Each angle represents a different way of looking at the problem,
    drawn from one of the angle categories.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    category: AngleCategory = AngleCategory.TECHNICAL
    description: str = ""
    hypothesis: str = ""
    method: str = ""
    parent_id: Optional[str] = None  # If branched from another angle's discovery
    created_at: datetime = field(default_factory=datetime.now)

    def __repr__(self) -> str:
        return f"Angle({self.id}, {self.category.value}: {self.description[:50]}...)"


@dataclass
class AngleResult:
    """Result of executing a single angle."""

    angle: Angle
    has_signal: bool = False
    signal_strength: float = 0.0  # 0.0 to 1.0
    findings: list[str] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    error: Optional[str] = None
    executed_at: datetime = field(default_factory=datetime.now)

    @property
    def is_discovery(self) -> bool:
        """Returns True if this result represents a meaningful discovery."""
        return self.has_signal and self.signal_strength >= 0.3


@dataclass
class Discovery:
    """
    A discovery is a validated finding that advances understanding.

    Discoveries are synthesized from one or more angle results that
    showed significant signal.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    description: str = ""
    confidence: float = 0.0  # 0.0 to 1.0
    source_angles: list[str] = field(default_factory=list)  # Angle IDs
    implications: list[str] = field(default_factory=list)
    next_questions: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ProbabilityLog:
    """Log entry for probability calculations, enabling audit trail."""

    timestamp: datetime = field(default_factory=datetime.now)
    loop_iteration: int = 0
    estimated_p: float = 0.0
    target_confidence: float = 0.0
    calculated_n: int = 0
    factors: dict[str, float] = field(default_factory=dict)
    reasoning: str = ""


class KnowledgeGraph:
    """
    Accumulates knowledge across discovery loops.

    Stores:
    - All angles tried and their outcomes
    - Discoveries made
    - Relationships between findings
    - Failed approaches (which are also data)
    """

    def __init__(self) -> None:
        self.angles: dict[str, Angle] = {}
        self.results: dict[str, AngleResult] = {}
        self.discoveries: dict[str, Discovery] = {}
        self.failed_approaches: list[str] = []
        self.domain_knowledge: dict[str, Any] = {}
        self.connections: list[tuple[str, str, str]] = []  # (from_id, to_id, relationship)
        self.created_at: datetime = datetime.now()
        self.last_updated: datetime = datetime.now()

    def add_angle(self, angle: Angle) -> None:
        """Record an angle that was tried."""
        self.angles[angle.id] = angle
        self.last_updated = datetime.now()

    def add_result(self, result: AngleResult) -> None:
        """Record the result of an angle execution."""
        self.results[result.angle.id] = result
        if not result.has_signal:
            self.failed_approaches.append(result.angle.id)
        self.last_updated = datetime.now()

    def add_discovery(self, discovery: Discovery) -> None:
        """Record a validated discovery."""
        self.discoveries[discovery.id] = discovery
        self.last_updated = datetime.now()

    def add_connection(self, from_id: str, to_id: str, relationship: str) -> None:
        """Record a relationship between two entities."""
        self.connections.append((from_id, to_id, relationship))
        self.last_updated = datetime.now()

    def merge(self, findings: list[AngleResult]) -> "KnowledgeGraph":
        """
        Merge new findings into the knowledge graph.
        Returns self for chaining.
        """
        for result in findings:
            self.add_result(result)
        return self

    def get_successful_angles(self) -> list[AngleResult]:
        """Return all angle results that had signal."""
        return [r for r in self.results.values() if r.has_signal]

    def get_failed_angles(self) -> list[AngleResult]:
        """Return all angle results that had no signal."""
        return [r for r in self.results.values() if not r.has_signal]

    def get_coverage_by_category(self) -> dict[AngleCategory, int]:
        """Return count of angles tried per category."""
        coverage: dict[AngleCategory, int] = {cat: 0 for cat in AngleCategory}
        for angle in self.angles.values():
            coverage[angle.category] += 1
        return coverage

    def to_dict(self) -> dict[str, Any]:
        """Serialize knowledge graph for persistence."""
        return {
            "angles": {k: vars(v) for k, v in self.angles.items()},
            "results": {k: vars(v) for k, v in self.results.items()},
            "discoveries": {k: vars(v) for k, v in self.discoveries.items()},
            "failed_approaches": self.failed_approaches,
            "domain_knowledge": self.domain_knowledge,
            "connections": self.connections,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
        }


class ProbabilityEstimator:
    """
    Estimates per-angle probability (p) based on problem characteristics.

    Factors considered:
    1. Problem novelty - Has this type of problem been solved before?
    2. Data availability - How much can we actually test?
    3. Constraint level - How bounded is the solution space?
    4. Prior work - Have others tried and failed?
    """

    # Base probabilities by problem novelty
    NOVELTY_BASE = {
        "well_studied": (0.10, 0.25),   # Well-studied domain
        "partially_explored": (0.03, 0.10),  # Partially explored
        "completely_novel": (0.01, 0.03),    # Completely novel
    }

    # Multipliers for other factors
    DATA_MULTIPLIERS = {
        "rich": 1.5,
        "moderate": 1.0,
        "sparse": 0.5,
    }

    CONSTRAINT_MULTIPLIERS = {
        "highly_constrained": 2.0,
        "moderately_constrained": 1.0,
        "wide_open": 0.5,
    }

    PRIOR_WORK_ADJUSTMENTS = {
        "many_failures": (0.01, 0.02),
        "some_attempts": (0.03, 0.08),
        "fresh_problem": (0.05, 0.15),
    }

    def __init__(self) -> None:
        self.estimation_history: list[ProbabilityLog] = []

    def estimate(
        self,
        novelty: str = "partially_explored",
        data_availability: str = "moderate",
        constraint_level: str = "moderately_constrained",
        prior_work: str = "some_attempts",
        custom_factors: Optional[dict[str, float]] = None,
        loop_iteration: int = 0,
    ) -> tuple[float, ProbabilityLog]:
        """
        Estimate per-angle probability based on problem characteristics.

        Returns:
            Tuple of (estimated_p, log_entry)
        """
        # Start with base probability from novelty
        base_range = self.NOVELTY_BASE.get(novelty, self.NOVELTY_BASE["partially_explored"])
        base_p = (base_range[0] + base_range[1]) / 2

        # Apply multipliers
        data_mult = self.DATA_MULTIPLIERS.get(data_availability, 1.0)
        constraint_mult = self.CONSTRAINT_MULTIPLIERS.get(constraint_level, 1.0)

        # Factor in prior work
        prior_range = self.PRIOR_WORK_ADJUSTMENTS.get(prior_work, (0.03, 0.08))
        prior_factor = (prior_range[0] + prior_range[1]) / 2

        # Combine: weighted average of base and prior, then apply multipliers
        combined_base = (base_p * 0.6 + prior_factor * 0.4)
        estimated_p = combined_base * data_mult * constraint_mult

        # Apply any custom factors
        factors = {
            "novelty": base_p,
            "data_availability": data_mult,
            "constraint_level": constraint_mult,
            "prior_work": prior_factor,
        }

        if custom_factors:
            for factor_name, multiplier in custom_factors.items():
                estimated_p *= multiplier
                factors[factor_name] = multiplier

        # Clamp to valid probability range
        estimated_p = max(0.001, min(0.5, estimated_p))

        # Create log entry
        log_entry = ProbabilityLog(
            loop_iteration=loop_iteration,
            estimated_p=estimated_p,
            factors=factors,
            reasoning=f"Novelty={novelty}, Data={data_availability}, "
                      f"Constraints={constraint_level}, Prior={prior_work}",
        )

        self.estimation_history.append(log_entry)
        logger.info(f"Estimated p={estimated_p:.4f} for iteration {loop_iteration}")

        return estimated_p, log_entry


class AngleGenerator(ABC):
    """
    Abstract base class for angle generators.

    Subclass this to create domain-specific angle generators.
    """

    @abstractmethod
    def generate(
        self,
        problem: str,
        knowledge: KnowledgeGraph,
        count: int,
        categories: Optional[list[AngleCategory]] = None,
    ) -> list[Angle]:
        """Generate angles for the problem."""
        pass


class DefaultAngleGenerator(AngleGenerator):
    """
    Default angle generator that creates angles across all categories.

    This is a template generator - in practice, you'd subclass this
    or provide custom implementations for specific domains.
    """

    # Templates for generating angles in each category
    CATEGORY_TEMPLATES = {
        AngleCategory.TEMPORAL: [
            "Analyze time-based patterns in {problem}",
            "Look for sequences and progressions",
            "Correlate with known events or timelines",
            "Examine frequency distributions over time",
            "Search for periodic or cyclical patterns",
        ],
        AngleCategory.STRUCTURAL: [
            "Examine format and encoding structures",
            "Look for nesting and hierarchical patterns",
            "Analyze length and size distributions",
            "Search for delimiters and boundaries",
            "Investigate byte-level patterns",
        ],
        AngleCategory.RELATIONAL: [
            "Map connections to related data sources",
            "Build network graphs of relationships",
            "Find similarities with known patterns",
            "Trace dependencies and references",
            "Cluster by similarity metrics",
        ],
        AngleCategory.SEMANTIC: [
            "Extract meaning and intent",
            "Analyze language and terminology",
            "Consider cultural context",
            "Examine selection criteria and significance",
            "Look for hidden messages or encodings",
        ],
        AngleCategory.META: [
            "Investigate who created this and why",
            "Look for what's being hidden or obscured",
            "Track what changed and when",
            "Examine metadata and provenance",
            "Analyze the creation process itself",
        ],
        AngleCategory.SOURCE: [
            "Search for human intelligence sources",
            "Examine archives and historical records",
            "Look for existing tools and solutions",
            "Find communities who've worked on similar problems",
            "Gather domain expert knowledge",
        ],
        AngleCategory.TECHNICAL: [
            "Apply standard algorithms for this domain",
            "Try edge case handling approaches",
            "Combine multiple techniques",
            "Use brute force enumeration where feasible",
            "Apply statistical analysis methods",
        ],
        AngleCategory.INVERSE: [
            "What would make this problem unsolvable?",
            "Which assumptions might be wrong?",
            "What if the problem is misframed?",
            "What constraints might be artificial?",
            "What would disprove our current theory?",
        ],
    }

    def generate(
        self,
        problem: str,
        knowledge: KnowledgeGraph,
        count: int,
        categories: Optional[list[AngleCategory]] = None,
    ) -> list[Angle]:
        """
        Generate angles for the problem, distributed across categories.

        Args:
            problem: Description of the problem to solve
            knowledge: Current knowledge graph with prior results
            count: Number of angles to generate
            categories: Specific categories to use (all if None)

        Returns:
            List of generated angles
        """
        if categories is None:
            categories = list(AngleCategory)

        angles: list[Angle] = []
        tried_angle_ids = set(knowledge.angles.keys())
        coverage = knowledge.get_coverage_by_category()

        # Distribute angles across categories, favoring undercovered ones
        per_category = max(1, count // len(categories))
        remainder = count % len(categories)

        # Sort categories by coverage (least covered first)
        sorted_categories = sorted(categories, key=lambda c: coverage.get(c, 0))

        for i, category in enumerate(sorted_categories):
            # Give extra angles to least covered categories
            cat_count = per_category + (1 if i < remainder else 0)
            templates = self.CATEGORY_TEMPLATES.get(category, [])

            for j in range(cat_count):
                template_idx = j % len(templates) if templates else 0
                template = templates[template_idx] if templates else f"Analyze {category.value} aspects"

                angle = Angle(
                    category=category,
                    description=template.format(problem=problem[:100]),
                    hypothesis=f"The {category.value} perspective may reveal patterns in: {problem[:50]}",
                    method=f"Apply {category.value} analysis techniques",
                )

                # Avoid duplicating exact angles (by description)
                if angle.id not in tried_angle_ids:
                    angles.append(angle)
                    tried_angle_ids.add(angle.id)

        logger.info(f"Generated {len(angles)} angles across {len(categories)} categories")
        return angles[:count]  # Ensure we don't exceed requested count

    def branch_on_discovery(
        self,
        result: AngleResult,
        count: int = 15,
    ) -> list[Angle]:
        """
        Generate specialized follow-up angles based on a discovery.

        When an angle yields signal, we branch into 10-20 new angles
        that explore that specific direction more deeply.
        """
        angles: list[Angle] = []
        base_description = result.angle.description
        category = result.angle.category

        # Generate follow-up angles in the same category and related categories
        related_categories = self._get_related_categories(category)

        for i in range(count):
            follow_up_category = related_categories[i % len(related_categories)]

            angle = Angle(
                category=follow_up_category,
                description=f"Follow up on signal: {base_description[:50]} - variation {i+1}",
                hypothesis=f"Deeper exploration of {category.value} finding",
                method=f"Specialized {follow_up_category.value} analysis",
                parent_id=result.angle.id,
            )
            angles.append(angle)

        logger.info(f"Branched {len(angles)} angles from discovery in {category.value}")
        return angles

    def _get_related_categories(self, category: AngleCategory) -> list[AngleCategory]:
        """Get categories related to the given category for branching."""
        relations = {
            AngleCategory.TEMPORAL: [AngleCategory.TEMPORAL, AngleCategory.STRUCTURAL, AngleCategory.META],
            AngleCategory.STRUCTURAL: [AngleCategory.STRUCTURAL, AngleCategory.TECHNICAL, AngleCategory.RELATIONAL],
            AngleCategory.RELATIONAL: [AngleCategory.RELATIONAL, AngleCategory.SEMANTIC, AngleCategory.SOURCE],
            AngleCategory.SEMANTIC: [AngleCategory.SEMANTIC, AngleCategory.META, AngleCategory.INVERSE],
            AngleCategory.META: [AngleCategory.META, AngleCategory.SOURCE, AngleCategory.TEMPORAL],
            AngleCategory.SOURCE: [AngleCategory.SOURCE, AngleCategory.RELATIONAL, AngleCategory.TECHNICAL],
            AngleCategory.TECHNICAL: [AngleCategory.TECHNICAL, AngleCategory.STRUCTURAL, AngleCategory.INVERSE],
            AngleCategory.INVERSE: [AngleCategory.INVERSE, AngleCategory.SEMANTIC, AngleCategory.META],
        }
        return relations.get(category, list(AngleCategory))


class DiscoveryEngine:
    """
    Main Discovery Engine that makes breakthroughs inevitable through
    systematic angle exhaustion.

    Usage:
        engine = DiscoveryEngine()
        result = engine.run(
            problem="Find the vulnerability in this smart contract",
            target_confidence=0.95,
        )
    """

    def __init__(
        self,
        angle_generator: Optional[AngleGenerator] = None,
        probability_estimator: Optional[ProbabilityEstimator] = None,
        angle_executor: Optional[Callable[[Angle, KnowledgeGraph], AngleResult]] = None,
        solution_checker: Optional[Callable[[str, list[Discovery]], bool]] = None,
    ) -> None:
        """
        Initialize the Discovery Engine.

        Args:
            angle_generator: Custom angle generator (uses default if None)
            probability_estimator: Custom probability estimator (uses default if None)
            angle_executor: Function to execute an angle and return results
            solution_checker: Function to check if problem is solved
        """
        self.angle_generator = angle_generator or DefaultAngleGenerator()
        self.probability_estimator = probability_estimator or ProbabilityEstimator()
        self.angle_executor = angle_executor or self._default_executor
        self.solution_checker = solution_checker or self._default_solution_checker

        self.state = DiscoveryState.INITIALIZED
        self.knowledge: Optional[KnowledgeGraph] = None
        self.probability_logs: list[ProbabilityLog] = []
        self.current_iteration = 0
        self.max_iterations = 100  # Safety limit

        # Interrupt handling
        self._interrupt_requested = False
        self._checkpoint: Optional[dict[str, Any]] = None

    @staticmethod
    def calculate_angles_needed(p: float, target_confidence: float) -> int:
        """
        Calculate number of angles needed to achieve target confidence.

        Formula: n = log(1 - target_confidence) / log(1 - p)

        Args:
            p: Estimated probability that a single angle yields discovery
            target_confidence: Desired probability of breakthrough (0.0 to 1.0)

        Returns:
            Number of angles needed (minimum 1)
        """
        if p <= 0 or p >= 1:
            raise ValueError(f"p must be between 0 and 1 (exclusive), got {p}")
        if target_confidence <= 0 or target_confidence >= 1:
            raise ValueError(f"target_confidence must be between 0 and 1 (exclusive), got {target_confidence}")

        n = math.log(1 - target_confidence) / math.log(1 - p)
        return max(1, int(math.ceil(n)))

    @staticmethod
    def calculate_breakthrough_probability(p: float, n: int) -> float:
        """
        Calculate probability of breakthrough given p and n.

        Formula: P(breakthrough) = 1 - (1 - p)^n

        Args:
            p: Probability that a single angle yields discovery
            n: Number of angles to execute

        Returns:
            Probability of at least one breakthrough
        """
        if p <= 0 or p >= 1:
            raise ValueError(f"p must be between 0 and 1 (exclusive), got {p}")
        if n < 1:
            raise ValueError(f"n must be at least 1, got {n}")

        return 1 - ((1 - p) ** n)

    def run(
        self,
        problem: str,
        target_confidence: float = 0.95,
        novelty: str = "partially_explored",
        data_availability: str = "moderate",
        constraint_level: str = "moderately_constrained",
        prior_work: str = "some_attempts",
        initial_knowledge: Optional[KnowledgeGraph] = None,
    ) -> dict[str, Any]:
        """
        Run the discovery loop until the problem is solved or exhausted.

        Args:
            problem: Description of the problem to solve
            target_confidence: Target probability of breakthrough (default 0.95)
            novelty: Problem novelty level
            data_availability: How much data is available
            constraint_level: How constrained the solution space is
            prior_work: Amount of prior work on similar problems
            initial_knowledge: Pre-existing knowledge to start with

        Returns:
            Dictionary containing discoveries, knowledge graph, and metadata
        """
        logger.info(f"Starting Discovery Engine for: {problem[:100]}...")

        # Initialize state
        self.state = DiscoveryState.RUNNING
        self.knowledge = initial_knowledge or KnowledgeGraph()
        self.knowledge.domain_knowledge["problem"] = problem
        self.current_iteration = 0
        self._interrupt_requested = False

        all_discoveries: list[Discovery] = []

        while self.state == DiscoveryState.RUNNING:
            self.current_iteration += 1

            # Check safety limits
            if self.current_iteration > self.max_iterations:
                logger.warning(f"Reached maximum iterations ({self.max_iterations})")
                self.state = DiscoveryState.EXHAUSTED
                break

            # Check for interrupt
            if self._interrupt_requested:
                self.state = DiscoveryState.PAUSED
                self._save_checkpoint(problem, target_confidence)
                logger.info("Discovery paused at user request")
                break

            logger.info(f"=== Iteration {self.current_iteration} ===")

            # Step 1: Estimate per-angle probability
            p, prob_log = self.probability_estimator.estimate(
                novelty=novelty,
                data_availability=data_availability,
                constraint_level=constraint_level,
                prior_work=prior_work,
                loop_iteration=self.current_iteration,
            )
            prob_log.target_confidence = target_confidence

            # Step 2: Calculate angles needed
            n = self.calculate_angles_needed(p, target_confidence)
            prob_log.calculated_n = n
            self.probability_logs.append(prob_log)

            expected_p_breakthrough = self.calculate_breakthrough_probability(p, n)
            logger.info(f"p={p:.4f}, n={n}, P(breakthrough)={expected_p_breakthrough:.4f}")

            # Step 3: Generate angle matrix
            angles = self.angle_generator.generate(
                problem=problem,
                knowledge=self.knowledge,
                count=n,
            )

            # Step 4: Execute all angles
            results: list[AngleResult] = []
            for angle in angles:
                self.knowledge.add_angle(angle)
                result = self.angle_executor(angle, self.knowledge)
                results.append(result)
                self.knowledge.add_result(result)

                # Branch immediately on signal
                if result.has_signal:
                    logger.info(f"Signal detected in angle {angle.id}: {angle.description[:50]}")
                    branch_count = 10 + int(result.signal_strength * 10)  # 10-20 based on strength

                    if isinstance(self.angle_generator, DefaultAngleGenerator):
                        new_angles = self.angle_generator.branch_on_discovery(result, branch_count)
                        angles.extend(new_angles)

            # Step 5: Process results
            discoveries = [r for r in results if r.is_discovery]
            failures = [r for r in results if not r.has_signal]

            logger.info(f"Results: {len(discoveries)} discoveries, {len(failures)} failures")

            if discoveries:
                # Synthesize discoveries
                for result in discoveries:
                    discovery = Discovery(
                        title=f"Discovery from {result.angle.category.value} analysis",
                        description="; ".join(result.findings) if result.findings else "Signal detected",
                        confidence=result.signal_strength,
                        source_angles=[result.angle.id],
                    )
                    self.knowledge.add_discovery(discovery)
                    all_discoveries.append(discovery)

                # Check if solved
                if self.solution_checker(problem, all_discoveries):
                    self.state = DiscoveryState.SOLVED
                    logger.info("Problem solved!")
                    break

                # Not fully solved - update knowledge factors for next iteration
                # Discoveries suggest we're on the right track, potentially raise p
                data_availability = "rich" if data_availability != "rich" else data_availability

            else:
                # All angles failed - this IS data
                # Analyze failures and potentially lower p for next iteration
                logger.info("All angles failed - using failure data to inform next iteration")

                # Failures suggest problem is harder than expected
                if novelty == "well_studied":
                    novelty = "partially_explored"
                elif novelty == "partially_explored":
                    novelty = "completely_novel"

                prior_work = "many_failures"

            # Merge all results into knowledge
            self.knowledge.merge(results)

        # Compile final result
        return {
            "state": self.state.value,
            "problem": problem,
            "iterations": self.current_iteration,
            "discoveries": all_discoveries,
            "knowledge": self.knowledge,
            "probability_logs": self.probability_logs,
            "total_angles_tried": len(self.knowledge.angles),
            "successful_angles": len(self.knowledge.get_successful_angles()),
            "failed_angles": len(self.knowledge.get_failed_angles()),
        }

    def run_iterator(
        self,
        problem: str,
        target_confidence: float = 0.95,
        **kwargs: Any,
    ) -> Iterator[dict[str, Any]]:
        """
        Run the discovery loop as an iterator, yielding after each iteration.

        This allows for interruptible and resumable operation.

        Yields:
            Dictionary with current state after each iteration
        """
        self.state = DiscoveryState.RUNNING
        self.knowledge = kwargs.get("initial_knowledge") or KnowledgeGraph()
        self.knowledge.domain_knowledge["problem"] = problem
        self.current_iteration = 0

        novelty = kwargs.get("novelty", "partially_explored")
        data_availability = kwargs.get("data_availability", "moderate")
        constraint_level = kwargs.get("constraint_level", "moderately_constrained")
        prior_work = kwargs.get("prior_work", "some_attempts")

        all_discoveries: list[Discovery] = []

        while self.state == DiscoveryState.RUNNING:
            self.current_iteration += 1

            if self.current_iteration > self.max_iterations:
                self.state = DiscoveryState.EXHAUSTED
                break

            # Estimate and calculate
            p, prob_log = self.probability_estimator.estimate(
                novelty=novelty,
                data_availability=data_availability,
                constraint_level=constraint_level,
                prior_work=prior_work,
                loop_iteration=self.current_iteration,
            )
            prob_log.target_confidence = target_confidence
            n = self.calculate_angles_needed(p, target_confidence)
            prob_log.calculated_n = n
            self.probability_logs.append(prob_log)

            # Generate and execute angles
            angles = self.angle_generator.generate(problem, self.knowledge, n)
            results = []

            for angle in angles:
                self.knowledge.add_angle(angle)
                result = self.angle_executor(angle, self.knowledge)
                results.append(result)
                self.knowledge.add_result(result)

            # Process results
            discoveries = [r for r in results if r.is_discovery]

            for result in discoveries:
                discovery = Discovery(
                    title=f"Discovery from {result.angle.category.value} analysis",
                    description="; ".join(result.findings) if result.findings else "Signal detected",
                    confidence=result.signal_strength,
                    source_angles=[result.angle.id],
                )
                self.knowledge.add_discovery(discovery)
                all_discoveries.append(discovery)

            if discoveries and self.solution_checker(problem, all_discoveries):
                self.state = DiscoveryState.SOLVED

            # Yield current state
            yield {
                "state": self.state.value,
                "iteration": self.current_iteration,
                "p": p,
                "n": n,
                "angles_executed": len(results),
                "discoveries_this_iteration": len(discoveries),
                "total_discoveries": len(all_discoveries),
                "knowledge": self.knowledge,
            }

    def pause(self) -> None:
        """Request the engine to pause after the current iteration."""
        self._interrupt_requested = True
        logger.info("Pause requested - will pause after current iteration")

    def resume(self, checkpoint: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """
        Resume from a paused state or checkpoint.

        Args:
            checkpoint: Optional checkpoint to resume from

        Returns:
            Result of continuing the discovery process
        """
        if checkpoint:
            self._load_checkpoint(checkpoint)
        elif self._checkpoint:
            self._load_checkpoint(self._checkpoint)
        else:
            raise ValueError("No checkpoint available to resume from")

        self._interrupt_requested = False
        return self.run(
            problem=self._checkpoint["problem"],
            target_confidence=self._checkpoint["target_confidence"],
            initial_knowledge=self.knowledge,
        )

    def _save_checkpoint(self, problem: str, target_confidence: float) -> None:
        """Save current state as a checkpoint."""
        self._checkpoint = {
            "problem": problem,
            "target_confidence": target_confidence,
            "iteration": self.current_iteration,
            "knowledge": self.knowledge.to_dict() if self.knowledge else None,
            "probability_logs": [vars(log) for log in self.probability_logs],
        }

    def _load_checkpoint(self, checkpoint: dict[str, Any]) -> None:
        """Load state from a checkpoint."""
        self._checkpoint = checkpoint
        self.current_iteration = checkpoint.get("iteration", 0)
        # Note: Full knowledge graph restoration would require deserialization

    def _default_executor(self, angle: Angle, knowledge: KnowledgeGraph) -> AngleResult:
        """
        Default angle executor - returns no signal.

        Override this with actual analysis logic for your domain.
        """
        return AngleResult(
            angle=angle,
            has_signal=False,
            signal_strength=0.0,
            findings=[],
        )

    def _default_solution_checker(self, problem: str, discoveries: list[Discovery]) -> bool:
        """
        Default solution checker - never considers problem solved.

        Override this with actual solution validation logic for your domain.
        """
        return False

    def get_probability_audit_log(self) -> list[dict[str, Any]]:
        """
        Get the complete audit log of probability calculations.

        Returns:
            List of all probability calculations with reasoning
        """
        return [
            {
                "timestamp": log.timestamp.isoformat(),
                "iteration": log.loop_iteration,
                "estimated_p": log.estimated_p,
                "target_confidence": log.target_confidence,
                "calculated_n": log.calculated_n,
                "factors": log.factors,
                "reasoning": log.reasoning,
            }
            for log in self.probability_logs
        ]


def analyze_failure_patterns(results: list[AngleResult]) -> dict[str, Any]:
    """
    Analyze patterns in failed angles to inform next iteration.

    Failed angles are data - they tell us what doesn't work and
    help narrow the search space.
    """
    failed = [r for r in results if not r.has_signal]

    category_failures: dict[AngleCategory, int] = {cat: 0 for cat in AngleCategory}
    for result in failed:
        category_failures[result.angle.category] += 1

    # Find most-failed category
    worst_category = max(category_failures, key=category_failures.get) if failed else None

    # Calculate failure rate
    failure_rate = len(failed) / len(results) if results else 0

    return {
        "total_failures": len(failed),
        "failure_rate": failure_rate,
        "failures_by_category": {k.value: v for k, v in category_failures.items()},
        "worst_performing_category": worst_category.value if worst_category else None,
        "recommendation": "Try different categories" if failure_rate > 0.9 else "Continue current approach",
    }
