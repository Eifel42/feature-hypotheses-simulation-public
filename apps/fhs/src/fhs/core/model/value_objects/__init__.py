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

"""Domain Value Objects: immutable, identity-less domain concepts."""

from .advisor import (
    BudgetRiskRow,
    FeatureRanking,
    FeatureRankingRow,
    NegativeScoreComparisonRow,
    NegativeScoreFeature,
    NegativeScoreReport,
    StrategyCategoryCostRow,
)
from .beta_parameters import BetaParameters
from .budget import Budget
from .budget_check import BudgetCheckResult, FeatureBudgetCheckRow
from .budget_frontier import BudgetFrontierRow
from .case_study import FeatureYear1Result
from .component_risk import ClusterRisk, ComponentRiskResult
from .concentration import ConcentrationResult
from .confidence_level import ConfidenceLevel
from .executive_decision import (
    DecisionDimension,
    ExecutiveDecisionResult,
    ScenarioComparison,
    aggregate_decision_signals,
)
from .feature_ranking_metrics import FeatureRankingMetrics
from .financial_view import (
    FinancialViewResult,
    IrrAssessment,
    IrrSummary,
    NpvAssessment,
    NpvSummary,
)
from .governance import (
    AssumptionConfidence,
    AssumptionMetadata,
    AssumptionStatus,
    DecisionGrade,
    DecisionPolicy,
    DecisionPolicyResult,
    ModelCard,
    RiskAppetitePolicy,
)
from .loss_profile import LossMetrics, LossProfile
from .multi_year_pnl import (
    MultiYearLayer,
    MultiYearLayerYear,
    MultiYearPnLMeta,
    MultiYearPnLResult,
    MultiYearRiskProbabilities,
)
from .multi_year_result import MultiYearResult, YearResult
from .operating_cost import FeatureOperatingCostStats, OperatingCostResult
from .optimization_result import OptimizationResult
from .optimization_strategy import OptimizationStrategy
from .pnl_assessment import PnLAssessment
from .portfolio_analysis import (
    CorrelationPair,
    CorrelationResult,
    CorrelationStatistics,
    DiversificationMetrics,
    IndividualRiskMetrics,
    PortfolioMetrics,
    PortfolioRiskResult,
    RiskContributionResult,
)
from .portfolio_pl import PLVariantRow, PortfolioPLVariants
from .portfolio_snapshot import PortfolioSnapshot
from .risk_layer_stats import (
    DeliveryStressResult,
    FeatureRiskProfile,
    PortfolioPnLLayers,
    PortfolioRiskLayers,
    PortfolioRiskMeta,
    RetentionMatrix,
    RetentionRow,
    RiskHitRates,
    RiskLayerStats,
    RiskManagementROI,
    RiskProbabilities,
    WaterfallRow,
    WaterfallSummary,
)
from .risk_metric import RiskMetric
from .risk_simulation_state import RiskSimulationState
from .sensitivity import (
    FeatureSensitivityResult,
    PortfolioSensitivityRow,
    SensitivityDetail,
    SensitivityDriver,
    TornadoRow,
)
from .shapley import (
    RiskFactorContribution,
    RiskFactorShapley,
    ShapleyAttribution,
    ShapleyContribution,
)
from .simulation_result import SimulationResult
from .sprint_delivery import (
    DeliverySimulationResult,
    PortfolioProfitabilityResult,
    ProfitabilityResult,
    SprintPlan,
)

__all__ = [
    "AssumptionConfidence",
    "AssumptionMetadata",
    "AssumptionStatus",
    "BetaParameters",
    "Budget",
    "BudgetCheckResult",
    "BudgetFrontierRow",
    "BudgetRiskRow",
    "ClusterRisk",
    "ComponentRiskResult",
    "ConcentrationResult",
    "ConfidenceLevel",
    "CorrelationPair",
    "CorrelationResult",
    "CorrelationStatistics",
    "DecisionDimension",
    "DecisionGrade",
    "DecisionPolicy",
    "DecisionPolicyResult",
    "DeliverySimulationResult",
    "DeliveryStressResult",
    "DiversificationMetrics",
    "ExecutiveDecisionResult",
    "FeatureBudgetCheckRow",
    "FeatureOperatingCostStats",
    "FeatureRanking",
    "FeatureRankingMetrics",
    "FeatureRankingRow",
    "FeatureRiskProfile",
    "FeatureSensitivityResult",
    "FeatureYear1Result",
    "FinancialViewResult",
    "IndividualRiskMetrics",
    "IrrAssessment",
    "IrrSummary",
    "LossMetrics",
    "LossProfile",
    "ModelCard",
    "MultiYearLayer",
    "MultiYearLayerYear",
    "MultiYearPnLMeta",
    "MultiYearPnLResult",
    "MultiYearResult",
    "MultiYearRiskProbabilities",
    "NegativeScoreComparisonRow",
    "NegativeScoreFeature",
    "NegativeScoreReport",
    "NpvAssessment",
    "NpvSummary",
    "OperatingCostResult",
    "OptimizationResult",
    "OptimizationStrategy",
    "PLVariantRow",
    "PnLAssessment",
    "PortfolioMetrics",
    "PortfolioPLVariants",
    "PortfolioPnLLayers",
    "PortfolioProfitabilityResult",
    "PortfolioRiskLayers",
    "PortfolioRiskMeta",
    "PortfolioRiskResult",
    "PortfolioSensitivityRow",
    "PortfolioSnapshot",
    "ProfitabilityResult",
    "RetentionMatrix",
    "RetentionRow",
    "RiskAppetitePolicy",
    "RiskContributionResult",
    "RiskFactorContribution",
    "RiskFactorShapley",
    "RiskHitRates",
    "RiskLayerStats",
    "RiskManagementROI",
    "RiskMetric",
    "RiskProbabilities",
    "RiskSimulationState",
    "ScenarioComparison",
    "SensitivityDetail",
    "SensitivityDriver",
    "ShapleyAttribution",
    "ShapleyContribution",
    "SimulationResult",
    "SprintPlan",
    "StrategyCategoryCostRow",
    "TornadoRow",
    "WaterfallRow",
    "WaterfallSummary",
    "YearResult",
    "aggregate_decision_signals",
]
