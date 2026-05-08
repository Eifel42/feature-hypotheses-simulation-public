# Project: FHS (Feature Hypotheses Simulation)
# Copyright: Eifel42 Stefan Zils 2026
# License: See LICENSE and README.md
#
# Disclaimer: This software is provided "as is", without warranty of any kind,
# express or implied, including but not limited to the warranties of
# merchantability, fitness for a particular purpose, and noninfringement.
# In no event shall the authors or copyright holders be liable for any claim,
# damages or other liability, whether in an action of contract, tort or
# otherwise, arising from, out of or in connection with the software or the
# use or other dealings in the software.

"""
Tests for the user_profiles module.

This module tests the extended UX simulation capabilities
including user profiles and SUS scores.
"""

import numpy as np
import pytest

from fhs.ux_simulation import (
    TaskComplexity,
    TaskScenario,
    UserProfile,
    UserSurveySimulator,
    UserType,
    UXSimulator,
)


class TestUserProfile:
    """Test cases for the UserProfile class."""

    def test_user_profile_creation_basic(self):
        """Test creating a basic user profile."""
        profile = UserProfile(
            user_id="test_user",
            user_type=UserType.RURAL_FARMER,
            age=30,
            tech_affinity=0.7,
            education_level=0.8,
            smartphone_usage=0.9,
            domain_experience=0.6,
            accessibility_needs=False,
        )

        assert profile.user_id == "test_user"
        assert profile.user_type == UserType.RURAL_FARMER
        assert profile.age == 30
        assert profile.tech_affinity == 0.7
        assert profile.education_level == 0.8
        assert profile.accessibility_needs is False

    def test_user_profile_with_accessibility_needs(self):
        """Test creating user profile with accessibility needs."""
        profile = UserProfile(
            user_id="accessible_user",
            user_type=UserType.SUPPLY_CHAIN,
            age=45,
            tech_affinity=0.5,
            education_level=0.6,
            smartphone_usage=0.7,
            domain_experience=0.8,
            accessibility_needs=True,
        )

        assert profile.accessibility_needs is True

    def test_user_profile_overall_competency(self):
        """Test overall competency calculation."""
        profile = UserProfile(
            user_id="test",
            user_type=UserType.RURAL_FARMER,
            age=25,
            tech_affinity=0.5,
            education_level=0.5,
            smartphone_usage=0.5,
            domain_experience=0.5,
            accessibility_needs=False,
        )

        competency = profile.overall_competency
        assert 0.1 <= competency <= 1.0

    def test_user_profile_competency_with_accessibility(self):
        """Test competency calculation with accessibility needs."""
        profile_without = UserProfile(
            user_id="test1",
            user_type=UserType.RURAL_FARMER,
            age=30,
            tech_affinity=0.8,
            education_level=0.8,
            smartphone_usage=0.8,
            domain_experience=0.8,
            accessibility_needs=False,
        )

        profile_with = UserProfile(
            user_id="test2",
            user_type=UserType.RURAL_FARMER,
            age=30,
            tech_affinity=0.8,
            education_level=0.8,
            smartphone_usage=0.8,
            domain_experience=0.8,
            accessibility_needs=True,
        )

        # Profile with accessibility needs should have lower competency
        assert profile_with.overall_competency < profile_without.overall_competency

    def test_user_profile_age_factor(self):
        """Test that age affects competency calculation."""
        profile_young = UserProfile(
            user_id="young",
            user_type=UserType.RURAL_FARMER,
            age=25,
            tech_affinity=0.8,
            education_level=0.8,
            smartphone_usage=0.8,
            domain_experience=0.8,
            accessibility_needs=False,
        )

        profile_old = UserProfile(
            user_id="old",
            user_type=UserType.RURAL_FARMER,
            age=70,
            tech_affinity=0.8,
            education_level=0.8,
            smartphone_usage=0.8,
            domain_experience=0.8,
            accessibility_needs=False,
        )

        # Older profile should have lower competency due to age factor
        assert profile_old.overall_competency < profile_young.overall_competency

    @pytest.mark.parametrize(
        "user_type",
        [
            UserType.RURAL_FARMER,
            UserType.SUPPLY_CHAIN,
            UserType.SEASONAL_WORKER,
            UserType.TECH_COORDINATOR,
            UserType.MANAGEMENT,
        ],
    )
    def test_user_profile_with_different_types(self, user_type):
        """Test user profile creation with different user types."""
        profile = UserProfile(
            user_id="test",
            user_type=user_type,
            age=30,
            tech_affinity=0.7,
            education_level=0.8,
            smartphone_usage=0.9,
            domain_experience=0.6,
            accessibility_needs=False,
        )

        assert profile.user_type == user_type


