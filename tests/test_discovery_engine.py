"""
Tests for the Discovery Engine module.
"""

import math
import pytest
from marcos.discovery_engine import (
    Angle,
    AngleCategory,
    AngleResult,
    DefaultAngleGenerator,
    Discovery,
    DiscoveryEngine,
    DiscoveryState,
    KnowledgeGraph,
    ProbabilityEstimator,
    ProbabilityLog,
    analyze_failure_patterns,
)


class TestProbabilityCalculations:
    """Tests for core probability math."""

    def test_calculate_angles_needed_basic(self):
        """Test basic angle calculation."""
        # From the task: p=0.02, target=0.97 -> ~173 angles
        n = DiscoveryEngine.calculate_angles_needed(0.02, 0.97)
        assert 170 <= n <= 176  # Allow small variance from ceiling

    def test_calculate_angles_needed_higher_p(self):
        """Test with higher per-angle probability."""
        # From the task: p=0.15, target=0.95 -> ~18 angles
        n = DiscoveryEngine.calculate_angles_needed(0.15, 0.95)
        assert 17 <= n <= 20

    def test_calculate_angles_needed_minimum(self):
        """Should always return at least 1 angle."""
        n = DiscoveryEngine.calculate_angles_needed(0.99, 0.50)
        assert n >= 1

    def test_calculate_angles_needed_invalid_p(self):
        """Should raise error for invalid p values."""
        with pytest.raises(ValueError):
            DiscoveryEngine.calculate_angles_needed(0, 0.95)
        with pytest.raises(ValueError):
            DiscoveryEngine.calculate_angles_needed(1, 0.95)
        with pytest.raises(ValueError):
            DiscoveryEngine.calculate_angles_needed(-0.1, 0.95)

    def test_calculate_breakthrough_probability(self):
        """Test breakthrough probability calculation."""
        # P = 1 - (1-p)^n
        p, n = 0.1, 10
        expected = 1 - (0.9 ** 10)  # ~0.6513
        actual = DiscoveryEngine.calculate_breakthrough_probability(p, n)
        assert abs(actual - expected) < 0.0001

    def test_calculate_breakthrough_probability_high_n(self):
        """With enough angles, probability approaches 1."""
        p = DiscoveryEngine.calculate_breakthrough_probability(0.05, 100)
        assert p > 0.99

    def test_calculate_breakthrough_probability_invalid(self):
        """Should raise error for invalid inputs."""
        with pytest.raises(ValueError):
            DiscoveryEngine.calculate_breakthrough_probability(0, 10)
        with pytest.raises(ValueError):
            DiscoveryEngine.calculate_breakthrough_probability(0.1, 0)

    def test_probability_math_consistency(self):
        """Verify that n calculation produces target probability."""
        p = 0.08
        target = 0.95
        n = DiscoveryEngine.calculate_angles_needed(p, target)
        actual_prob = DiscoveryEngine.calculate_breakthrough_probability(p, n)
        # Should achieve at least target (may exceed due to ceiling)
        assert actual_prob >= target


class TestProbabilityEstimator:
    """Tests for probability estimation."""

    def test_estimate_well_studied(self):
        """Well-studied problems should have higher p."""
        estimator = ProbabilityEstimator()
        p_studied, _ = estimator.estimate(novelty="well_studied")
        p_novel, _ = estimator.estimate(novelty="completely_novel")
        assert p_studied > p_novel

    def test_estimate_rich_data(self):
        """Rich data should increase p."""
        estimator = ProbabilityEstimator()
        p_rich, _ = estimator.estimate(data_availability="rich")
        p_sparse, _ = estimator.estimate(data_availability="sparse")
        assert p_rich > p_sparse

    def test_estimate_constrained(self):
        """Highly constrained problems should have higher p."""
        estimator = ProbabilityEstimator()
        p_constrained, _ = estimator.estimate(constraint_level="highly_constrained")
        p_open, _ = estimator.estimate(constraint_level="wide_open")
        assert p_constrained > p_open

    def test_estimate_returns_valid_probability(self):
        """Estimated p should always be valid probability."""
        estimator = ProbabilityEstimator()
        for novelty in ["well_studied", "partially_explored", "completely_novel"]:
            for data in ["rich", "moderate", "sparse"]:
                p, _ = estimator.estimate(novelty=novelty, data_availability=data)
                assert 0 < p < 1

    def test_estimate_logs_history(self):
        """Estimator should track history."""
        estimator = ProbabilityEstimator()
        estimator.estimate(loop_iteration=1)
        estimator.estimate(loop_iteration=2)
        assert len(estimator.estimation_history) == 2
        assert estimator.estimation_history[0].loop_iteration == 1
        assert estimator.estimation_history[1].loop_iteration == 2


