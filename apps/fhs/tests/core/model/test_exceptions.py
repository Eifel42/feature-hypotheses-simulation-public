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
Tests for the exceptions module.

Covers FHSException, SimulationError, and ValidationError.
"""

from fhs.core.model.exceptions import FHSException, SimulationError, ValidationError


class TestExceptionsCoverage:
    """Cover FHSException.__str__ with details and SimulationError with scenarios."""

    def test_fhs_exception_str_with_details(self):
        """FHSException.__str__ with non-empty details."""
        exc = FHSException("boom", details={"key": "val", "num": 42})
        s = str(exc)
        assert "boom" in s
        assert "key=val" in s
        assert "num=42" in s

    def test_fhs_exception_str_without_details(self):
        """FHSException.__str__ without details returns message only."""
        exc = FHSException("simple error")
        assert str(exc) == "simple error"

    def test_simulation_error_with_scenarios(self):
        """SimulationError.__init__ with scenarios kwarg."""
        exc = SimulationError("sim failed", scenarios=5000)
        assert exc.details["scenarios"] == 5000
        assert "sim failed" in str(exc)

    def test_simulation_error_with_extra_kwargs(self):
        """SimulationError with additional kwargs stored in details."""
        exc = SimulationError("fail", scenarios=100, distribution="normal")
        assert exc.details["scenarios"] == 100
        assert exc.details["distribution"] == "normal"

    def test_validation_error_with_field_and_value(self):
        """ValidationError stores field and value in details."""
        exc = ValidationError("bad input", field="name", value="")
        assert exc.details["field"] == "name"
        assert exc.details["value"] == ""


class TestPortfolioOptimizationError:
    """Tests for PortfolioOptimizationError."""

    def test_portfolio_optimization_error_filters_none_values(self):
        """PortfolioOptimizationError filters out None values from details."""
        from fhs.core.model.exceptions import PortfolioOptimizationError

        exc = PortfolioOptimizationError(
            "Constraint violated", budget=100_000, constraint_type=None, extra="data"
        )
        assert exc.details["budget"] == 100_000
        assert exc.details["extra"] == "data"
        assert "constraint_type" not in exc.details


class TestConstraintViolationError:
    """Tests for ConstraintViolationError."""

    def test_constraint_violation_error_filters_none_values(self):
        """ConstraintViolationError filters out None values from details."""
        from fhs.core.model.exceptions import ConstraintViolationError

        exc = ConstraintViolationError(
            "Constraint violated", budget=100_000, constraint_type=None, extra="data"
        )
        assert exc.details["budget"] == 100_000
        assert exc.details["extra"] == "data"
        assert "constraint_type" not in exc.details
