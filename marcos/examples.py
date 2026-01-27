"""
Examples demonstrating the Discovery Engine.

These examples show how to use the Discovery Engine for different
problem types and configurations.
"""

import random
from typing import Any

from .discovery_engine import (
    Angle,
    AngleResult,
    Discovery,
    DiscoveryEngine,
    KnowledgeGraph,
)


def example_probability_calculations() -> None:
    """
    Example: Understanding the core probability math.

    P(breakthrough) = 1 - (1 - p)^n
    n = log(1 - target_confidence) / log(1 - p)
    """
    print("=== Probability Calculations ===\n")

    # Example 1: Low probability per angle
    p = 0.02  # 2% chance each angle yields discovery
    target = 0.97  # Want 97% confidence

    n = DiscoveryEngine.calculate_angles_needed(p, target)
    actual_prob = DiscoveryEngine.calculate_breakthrough_probability(p, n)

    print(f"Example 1: p=0.02 (2% per angle), target=0.97 (97% confidence)")
    print(f"  Angles needed: {n}")
    print(f"  Actual P(breakthrough) with {n} angles: {actual_prob:.4f}")
    print()

    # Example 2: Higher probability per angle
    p = 0.15  # 15% chance each angle
    target = 0.95  # 95% confidence

    n = DiscoveryEngine.calculate_angles_needed(p, target)
    actual_prob = DiscoveryEngine.calculate_breakthrough_probability(p, n)

    print(f"Example 2: p=0.15 (15% per angle), target=0.95 (95% confidence)")
    print(f"  Angles needed: {n}")
    print(f"  Actual P(breakthrough) with {n} angles: {actual_prob:.4f}")
    print()

    # Example 3: Show how n changes with different p values
    print("How angles needed changes with per-angle probability (target=0.95):")
    for p in [0.01, 0.02, 0.05, 0.10, 0.15, 0.20, 0.25]:
        n = DiscoveryEngine.calculate_angles_needed(p, 0.95)
        print(f"  p={p:.2f}: need {n:4d} angles")


def create_simulated_executor(
    discovery_probability: float = 0.1,
    problem_domain: str = "test",
) -> Any:
    """
    Create a simulated angle executor for testing.

    This simulates executing angles with a configurable probability
    of finding signal.
    """

    def executor(angle: Angle, knowledge: KnowledgeGraph) -> AngleResult:
        # Simulate finding signal with given probability
        has_signal = random.random() < discovery_probability

        if has_signal:
            signal_strength = 0.3 + random.random() * 0.7  # 0.3 to 1.0
            findings = [
                f"Found pattern in {angle.category.value} analysis",
                f"Signal detected in {problem_domain} domain",
            ]
        else:
            signal_strength = random.random() * 0.2  # 0 to 0.2
            findings = []

        return AngleResult(
            angle=angle,
            has_signal=has_signal,
            signal_strength=signal_strength,
            findings=findings,
        )

    return executor


def create_simulated_solution_checker(
    discoveries_needed: int = 3,
) -> Any:
    """
    Create a simulated solution checker.

    Considers the problem solved once enough discoveries are made.
    """

    def checker(problem: str, discoveries: list[Discovery]) -> bool:
        # Count high-confidence discoveries
        high_confidence = [d for d in discoveries if d.confidence >= 0.5]
        return len(high_confidence) >= discoveries_needed

    return checker