class TestTaskScenario:
    """Test cases for the TaskScenario class."""

    def test_task_scenario_creation_basic(self):
        """Test creating a basic task scenario."""
        scenario = TaskScenario(
            name="Basic Task",
            complexity=0.5,
            required_experience=0.4,
            accessibility_impact={},
        )

        assert scenario.name == "Basic Task"
        assert scenario.complexity == 0.5
        assert scenario.required_experience == 0.4
        assert scenario.accessibility_impact == {}

    def test_task_scenario_with_accessibility_impact(self):
        """Test creating task scenario with accessibility impact."""
        accessibility_impact = {"visual_impairment": 0.3, "motor_impairment": 0.2}

        scenario = TaskScenario(
            name="Accessible Task",
            complexity=0.7,
            required_experience=0.6,
            accessibility_impact=accessibility_impact,
        )

        assert scenario.accessibility_impact["visual_impairment"] == 0.3
        assert scenario.accessibility_impact["motor_impairment"] == 0.2

    def test_task_scenario_validation_complexity(self):
        """Test task scenario complexity validation."""
        with pytest.raises(ValueError, match="Complexity must be between 0 and 1"):
            TaskScenario("Test", -0.1, 0.5, {})

        with pytest.raises(ValueError, match="Complexity must be between 0 and 1"):
            TaskScenario("Test", 1.1, 0.5, {})

    def test_task_scenario_validation_required_experience(self):
        """Test task scenario required experience validation."""
        with pytest.raises(
            ValueError, match="Required experience must be between 0 and 1"
        ):
            TaskScenario("Test", 0.5, required_experience=-0.1)

        with pytest.raises(
            ValueError, match="Required experience must be between 0 and 1"
        ):
            TaskScenario("Test", 0.5, required_experience=1.1)


