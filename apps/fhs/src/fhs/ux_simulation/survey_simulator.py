#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
User Survey Simulator

Simulates comprehensive user surveys with realistic profiles and tasks.
"""

import numpy as np
import pandas as pd

from .models import (
    TaskComplexity,
    TaskScenario,
    UserProfile,
    UserType,
)


class UserSurveySimulator:
    """Simulates comprehensive user surveys with realistic profiles and tasks.

    Generates a pool of user profiles and task scenarios, then simulates
    task performance across all users to produce UX metrics such as
    success rate, SUS score, and support requirements.
    """

    def __init__(self, seed: int | None = None):
        """Initialise the survey simulator.

        Args:
            seed: Optional random seed for reproducible results.
        """
        self.rng = np.random.default_rng(seed)
        self.user_profiles = self._generate_realistic_profiles()
        self.task_scenarios = self._define_task_scenarios()

    def _generate_realistic_profiles(self) -> list[UserProfile]:
        """Generates realistic user profiles based on market research"""
        profiles = []

        # Farmers (40% of users)
        for i in range(20):
            profiles.append(
                UserProfile(
                    user_id=f"farmer_{i:02d}",
                    user_type=UserType.RURAL_FARMER,
                    age=int(self.rng.normal(48, 12)),  # Average age of farmers
                    tech_affinity=np.clip(self.rng.beta(2, 5), 0.1, 0.9),  # Rather low
                    education_level=np.clip(self.rng.beta(3, 2), 0.3, 0.95),
                    smartphone_usage=np.clip(self.rng.beta(3, 2), 0.4, 0.95),
                    domain_experience=np.clip(
                        self.rng.beta(5, 2), 0.6, 1.0
                    ),  # High domain expertise
                    accessibility_needs=self.rng.random() < 0.15,
                    location_type="rural",
                )
            )

        # Supply Chain Partners (30% of users)
        for i in range(15):
            profiles.append(
                UserProfile(
                    user_id=f"supply_{i:02d}",
                    user_type=UserType.SUPPLY_CHAIN,
                    age=int(self.rng.normal(38, 10)),
                    tech_affinity=np.clip(self.rng.beta(4, 2), 0.5, 0.95),  # Higher
                    education_level=np.clip(self.rng.beta(5, 2), 0.7, 1.0),
                    smartphone_usage=np.clip(self.rng.beta(6, 1.5), 0.8, 1.0),
                    domain_experience=np.clip(self.rng.beta(4, 2), 0.4, 0.9),
                    accessibility_needs=self.rng.random() < 0.10,
                    location_type="urban",
                )
            )

        # Seasonal Workers (25% of users)
        for i in range(12):
            profiles.append(
                UserProfile(
                    user_id=f"seasonal_{i:02d}",
                    user_type=UserType.SEASONAL_WORKER,
                    age=int(self.rng.normal(29, 8)),  # Younger
                    tech_affinity=np.clip(self.rng.beta(3, 3), 0.3, 0.85),
                    education_level=np.clip(self.rng.beta(2, 3), 0.2, 0.8),
                    smartphone_usage=np.clip(self.rng.beta(4, 2), 0.6, 0.95),
                    domain_experience=np.clip(self.rng.beta(2, 4), 0.1, 0.6),  # Low
                    accessibility_needs=self.rng.random() < 0.08,
                    location_type="mixed",
                )
            )

        # Tech Coordinators (5% of users)
        for i in range(3):
            profiles.append(
                UserProfile(
                    user_id=f"tech_{i:02d}",
                    user_type=UserType.TECH_COORDINATOR,
                    age=int(self.rng.normal(35, 6)),
                    tech_affinity=np.clip(self.rng.beta(6, 1), 0.8, 1.0),  # Very high
                    education_level=np.clip(self.rng.beta(5, 1), 0.8, 1.0),
                    smartphone_usage=np.clip(self.rng.beta(8, 1), 0.9, 1.0),
                    domain_experience=np.clip(self.rng.beta(3, 2), 0.5, 0.9),
                    accessibility_needs=False,
                    location_type="urban",
                )
            )

        return profiles

    @staticmethod
    def _define_task_scenarios() -> list[TaskScenario]:
        """Defines realistic task scenarios for all hypotheses"""
        return [
            # H1: User Interface Tasks
            TaskScenario(
                task_id="h1_basic_entry",
                name="Basic Data Entry",
                complexity=TaskComplexity.SIMPLE,
                target_time_seconds=25,
                max_acceptable_time=45,
                required_steps=4,
                error_probability_base=0.15,
                hypothesis_relevance="H1",
            ),
            TaskScenario(
                task_id="h1_batch_entry",
                name="Batch Data Entry",
                complexity=TaskComplexity.MEDIUM,
                target_time_seconds=120,
                max_acceptable_time=180,
                required_steps=12,
                error_probability_base=0.25,
                hypothesis_relevance="H1",
            ),
            # H2: Traceability Tasks
            TaskScenario(
                task_id="h2_track_product",
                name="Product Tracking",
                complexity=TaskComplexity.MEDIUM,
                target_time_seconds=300,  # 5 minutes target
                max_acceptable_time=480,  # 8 minutes acceptable
                required_steps=8,
                error_probability_base=0.20,
                hypothesis_relevance="H2",
            ),
            TaskScenario(
                task_id="h2_verify_chain",
                name="Verify Supply Chain",
                complexity=TaskComplexity.COMPLEX,
                target_time_seconds=600,
                max_acceptable_time=900,
                required_steps=15,
                error_probability_base=0.30,
                hypothesis_relevance="H2",
            ),
            # H3: MHD Warning Tasks
            TaskScenario(
                task_id="h3_check_warnings",
                name="Check Expiration Warnings",
                complexity=TaskComplexity.SIMPLE,
                target_time_seconds=60,
                max_acceptable_time=120,
                required_steps=3,
                error_probability_base=0.10,
                hypothesis_relevance="H3",
            ),
            TaskScenario(
                task_id="h3_configure_alerts",
                name="Configure Alert Settings",
                complexity=TaskComplexity.COMPLEX,
                target_time_seconds=180,
                max_acceptable_time=300,
                required_steps=10,
                error_probability_base=0.35,
                hypothesis_relevance="H3",
            ),
        ]

    def simulate_task_performance(
        self, user: UserProfile, task: TaskScenario, learning_iteration: int = 1
    ) -> dict:
        """Simulate task performance for a single user on a single task.

        Args:
            user: User profile to simulate.
            task: Task scenario to perform.
            learning_iteration: Repetition number (1 = first attempt).

        Returns:
            Dict with keys: user_id, task_name, completion_time, error_count,
            sus_score, task_success, and more.
        """

        # Competency-based time adjustment
        competency = user.overall_competency

        # Learning curve: improvement with repetitions
        learning_factor = 1.0 - (learning_iteration - 1) * 0.15
        learning_factor = max(0.5, learning_factor)  # Minimum 50% of original time

        # Complexity adjustment based on user type
        if isinstance(task.complexity, TaskComplexity):
            complexity_multiplier = {
                TaskComplexity.SIMPLE: 1.0,
                TaskComplexity.MEDIUM: 1.5,
                TaskComplexity.COMPLEX: 2.2,
                TaskComplexity.EXPERT: 3.0,
            }[task.complexity]
        else:
            # If complexity is a float, calculate multiplier
            # linearly between 1.0 and 3.0
            complexity_multiplier = 1.0 + (task.complexity * 2.0)

        # User type-specific adjustments
        if user.user_type == UserType.TECH_COORDINATOR:
            complexity_multiplier *= 0.7  # Tech coordinators are more efficient
        elif user.user_type == UserType.SEASONAL_WORKER:
            complexity_multiplier *= 1.3  # Seasonal workers take longer

        # Time simulation
        target_time = (
            task.target_time_seconds
            if task.target_time_seconds is not None
            else task.max_acceptable_time
        )
        base_time = target_time * learning_factor
        actual_time = base_time * complexity_multiplier / competency

        # Add realistic time variation
        time_variation = self.rng.normal(1.0, 0.2)
        actual_time *= max(0.5, time_variation)

        # Error simulation
        error_probability = (
            task.error_probability_base * (1.0 - competency) * complexity_multiplier
        )
        if user.accessibility_needs:
            error_probability *= 1.4

        error_count = self.rng.poisson(error_probability * task.required_steps)

        # SUS Score basierend auf Performance
        time_performance = min(1.0, target_time / actual_time)
        error_performance = max(0.0, 1.0 - error_count / task.required_steps)

        sus_base = 50 + (time_performance * 25) + (error_performance * 25)
        sus_score = max(0, min(100, sus_base + self.rng.normal(0, 8)))

        # Success determination
        task_success = (
            actual_time <= task.max_acceptable_time
            and error_count <= task.required_steps * 0.3
        )

        return {
            "user_id": user.user_id,
            "user_type": user.user_type.value,
            "task_id": task.task_id,
            "task_name": task.name,
            "completion_time": actual_time,
            "target_time": task.target_time_seconds,
            "error_count": error_count,
            "sus_score": sus_score,
            "task_success": task_success,
            "user_competency": competency,
            "learning_iteration": learning_iteration,
            "would_recommend": sus_score >= 70 and task_success,
            "needs_support": competency < 0.4 or error_count > 2,
            "accessibility_accommodated": user.accessibility_needs,
            "age": user.age,
        }

    def run_comprehensive_survey(
        self, hypothesis: str = "H1", learning_iterations: int = 1
    ) -> dict:
        """Run a full user survey for a hypothesis.

        Args:
            hypothesis: Hypothesis label (e.g. ``"H1"``).
            learning_iterations: How many repeated-attempt rounds to simulate.

        Returns:
            Dict with aggregated metrics: success_rate, avg_sus_score,
            recommendation_rate, accessibility results, and detailed_results.

        Raises:
            ValueError: If no tasks are defined for the given hypothesis.
        """

        relevant_tasks = [
            t for t in self.task_scenarios if t.hypothesis_relevance == hypothesis
        ]

        if not relevant_tasks:
            raise ValueError(f"No tasks defined for hypothesis {hypothesis}")

        all_results = []

        for iteration in range(1, learning_iterations + 1):
            for user in self.user_profiles:
                for task in relevant_tasks:
                    result = self.simulate_task_performance(user, task, iteration)
                    all_results.append(result)

        # Aggregated analysis via pandas
        df = pd.DataFrame(all_results)

        accessibility_mask = df["accessibility_accommodated"]
        accessibility_success = (
            float(df.loc[accessibility_mask, "task_success"].mean())
            if accessibility_mask.any()
            else 0
        )

        summary = {
            "hypothesis": hypothesis,
            "total_users": len(self.user_profiles),
            "total_tasks": len(relevant_tasks),
            "total_sessions": len(df),
            "learning_iterations": learning_iterations,
            # Performance metrics
            "success_rate": float(df["task_success"].mean()),
            "avg_completion_time": float(df["completion_time"].mean()),
            "avg_sus_score": float(df["sus_score"].mean()),
            "avg_error_count": float(df["error_count"].mean()),
            # Business metrics
            "recommendation_rate": float(df["would_recommend"].mean()),
            "support_requirement_rate": float(df["needs_support"].mean()),
            # Accessibility
            "accessibility_users": sum(
                1 for u in self.user_profiles if u.accessibility_needs
            ),
            "accessibility_success_rate": accessibility_success,
            # Detailed results
            "detailed_results": all_results,
            "user_profiles": [u.__dict__ for u in self.user_profiles],
            "task_definitions": [t.__dict__ for t in relevant_tasks],
        }

        return summary