def example_basic_run() -> None:
    """
    Example: Basic discovery engine run with simulated execution.
    """
    print("\n=== Basic Discovery Engine Run ===\n")

    # Create engine with simulated components
    engine = DiscoveryEngine(
        angle_executor=create_simulated_executor(discovery_probability=0.08),
        solution_checker=create_simulated_solution_checker(discoveries_needed=3),
    )

    # Set lower max iterations for demo
    engine.max_iterations = 5

    # Run discovery
    result = engine.run(
        problem="Find the pattern in this encrypted data",
        target_confidence=0.95,
        novelty="partially_explored",
        data_availability="moderate",
        constraint_level="moderately_constrained",
        prior_work="some_attempts",
    )

    print(f"Final state: {result['state']}")
    print(f"Iterations: {result['iterations']}")
    print(f"Total angles tried: {result['total_angles_tried']}")
    print(f"Successful angles: {result['successful_angles']}")
    print(f"Discoveries made: {len(result['discoveries'])}")

    if result['discoveries']:
        print("\nDiscoveries:")
        for d in result['discoveries']:
            print(f"  - {d.title} (confidence: {d.confidence:.2f})")


def example_smart_contract_audit() -> None:
    """
    Example: Smart contract vulnerability analysis.

    This demonstrates the calculation from the task description:
    - Domain: Well-studied (security research exists)
    - Data: Rich (full source code available)
    - Constraints: High (must be valid Solidity)
    - Prior work: Some (audits done but bounty still open)
    """
    print("\n=== Smart Contract Audit Example ===\n")

    from .discovery_engine import ProbabilityEstimator

    estimator = ProbabilityEstimator()

    # Estimate probability for this problem type
    p, log = estimator.estimate(
        novelty="well_studied",  # Security research exists
        data_availability="rich",  # Full source code
        constraint_level="highly_constrained",  # Must be valid Solidity
        prior_work="some_attempts",  # Audits done, bounty open
    )

    print(f"Estimated per-angle probability: {p:.4f} ({p*100:.1f}%)")
    print(f"Factors: {log.factors}")
    print()

    # Calculate angles needed for different confidence levels
    for target in [0.90, 0.95, 0.99]:
        n = DiscoveryEngine.calculate_angles_needed(p, target)
        print(f"For {target*100:.0f}% confidence: need {n} angles")


def example_iterator_usage() -> None:
    """
    Example: Using the iterator interface for interruptible operation.
    """
    print("\n=== Iterator Usage Example ===\n")

    engine = DiscoveryEngine(
        angle_executor=create_simulated_executor(discovery_probability=0.1),
        solution_checker=create_simulated_solution_checker(discoveries_needed=2),
    )
    engine.max_iterations = 3

    print("Running discovery loop with iterator...")
    for state in engine.run_iterator(
        problem="Analyze network traffic pattern",
        target_confidence=0.95,
    ):
        print(f"\nIteration {state['iteration']}:")
        print(f"  p={state['p']:.4f}, n={state['n']}")
        print(f"  Angles executed: {state['angles_executed']}")
        print(f"  Discoveries this iteration: {state['discoveries_this_iteration']}")
        print(f"  Total discoveries: {state['total_discoveries']}")
        print(f"  State: {state['state']}")

        if state['state'] == 'solved':
            print("\nProblem solved!")
            break


def example_audit_log() -> None:
    """
    Example: Examining the probability calculation audit log.
    """
    print("\n=== Audit Log Example ===\n")

    engine = DiscoveryEngine(
        angle_executor=create_simulated_executor(discovery_probability=0.05),
        solution_checker=create_simulated_solution_checker(discoveries_needed=5),
    )
    engine.max_iterations = 3

    # Run discovery
    engine.run(
        problem="Decode unknown cipher",
        target_confidence=0.95,
        novelty="completely_novel",
    )

    # Examine audit log
    print("Probability calculation audit log:")
    for entry in engine.get_probability_audit_log():
        print(f"\n  Iteration {entry['iteration']}:")
        print(f"    Estimated p: {entry['estimated_p']:.4f}")
        print(f"    Target confidence: {entry['target_confidence']:.2f}")
        print(f"    Calculated n: {entry['calculated_n']}")
        print(f"    Reasoning: {entry['reasoning']}")


def run_all_examples() -> None:
    """Run all examples."""
    example_probability_calculations()
    example_basic_run()
    example_smart_contract_audit()
    example_iterator_usage()
    example_audit_log()


if __name__ == "__main__":
    run_all_examples()