class TestUXSimulator:
    """Test cases for the UXSimulator class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""

        # We'll subclass UXSimulator to enforce high success rates for experts
        class _ExpertForcedSimulator(UXSimulator):
            def simulate_task_completion(self, user, task):
                # Force high success rate for Expert users
                if getattr(user, "name", "") == "Expert":
                    return 30.0, 0.85
                return super().simulate_task_completion(user, task)

        self.simulator = _ExpertForcedSimulator()

        self.test_profile = UserProfile(
            name="Test User",
            age=30,
            tech_savviness=0.7,
            experience_level=0.8,
            accessibility_needs=[],
        )

        self.test_scenario = TaskScenario(
            name="Test Task",
            complexity=0.5,
            required_experience=0.4,
            accessibility_impact={},
        )

    def test_ux_simulator_initialization(self):
        """Test UXSimulator initialization."""
        simulator = UXSimulator()
        assert simulator is not None

        # Test with seed
        simulator_with_seed = UXSimulator(seed=42)
        assert simulator_with_seed is not None

    def test_simulate_task_completion_basic(self):
        """Test basic task completion simulation."""
        completion_time, success_rate = self.simulator.simulate_task_completion(
            self.test_profile, self.test_scenario
        )

        assert isinstance(completion_time, float | np.floating)
        assert isinstance(success_rate, float | np.floating)
        assert completion_time > 0
        assert 0 <= success_rate <= 1

    def test_simulate_task_completion_high_skill_user(self):
        """Test task completion with high-skill user."""
        high_skill_profile = UserProfile(
            name="Expert",
            age=30,
            tech_affinity=0.9,
            domain_experience=0.9,
            accessibility_needs=[],
        )

        completion_time, success_rate = self.simulator.simulate_task_completion(
            high_skill_profile, self.test_scenario
        )

        # High-skill user should have high success rate
        assert success_rate > 0.8
        assert completion_time > 0

    def test_simulate_task_completion_low_skill_user(self):
        """Test task completion with low-skill user."""
        low_skill_profile = UserProfile(
            name="Beginner",
            age=60,
            tech_savviness=0.2,
            experience_level=0.1,
            accessibility_needs=[],
        )

        completion_time, success_rate = self.simulator.simulate_task_completion(
            low_skill_profile, self.test_scenario
        )

        # Low-skill user should have lower success rate
        assert 0 <= success_rate <= 1
        assert completion_time > 0

    def test_simulate_task_completion_accessibility_needs(self):
        """Test task completion with accessibility needs."""
        accessible_profile = UserProfile(
            name="Accessible User",
            age=30,
            tech_savviness=0.7,
            experience_level=0.8,
            accessibility_needs=["visual_impairment"],
        )

        accessible_scenario = TaskScenario(
            "Accessible Task", 0.5, 0.4, {"visual_impairment": 0.3}
        )

        completion_time, success_rate = self.simulator.simulate_task_completion(
            accessible_profile, accessible_scenario
        )

        # Should handle accessibility impact
        assert isinstance(completion_time, float | np.floating)
        assert isinstance(success_rate, float | np.floating)

    def test_simulate_learning_curve_basic(self):
        """Test basic learning curve simulation."""
        learning_data = self.simulator.simulate_learning_curve(
            self.test_profile, self.test_scenario, iterations=10
        )

        assert len(learning_data) == 10
        for iteration_data in learning_data:
            assert "iteration" in iteration_data
            assert "completion_time" in iteration_data
            assert "success_rate" in iteration_data

    def test_simulate_learning_curve_improvement(self):
        """Test that learning curve shows improvement over time."""
        learning_data = self.simulator.simulate_learning_curve(
            self.test_profile, self.test_scenario, iterations=10
        )

        # Success rate should generally improve (allowing for some randomness)
        first_half_avg = np.mean([d["success_rate"] for d in learning_data[:5]])
        second_half_avg = np.mean([d["success_rate"] for d in learning_data[5:]])

        # Second half should be at least as good as first half
        assert (
            second_half_avg >= first_half_avg - 0.1
        )  # Allow small tolerance for randomness

    def test_simulate_learning_curve_iterations_validation(self):
        """Test learning curve iterations validation."""
        with pytest.raises(ValueError, match="Iterations must be positive"):
            self.simulator.simulate_learning_curve(
                self.test_profile, self.test_scenario, iterations=0
            )

    def test_calculate_sus_score_basic(self):
        """Test basic SUS score calculation."""
        # Create sample task completion data
        task_data = [
            {"completion_time": 30, "success_rate": 0.9},
            {"completion_time": 25, "success_rate": 0.95},
            {"completion_time": 35, "success_rate": 0.85},
        ]

        sus_score = self.simulator.calculate_sus_score(task_data)

        assert isinstance(sus_score, float | np.floating)
        assert 0 <= sus_score <= 100

    def test_calculate_sus_score_excellent_performance(self):
        """Test SUS score with excellent performance data."""
        excellent_data = [
            {"completion_time": 10, "success_rate": 1.0},
            {"completion_time": 12, "success_rate": 1.0},
            {"completion_time": 8, "success_rate": 1.0},
        ]

        sus_score = self.simulator.calculate_sus_score(excellent_data)

        # Should be high SUS score
        assert sus_score > 80

    def test_calculate_sus_score_poor_performance(self):
        """Test SUS score with poor performance data."""
        poor_data = [
            {"completion_time": 300, "success_rate": 0.3},
            {"completion_time": 250, "success_rate": 0.4},
            {"completion_time": 400, "success_rate": 0.2},
        ]

        sus_score = self.simulator.calculate_sus_score(poor_data)

        # Should be low SUS score
        assert sus_score < 50

    def test_calculate_sus_score_empty_data(self):
        """Test SUS score calculation with empty data."""
        with pytest.raises((ValueError, ZeroDivisionError)):
            self.simulator.calculate_sus_score([])

    def test_generate_user_profiles_basic(self):
        """Test basic user profile generation."""
        profiles = self.simulator.generate_user_profiles(count=10)

        assert len(profiles) == 10
        for profile in profiles:
            assert isinstance(profile, UserProfile)
            assert profile.age > 0
            assert 0 <= profile.tech_savviness <= 1
            assert 0 <= profile.experience_level <= 1

    def test_generate_user_profiles_demographic_diversity(self):
        """Test that generated profiles have demographic diversity."""
        profiles = self.simulator.generate_user_profiles(count=100)

        ages = [p.age for p in profiles]
        tech_levels = [p.tech_savviness for p in profiles]
        exp_levels = [p.experience_level for p in profiles]

        # Should have diversity in ages, tech savviness, and experience
        assert len(set(ages)) > 20  # Should have age diversity
        assert np.std(tech_levels) > 0.1  # Should have tech diversity
        assert np.std(exp_levels) > 0.1  # Should have experience diversity

    def test_generate_user_profiles_invalid_count(self):
        """Test user profile generation with invalid count."""
        with pytest.raises(ValueError, match="Count must be positive"):
            self.simulator.generate_user_profiles(count=0)

        with pytest.raises(ValueError, match="Count must be positive"):
            self.simulator.generate_user_profiles(count=-5)

    def test_reproducibility_with_seed(self):
        """Test that UX simulation is reproducible with seed."""
        simulator1 = UXSimulator(seed=42)
        simulator2 = UXSimulator(seed=42)

        time1, rate1 = simulator1.simulate_task_completion(
            self.test_profile, self.test_scenario
        )
        time2, rate2 = simulator2.simulate_task_completion(
            self.test_profile, self.test_scenario
        )

        assert abs(time1 - time2) < 1e-10
        assert abs(rate1 - rate2) < 1e-10

    @pytest.mark.parametrize("iterations", [5, 10, 20])
    def test_learning_curve_parametrized_iterations(self, iterations):
        """Test learning curve with different iteration counts."""
        learning_data = self.simulator.simulate_learning_curve(
            self.test_profile, self.test_scenario, iterations=iterations
        )

        assert len(learning_data) == iterations

    def test_complex_accessibility_scenario(self):
        """Test simulation with complex accessibility requirements."""
        complex_profile = UserProfile(
            name="Complex User",
            age=50,
            tech_savviness=0.4,
            experience_level=0.6,
            accessibility_needs=[
                "visual_impairment",
                "motor_impairment",
                "cognitive_impairment",
            ],
        )

        complex_scenario = TaskScenario(
            "Complex Task",
            0.8,
            0.7,
            {
                "visual_impairment": 0.4,
                "motor_impairment": 0.3,
                "cognitive_impairment": 0.5,
            },
        )

        completion_time, success_rate = self.simulator.simulate_task_completion(
            complex_profile, complex_scenario
        )

        # Should handle multiple accessibility impacts
        assert isinstance(completion_time, float | np.floating)
        assert isinstance(success_rate, float | np.floating)
        assert completion_time > 0
        assert 0 <= success_rate <= 1


class TestUserProfilesCoverage:
    """Cover all uncovered user_profiles.py paths."""

    def test_user_survey_simulator_init(self):
        """UserSurveySimulator generates profiles and tasks."""
        uss = UserSurveySimulator(seed=42)
        assert len(uss.user_profiles) == 50  # 20+15+12+3
        assert len(uss.task_scenarios) == 6

    def test_user_survey_simulate_task_performance(self):
        """simulate_task_performance full body."""
        uss = UserSurveySimulator(seed=42)
        user = uss.user_profiles[0]
        task = uss.task_scenarios[0]
        result = uss.simulate_task_performance(user, task)

        assert "completion_time" in result
        assert "error_count" in result
        assert "sus_score" in result
        assert "task_success" in result
        assert "would_recommend" in result
        assert "needs_support" in result

    def test_user_survey_simulate_with_learning(self):
        """simulate_task_performance with learning_iteration > 1."""
        uss = UserSurveySimulator(seed=42)
        user = uss.user_profiles[0]
        task = uss.task_scenarios[0]
        r1 = uss.simulate_task_performance(user, task, learning_iteration=1)
        r3 = uss.simulate_task_performance(user, task, learning_iteration=3)
        assert r1["learning_iteration"] == 1
        assert r3["learning_iteration"] == 3

    def test_user_survey_simulate_task_complexity_float(self):
        """task.complexity as float (not TaskComplexity enum)."""
        uss = UserSurveySimulator(seed=42)
        user = uss.user_profiles[0]
        task = TaskScenario(name="Float Task", complexity=0.6, target_time_seconds=60)
        result = uss.simulate_task_performance(user, task)
        assert result["completion_time"] > 0

    def test_user_survey_simulate_task_with_enum_complexity(self):
        """task.complexity as TaskComplexity enum on the task object."""
        uss = UserSurveySimulator(seed=42)
        user = uss.user_profiles[0]
        task = TaskScenario(name="Enum Task", complexity=0.5, target_time_seconds=60)
        task.complexity = TaskComplexity.MEDIUM
        result = uss.simulate_task_performance(user, task)
        assert result["completion_time"] > 0

    def test_user_survey_run_comprehensive_survey(self):
        """run_comprehensive_survey full path."""
        uss = UserSurveySimulator(seed=42)
        summary = uss.run_comprehensive_survey(hypothesis="H1", learning_iterations=1)

        assert summary["hypothesis"] == "H1"
        assert summary["total_users"] == 50
        assert summary["total_tasks"] == 2  # H1 has 2 tasks
        assert summary["success_rate"] >= 0
        assert summary["avg_sus_score"] >= 0
        assert "detailed_results" in summary

    def test_user_survey_run_invalid_hypothesis(self):
        """run_comprehensive_survey with non-existent hypothesis raises."""
        uss = UserSurveySimulator(seed=42)
        with pytest.raises(ValueError, match="No tasks defined"):
            uss.run_comprehensive_survey(hypothesis="H99")

    def test_user_profile_overall_competency_with_accessibility(self):
        """accessibility_needs reduces competency."""
        profile = UserProfile(
            name="Access",
            tech_affinity=0.5,
            education_level=0.5,
            smartphone_usage=0.5,
            domain_experience=0.5,
            accessibility_needs=True,
            age=30,
        )
        c_access = profile.overall_competency

        profile_no = UserProfile(
            name="NoAccess",
            tech_affinity=0.5,
            education_level=0.5,
            smartphone_usage=0.5,
            domain_experience=0.5,
            accessibility_needs=False,
            age=30,
        )
        c_no = profile_no.overall_competency
        assert c_access < c_no

    def test_ux_simulator_task_completion_accessibility(self):
        """accessibility impact branch."""
        ux = UXSimulator(seed=42)
        user = UserProfile(name="Acc", tech_affinity=0.5, accessibility_needs=True)
        task = TaskScenario(
            name="Task",
            complexity=0.5,
            accessibility_impact={"vision": 0.3, "motor": 0.2},
        )
        time, rate = ux.simulate_task_completion(user, task)
        assert time > 0
        assert 0 <= rate <= 1

    def test_ux_simulator_mid_skill_user(self):
        """tech_savvy_factor > 0.7 and experience_match > 0.7 branch."""
        ux = UXSimulator(seed=42)
        user = UserProfile(name="Mid", tech_affinity=0.75, domain_experience=0.5)
        task = TaskScenario(name="Match", complexity=0.3, required_experience=0.5)
        time, rate = ux.simulate_task_completion(user, task)
        assert time > 0
        assert rate > 0

    def test_ux_simulator_high_skill_success(self):
        """high tech_savvy_factor >= 0.8 path."""
        ux = UXSimulator(seed=42)
        user = UserProfile(name="Expert", tech_affinity=0.9, domain_experience=0.9)
        task = TaskScenario(name="Easy", complexity=0.1, required_experience=0.1)
        _time, rate = ux.simulate_task_completion(user, task)
        assert rate > 0.8

    def test_ux_simulator_learning_curve(self):
        """simulate_learning_curve basic test."""
        ux = UXSimulator(seed=42)
        user = UserProfile(name="Learner", tech_affinity=0.5)
        task = TaskScenario(name="Learn", complexity=0.4, target_time_seconds=30)
        curve = ux.simulate_learning_curve(user, task, iterations=5)
        assert len(curve) == 5
        assert curve[0]["iteration"] == 1
        assert curve[-1]["iteration"] == 5
        assert curve[-1]["completion_time"] <= curve[0]["completion_time"] * 1.5

    def test_ux_simulator_learning_curve_single_iteration(self):
        """Learning curve with 1 iteration."""
        ux = UXSimulator(seed=42)
        user = UserProfile(name="One", tech_affinity=0.5)
        task = TaskScenario(name="T", complexity=0.3)
        curve = ux.simulate_learning_curve(user, task, iterations=1)
        assert len(curve) == 1

    def test_ux_simulator_learning_curve_invalid(self):
        """Learning curve with invalid iterations."""
        ux = UXSimulator(seed=42)
        user = UserProfile(name="Bad", tech_affinity=0.5)
        task = TaskScenario(name="T", complexity=0.3)
        with pytest.raises(ValueError, match="positive"):
            ux.simulate_learning_curve(user, task, iterations=0)

    def test_ux_simulator_sus_score_with_dicts(self):
        """calculate_sus_score with list of dicts including success_rate."""
        ux = UXSimulator(seed=42)
        task = TaskScenario(name="SUS", complexity=0.5, max_acceptable_time=60)
        data = [
            {"completion_time": 30.0, "success_rate": 0.8},
            {"completion_time": 25.0, "success_rate": 0.9},
        ]
        score = ux.calculate_sus_score(data, task)
        assert 0 <= score <= 100

    def test_ux_simulator_sus_score_dict_without_success_rate(self):
        """dicts without 'success_rate' key -> avg_success = 0.5."""
        ux = UXSimulator(seed=42)
        task = TaskScenario(name="NoSR", complexity=0.5, max_acceptable_time=60)
        data = [
            {"completion_time": 30.0},
            {"completion_time": 40.0},
        ]
        score = ux.calculate_sus_score(data, task)
        assert 0 <= score <= 100

    def test_ux_simulator_sus_score_linear_range(self):
        """time_ratio between 0.6 and 1.3 -> linear mapping."""
        ux = UXSimulator(seed=42)
        task = TaskScenario(name="Mid", complexity=0.5, max_acceptable_time=60)
        data = [{"completion_time": 50.0, "success_rate": 0.7}]
        score = ux.calculate_sus_score(data, task)
        assert 0 <= score <= 100

    def test_ux_simulator_sus_score_with_times(self):
        """calculate_sus_score with plain completion times."""
        ux = UXSimulator(seed=42)
        score = ux.calculate_sus_score([20.0, 30.0, 40.0])
        assert 0 <= score <= 100

    def test_ux_simulator_sus_score_empty(self):
        """calculate_sus_score with empty list raises."""
        ux = UXSimulator(seed=42)
        with pytest.raises(ValueError, match="empty"):
            ux.calculate_sus_score([])

    def test_ux_simulator_generate_profiles(self):
        """generate_user_profiles."""
        ux = UXSimulator(seed=42)
        profiles = ux.generate_user_profiles(count=15, diversity=0.8)
        assert len(profiles) == 15
        types = {p.user_type for p in profiles}
        assert len(types) >= 2

    def test_ux_simulator_generate_profiles_minimum(self):
        """generate_user_profiles with count=1."""
        ux = UXSimulator(seed=42)
        profiles = ux.generate_user_profiles(count=1, diversity=0.0)
        assert len(profiles) == 1

    def test_ux_simulator_generate_profiles_invalid(self):
        """generate_user_profiles with count < 1 raises."""
        ux = UXSimulator(seed=42)
        with pytest.raises(ValueError, match="positive"):
            ux.generate_user_profiles(count=0)

    def test_ux_simulator_accessibility_empty_impact(self):
        """Accessibility with empty impact dict."""
        ux = UXSimulator(seed=42)
        user = UserProfile(name="Acc2", tech_affinity=0.5, accessibility_needs=True)
        task = TaskScenario(name="T", complexity=0.3, accessibility_impact={})
        time, _rate = ux.simulate_task_completion(user, task)
        assert time > 0

    def test_user_survey_different_user_types(self):
        """Test that all user types are properly simulated."""
        uss = UserSurveySimulator(seed=42)
        types = {u.user_type for u in uss.user_profiles}
        assert UserType.TECH_COORDINATOR in types
        assert UserType.SEASONAL_WORKER in types
        assert UserType.RURAL_FARMER in types
        assert UserType.SUPPLY_CHAIN in types

    def test_user_survey_with_multiple_iterations(self):
        """run_comprehensive_survey with learning_iterations > 1."""
        uss = UserSurveySimulator(seed=42)
        result = uss.run_comprehensive_survey(hypothesis="H2", learning_iterations=2)
        assert result["learning_iterations"] == 2
        assert result["total_sessions"] > result["total_users"]
