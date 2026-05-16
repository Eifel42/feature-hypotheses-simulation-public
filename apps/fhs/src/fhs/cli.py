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

import argparse
import json
import os
import sys

import pandas as pd
import yaml

from fhs.application.advanced_portfolio_service import AdvancedPortfolioService
from fhs.core.model import Feature


def load_features(file_path: str) -> list[Feature]:
    """Load features from YAML, JSON or CSV file."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext in (".yaml", ".yml"):
        with open(file_path) as f:
            data = yaml.safe_load(f)
            # Support both a list directly or a 'features' key
            features_data = (
                data.get("features", data) if isinstance(data, dict) else data
            )
    elif ext == ".json":
        with open(file_path) as f:
            data = json.load(f)
            features_data = (
                data.get("features", data) if isinstance(data, dict) else data
            )
    elif ext == ".csv":
        df = pd.read_csv(file_path)
        features_data = df.to_dict(orient="records")
    else:
        raise ValueError(f"Unsupported file format: {ext}. Use YAML, JSON or CSV.")

    features = []
    for item in features_data:
        # Map CSV columns if necessary (e.g. lowercase)
        if ext == ".csv":
            item = {k.lower().replace(" ", "_"): v for k, v in item.items()}

        features.append(Feature(**item))

    return features


def _build_plan_markdown(
    service: AdvancedPortfolioService,
    budget: float | None = None,
) -> str:
    """Generate a Markdown planning report from AdvancedPortfolioService."""
    lines: list[str] = [
        "# FHS Feature Planning Report",
        "",
        f"**Features:** {len(service.features)}  ",
        f"**Scenarios:** {service.scenarios:,}  ",
        f"**Seed:** {service.seed}  ",
    ]
    if budget is not None:
        lines.append(f"**Budget:** EUR {budget:,.0f}  ")
    lines.append("")

    # Ranked features
    lines.append("## Feature Ranking")
    lines.append("")
    rankings = service.decisions.rank_features()
    lines.append("| Rank | Feature | Expected Value | BVF 95% | LLP |")
    lines.append("|------|---------|---------------|---------|-----|")
    for rank, r in enumerate(rankings, 1):
        lines.append(
            f"| {rank} | {r.feature} "
            f"| EUR {r.expected_business_value:,.0f} "
            f"| EUR {r.var_95_business_value:,.0f} "
            f"| {r.llp:.1%} |"
        )
    lines.append("")

    # Portfolio snapshot
    lines.append("## Portfolio Overview")
    lines.append("")
    snap = service.portfolio_snapshot()
    lines.append(f"- **Portfolio Expected Value:** EUR {snap.expected:,.0f}")
    lines.append(f"- **Portfolio Business Value Floor 95%:** EUR {snap.var_95:,.0f}")
    lines.append(f"- **Portfolio CVaR 95%:** EUR {snap.cvar_95:,.0f}")
    lines.append("")

    # Budget optimisation (if budget provided)
    if budget is not None:
        lines.append("## Budget Optimisation")
        lines.append("")
        try:
            opt = service.optimize(budget=budget, solver="ilp", strategy="var_floor")
            lines.append(f"**Recommended features** (budget EUR {budget:,.0f}):")
            for name in opt.recommended_features:
                lines.append(f"- {name}")
            lines.append(f"\n**Total cost:** EUR {opt.total_cost:,.0f}")
            lines.append(f"**Budget remaining:** EUR {opt.budget_remaining:,.0f}")
        except Exception as exc:  # noqa: BLE001 - defensive error formatting  # pragma: no cover
            lines.append(
                f"*Optimisation failed: {exc}*"
            )  # pragma: no cover - defensive
        lines.append("")

    # Concentration
    lines.append("## Risk Concentration")
    lines.append("")
    conc = service.decisions.concentration()
    lines.append(f"- **HHI:** {conc.hhi:.3f}")
    lines.append(f"- **Verdict:** {conc.verdict}")
    if conc.shares:  # pragma: no cover - partial branch
        top_name = max(conc.shares, key=lambda k: conc.shares[k])
        lines.append(
            f"- **Top-feature share:** {conc.shares[top_name]:.1%} ({top_name})"
        )
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="FHS Planning CLI: Quantify product risks and optimize feature sets."
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # 'plan' command
    plan_parser = subparsers.add_parser(
        "plan", help="Generate a feature prioritization report"
    )
    plan_parser.add_argument(
        "--features",
        "-f",
        required=True,
        help="Path to features file (YAML, JSON, CSV)",
    )
    plan_parser.add_argument(
        "--budget", "-b", type=float, help="Total development budget (EUR)"
    )
    plan_parser.add_argument(
        "--scenarios",
        "-s",
        type=int,
        default=10000,
        help="Number of Monte Carlo scenarios (default: 10000)",
    )
    plan_parser.add_argument(
        "--output", "-o", help="Path to save the Markdown report (default: stdout)"
    )
    plan_parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    plan_parser.add_argument(
        "--distribution",
        "-d",
        default="normal",
        choices=["normal", "lognormal", "uniform"],
        help="Base distribution for simulation (default: normal)",
    )

    args = parser.parse_args()

    if args.command == "plan":
        try:
            features = load_features(args.features)
            service = AdvancedPortfolioService(
                features=features,
                seed=args.seed,
                scenarios=args.scenarios,
                budget=args.budget
                or sum(getattr(f, "development_cost", 0.0) for f in features),
                discount_rate=0.10,
            )

            report_md = _build_plan_markdown(service, budget=args.budget)

            if args.output:
                with open(args.output, "w") as f:
                    f.write(report_md)
                print(f"Report saved to {args.output}")
            else:
                print(report_md)

        except Exception as e:  # noqa: BLE001 — CLI process boundary
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