class TestAngle:
    """Tests for Angle dataclass."""

    def test_angle_creation(self):
        """Test basic angle creation."""
        angle = Angle(
            category=AngleCategory.TECHNICAL,
            description="Test analysis",
            hypothesis="This might work",
        )
        assert angle.id is not None
        assert angle.category == AngleCategory.TECHNICAL
        assert angle.description == "Test analysis"

    def test_angle_unique_ids(self):
        """Each angle should have unique ID."""
        angles = [Angle() for _ in range(100)]
        ids = [a.id for a in angles]
        assert len(ids) == len(set(ids))


class TestAngleResult:
    """Tests for AngleResult dataclass."""

    def test_is_discovery_true(self):
        """Result with signal >= 0.3 is a discovery."""
        angle = Angle()
        result = AngleResult(angle=angle, has_signal=True, signal_strength=0.5)
        assert result.is_discovery

    def test_is_discovery_false_no_signal(self):
        """Result without signal is not a discovery."""
        angle = Angle()
        result = AngleResult(angle=angle, has_signal=False, signal_strength=0.5)
        assert not result.is_discovery

    def test_is_discovery_false_low_strength(self):
        """Result with low strength is not a discovery."""
        angle = Angle()
        result = AngleResult(angle=angle, has_signal=True, signal_strength=0.2)
        assert not result.is_discovery


class TestKnowledgeGraph:
    """Tests for KnowledgeGraph."""

    def test_add_and_retrieve_angles(self):
        """Test adding and retrieving angles."""
        kg = KnowledgeGraph()
        angle = Angle(description="Test")
        kg.add_angle(angle)
        assert angle.id in kg.angles
        assert kg.angles[angle.id] == angle

    def test_add_and_retrieve_results(self):
        """Test adding and retrieving results."""
        kg = KnowledgeGraph()
        angle = Angle()
        result = AngleResult(angle=angle, has_signal=True)
        kg.add_result(result)
        assert angle.id in kg.results

    def test_failed_approaches_tracked(self):
        """Failed angles should be tracked."""
        kg = KnowledgeGraph()
        angle = Angle()
        result = AngleResult(angle=angle, has_signal=False)
        kg.add_result(result)
        assert angle.id in kg.failed_approaches

    def test_get_successful_angles(self):
        """Should filter to successful angles only."""
        kg = KnowledgeGraph()
        angle1 = Angle()
        angle2 = Angle()
        kg.add_result(AngleResult(angle=angle1, has_signal=True))
        kg.add_result(AngleResult(angle=angle2, has_signal=False))

        successful = kg.get_successful_angles()
        assert len(successful) == 1
        assert successful[0].angle.id == angle1.id

    def test_coverage_by_category(self):
        """Should count angles per category."""
        kg = KnowledgeGraph()
        kg.add_angle(Angle(category=AngleCategory.TECHNICAL))
        kg.add_angle(Angle(category=AngleCategory.TECHNICAL))
        kg.add_angle(Angle(category=AngleCategory.SEMANTIC))

        coverage = kg.get_coverage_by_category()
        assert coverage[AngleCategory.TECHNICAL] == 2
        assert coverage[AngleCategory.SEMANTIC] == 1
        assert coverage[AngleCategory.INVERSE] == 0

    def test_merge(self):
        """Test merging results into knowledge graph."""
        kg = KnowledgeGraph()
        results = [
            AngleResult(angle=Angle(), has_signal=True),
            AngleResult(angle=Angle(), has_signal=False),
        ]
        kg.merge(results)
        assert len(kg.results) == 2

    def test_to_dict(self):
        """Knowledge graph should serialize to dict."""
        kg = KnowledgeGraph()
        kg.add_angle(Angle(description="Test"))
        data = kg.to_dict()
        assert "angles" in data
        assert "results" in data
        assert "discoveries" in data


class TestDefaultAngleGenerator:
    """Tests for DefaultAngleGenerator."""

    def test_generate_correct_count(self):
        """Should generate requested number of angles."""
        generator = DefaultAngleGenerator()
        kg = KnowledgeGraph()
        angles = generator.generate("Test problem", kg, count=20)
        assert len(angles) == 20

    def test_generate_covers_categories(self):
        """Should distribute angles across categories."""
        generator = DefaultAngleGenerator()
        kg = KnowledgeGraph()
        angles = generator.generate("Test problem", kg, count=24)

        categories_used = set(a.category for a in angles)
        assert len(categories_used) >= 4  # Should use multiple categories

    def test_generate_specific_categories(self):
        """Should respect category filter."""
        generator = DefaultAngleGenerator()
        kg = KnowledgeGraph()
        categories = [AngleCategory.TECHNICAL, AngleCategory.INVERSE]
        angles = generator.generate("Test problem", kg, count=10, categories=categories)

        for angle in angles:
            assert angle.category in categories

    def test_branch_on_discovery(self):
        """Should generate follow-up angles from discovery."""
        generator = DefaultAngleGenerator()
        angle = Angle(category=AngleCategory.STRUCTURAL)
        result = AngleResult(angle=angle, has_signal=True, signal_strength=0.8)

        new_angles = generator.branch_on_discovery(result, count=15)
        assert len(new_angles) == 15
        for a in new_angles:
            assert a.parent_id == angle.id


