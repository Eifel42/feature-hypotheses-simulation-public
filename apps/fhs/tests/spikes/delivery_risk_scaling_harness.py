#!/usr/bin/env python3
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

"""Benchmark harness for delivery risk simulation scaling.

This script measures runtime and Python-heap peak memory for
`AdvancedPortfolioService.delivery.simulate_risk` across scenario levels.
It is intended for local spike runs and CI experiments, not as a unit test.
"""

from __future__ import annotations

import argparse
import gc
import json
import tracemalloc
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter

from fhs.application.advanced_portfolio_service import AdvancedPortfolioService
from fhs.application.scenario_service import ScenarioService


@dataclass(frozen=True)
class ScalingMeasurement:
    """Single benchmark measurement for one scenario count."""

    scenarios: int
    runtime_seconds: float
    peak_python_heap_mib: float
    feature_count: int
    result_count: int
    sample_count_per_feature: int
    mean_expected_actual_cost: float


def _parse_levels(raw: str) -> list[int]:
    levels = [int(token.strip()) for token in raw.split(",") if token.strip()]
    if not levels:
        raise ValueError("At least one scenario level is required")
    if any(level <= 0 for level in levels):
        raise ValueError("Scenario levels must be positive integers")
    return levels


def _run_single_measurement(
    *,
    scenario_id: str,
    config_dir: Path,
    scenarios: int,
    seed: int,
) -> ScalingMeasurement:
    scenario = ScenarioService.create_default(config_dir=config_dir).load_scenario(
        scenario_id
    )
    service = AdvancedPortfolioService.from_scenario(
        scenario,
        seed=seed,
        scenarios=scenarios,
        warm_cache=True,
    )
    selected_names = [feature.name for feature in scenario.features]

    delivery_config = scenario.delivery_config.model_copy(
        update={"scenarios": scenarios}
    )

    gc.collect()
    tracemalloc.start()
    start = perf_counter()
    delivery_results = service.delivery.simulate_risk(
        selected_names,
        delivery_config=delivery_config,
        risk_model=scenario.risk_model,
        seed=seed,
    )
    runtime_seconds = perf_counter() - start
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    counts = [len(result.actual_cost) for result in delivery_results.values()]
    expected_costs = [
        float(result.expected_actual_cost) for result in delivery_results.values()
    ]

    # Release large arrays before next measurement.
    del delivery_results
    del service
    gc.collect()

    return ScalingMeasurement(
        scenarios=scenarios,
        runtime_seconds=runtime_seconds,
        peak_python_heap_mib=peak_bytes / (1024 * 1024),
        feature_count=len(selected_names),
        result_count=len(counts),
        sample_count_per_feature=(counts[0] if counts else 0),
        mean_expected_actual_cost=(
            (sum(expected_costs) / len(expected_costs)) if expected_costs else 0.0
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark delivery simulation scaling across scenario counts.",
    )
    parser.add_argument("--scenario-id", default="blockchain")
    parser.add_argument(
        "--config-dir",
        default=str(Path(__file__).resolve().parents[2] / "notebooks" / "config"),
    )
    parser.add_argument(
        "--levels",
        default="1000,5000,10000,100000,1000000",
        help="Comma-separated scenario counts.",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output",
        default=str(
            Path(__file__).resolve().parent / "results" / "delivery_risk_scaling.json"
        ),
        help="Path to JSON output file.",
    )

    args = parser.parse_args()
    levels = _parse_levels(args.levels)
    config_dir = Path(args.config_dir)

    measurements = []
    for level in levels:
        measurement = _run_single_measurement(
            scenario_id=args.scenario_id,
            config_dir=config_dir,
            scenarios=level,
            seed=args.seed,
        )
        measurements.append(measurement)
        print(
            f"[DELIVERY-SCALING] scenarios={measurement.scenarios} runtime={measurement.runtime_seconds:.3f}s "
            f"peak_python_heap={measurement.peak_python_heap_mib:.1f}MiB results={measurement.result_count} samples={measurement.sample_count_per_feature}"
        )

    payload = {
        "scenario_id": args.scenario_id,
        "seed": args.seed,
        "levels": levels,
        "measurements": [asdict(item) for item in measurements],
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[DELIVERY-SCALING] Wrote results to {output_path}")


if __name__ == "__main__":
    main()
