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
UX Simulation Domain Models

User profiles, task scenarios, and related enumerations for UX simulation.
"""

from enum import Enum
from typing import Any

import numpy as np


class UserType(Enum):
    """Enumeration of user archetypes for UX simulation."""

    RURAL_FARMER = "rural_farmer"
    SUPPLY_CHAIN = "supply_chain"
    SEASONAL_WORKER = "seasonal_worker"
    TECH_COORDINATOR = "tech_coordinator"
    MANAGEMENT = "management"


class TaskComplexity(Enum):
    """Task complexity levels used by :class:`TaskScenario`."""

    SIMPLE = "simple"  # Basic functions
    MEDIUM = "medium"  # Multi-step workflows
    COMPLEX = "complex"  # Advanced features
    EXPERT = "expert"  # Administrative tasks


class UserProfile:
    """User profile capturing demographics, skills, and accessibility needs.

    Used by :class:`UserSurveySimulator` and :class:`UXSimulator` to
    generate realistic task-performance predictions.
    """

    def __init__(
        self,
        user_id: str | None = None,
        name: str | None = None,
        user_type: UserType | None = None,
        age: int = 30,
        tech_affinity: float | None = None,
        tech_savviness: float | None = None,
        education_level: float = 0.5,
        smartphone_usage: float = 0.5,
        domain_experience: float = 0.5,
        experience_level: str | None = None,
        accessibility_needs: bool | list[Any] | dict[str, float] | None = None,
        primary_language: str = "deutsch",
        location_type: str = "rural",
    ):
        """
        Initialize user profile with flexible parameters
        to support different test patterns

        Args:
            user_id: User identifier (alternative to name)
            name: User name (alternative to user_id)
            user_type: Type of user (enum)
            age: User age
            tech_affinity: Technical affinity score (0-1)
            tech_savviness: Alternative name for tech_affinity (0-1)
            education_level: Education level score (0-1)
            smartphone_usage: Smartphone usage score (0-1)
            domain_experience: Domain experience score (0-1)
            experience_level: Alternative name for domain_experience (0-1)
            accessibility_needs: Accessibility requirements (bool or list)
            primary_language: Primary language
            location_type: Location type (rural/urban)
        """
        # Handle name/user_id duality
        self.user_id = user_id or name or "user"
        self.name = name or user_id or "user"

        # Handle tech_affinity/tech_savviness duality
        self.tech_affinity = (
            tech_affinity if tech_affinity is not None else (tech_savviness or 0.5)
        )
        self.tech_savviness = self.tech_affinity

        # Handle domain_experience/experience_level duality
        self.domain_experience = (
            domain_experience
            if domain_experience is not None
            else (experience_level or 0.5)
        )
        self.experience_level = self.domain_experience

        # Handle accessibility_needs variations (bool or list)
        self.accessibility_needs: bool
        self.accessibility_list: list[Any]
        if isinstance(accessibility_needs, list):
            self.accessibility_needs = len(accessibility_needs) > 0
            self.accessibility_list = accessibility_needs
        else:
            self.accessibility_needs = bool(accessibility_needs)
            self.accessibility_list = (
                [] if not self.accessibility_needs else ["generic"]
            )

        # Set other attributes
        self.user_type = user_type or UserType.RURAL_FARMER
        self.age = age
        self.education_level = education_level
        self.smartphone_usage = smartphone_usage
        self.primary_language = primary_language
        self.location_type = location_type

    @property
    def overall_competency(self) -> float:
        """Calculates overall competency for UX predictions"""
        age_factor = max(0.3, 1.0 - (self.age - 25) * 0.01)  # Gentle age decline

        competency = (
            self.tech_affinity * 0.4
            + self.education_level * 0.2
            + self.smartphone_usage * 0.25
            + self.domain_experience * 0.15
        ) * age_factor

        # Accessibility adjustment
        if self.accessibility_needs:
            competency *= 0.85

        return float(np.clip(competency, 0.1, 1.0))


class TaskScenario:
    """Concrete task scenario for user testing.

    Encapsulates task metadata (complexity, timing, error rates) used by
    the survey and UX simulators to measure task performance.
    """

    def __init__(
        self,
        name: str,
        complexity: float | TaskComplexity,
        task_id: str | None = None,
        target_time_seconds: int | None = None,
        required_experience: float | None = None,
        accessibility_impact: dict[str, float] | None = None,
        max_acceptable_time: int = 120,
        required_steps: int = 5,
        error_probability_base: float = 0.1,
        hypothesis_relevance: str = "H1",
    ):
        """
        Initialize task scenario

        Args:
            name: Task name
            complexity: Complexity level (0.0-1.0) or TaskComplexity enum
            task_id: Optional task identifier
            target_time_seconds: Target completion time in seconds
            required_experience: Experience level required (0.0-1.0)
            accessibility_impact: Impact on users with accessibility needs
            max_acceptable_time: Maximum time in seconds
            required_steps: Number of steps to complete
            error_probability_base: Base probability of errors
            hypothesis_relevance: Which hypothesis this task validates
        """
        # Handle complexity parameter - can be float or TaskComplexity enum
        if isinstance(complexity, TaskComplexity):
            complexity_value = {
                TaskComplexity.SIMPLE: 0.2,
                TaskComplexity.MEDIUM: 0.5,
                TaskComplexity.COMPLEX: 0.8,
                TaskComplexity.EXPERT: 1.0,
            }[complexity]
        else:
            complexity_value = complexity

        if complexity_value < 0 or complexity_value > 1:
            raise ValueError("Complexity must be between 0 and 1")

        if required_experience is not None and (
            required_experience < 0 or required_experience > 1
        ):
            raise ValueError("Required experience must be between 0 and 1")

        self.name = name
        self.task_id = task_id
        self.complexity = complexity_value
        self.target_time_seconds = target_time_seconds
        self.required_experience = (
            complexity_value * 0.8
            if required_experience is None
            else required_experience
        )
        self.max_acceptable_time = max_acceptable_time
        self.required_steps = required_steps
        self.error_probability_base = error_probability_base
        self.hypothesis_relevance = hypothesis_relevance
        self.accessibility_impact = accessibility_impact or {}