class TestDiscoveryEngine:
    """Tests for DiscoveryEngine."""

    def test_initialization(self):
        """Engine should initialize correctly."""
        engine = DiscoveryEngine()
        assert engine.state == DiscoveryState.INITIALIZED
        assert engine.knowledge is None
        assert engine.current_iteration == 0

    def test_run_with_mock_executor(self):
        """Test run with mock executor that always finds nothing."""
        def mock_executor(angle, knowledge):
            return AngleResult(angle=angle, has_signal=False)

        def mock_checker(problem, discoveries):
            return False

        engine = DiscoveryEngine(
            angle_executor=mock_executor,
            solution_checker=mock_checker,
        )
        engine.max_iterations = 2

        result = engine.run("Test problem")
        assert result["state"] == DiscoveryState.EXHAUSTED.value
        assert result["iterations"] == 2
        assert len(result["discoveries"]) == 0

    def test_run_finds_solution(self):
        """Test run that finds solution."""
        call_count = [0]

        def mock_executor(angle, knowledge):
            call_count[0] += 1
            # Find signal on 3rd call
            if call_count[0] >= 3:
                return AngleResult(angle=angle, has_signal=True, signal_strength=0.8)
            return AngleResult(angle=angle, has_signal=False)

        def mock_checker(problem, discoveries):
            return len(discoveries) >= 1

        engine = DiscoveryEngine(
            angle_executor=mock_executor,
            solution_checker=mock_checker,
        )
        engine.max_iterations = 5

        result = engine.run("Test problem")
        assert result["state"] == DiscoveryState.SOLVED.value
        assert len(result["discoveries"]) >= 1

    def test_pause_and_resume(self):
        """Test pause functionality."""
        engine = DiscoveryEngine()
        engine.max_iterations = 10

        # Request pause immediately
        engine.pause()
        assert engine._interrupt_requested

    def test_audit_log(self):
        """Test probability audit log generation."""
        def mock_executor(angle, knowledge):
            return AngleResult(angle=angle, has_signal=False)

        engine = DiscoveryEngine(angle_executor=mock_executor)
        engine.max_iterations = 2
        engine.run("Test problem")

        log = engine.get_probability_audit_log()
        assert len(log) == 2
        assert "estimated_p" in log[0]
        assert "calculated_n" in log[0]
        assert "reasoning" in log[0]


class TestAnalyzeFailurePatterns:
    """Tests for failure pattern analysis."""

    def test_analyze_all_failures(self):
        """Test analysis when all angles fail."""
        results = [
            AngleResult(angle=Angle(category=AngleCategory.TECHNICAL), has_signal=False),
            AngleResult(angle=Angle(category=AngleCategory.TECHNICAL), has_signal=False),
            AngleResult(angle=Angle(category=AngleCategory.SEMANTIC), has_signal=False),
        ]

        analysis = analyze_failure_patterns(results)
        assert analysis["total_failures"] == 3
        assert analysis["failure_rate"] == 1.0
        assert analysis["failures_by_category"]["technical"] == 2

    def test_analyze_mixed_results(self):
        """Test analysis with mixed results."""
        results = [
            AngleResult(angle=Angle(category=AngleCategory.TECHNICAL), has_signal=True),
            AngleResult(angle=Angle(category=AngleCategory.SEMANTIC), has_signal=False),
        ]

        analysis = analyze_failure_patterns(results)
        assert analysis["total_failures"] == 1
        assert analysis["failure_rate"] == 0.5

    def test_analyze_empty_results(self):
        """Test analysis with no results."""
        analysis = analyze_failure_patterns([])
        assert analysis["total_failures"] == 0
        assert analysis["failure_rate"] == 0


class TestIntegration:
    """Integration tests."""

    def test_full_discovery_flow(self):
        """Test complete discovery flow."""
        # Create a scenario where we find something after a few angles
        angle_count = [0]

        def executor(angle, knowledge):
            angle_count[0] += 1
            # 10% chance of signal
            has_signal = angle_count[0] % 10 == 0
            return AngleResult(
                angle=angle,
                has_signal=has_signal,
                signal_strength=0.7 if has_signal else 0.1,
                findings=["Found something"] if has_signal else [],
            )

        def checker(problem, discoveries):
            return len(discoveries) >= 3

        engine = DiscoveryEngine(
            angle_executor=executor,
            solution_checker=checker,
        )
        engine.max_iterations = 10

        result = engine.run(
            problem="Find the hidden pattern",
            target_confidence=0.90,
            novelty="partially_explored",
        )

        # Should have tried multiple angles
        assert result["total_angles_tried"] > 0
        # Should have knowledge accumulated
        assert result["knowledge"] is not None
        # Should have probability logs
        assert len(result["probability_logs"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
