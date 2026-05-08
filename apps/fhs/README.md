<!--
Project: FHS (Feature Hypotheses Simulation)
Copyright: Eifel42 Stefan Zils 2026
License: See LICENSE and README.md
#
Disclaimer: This software is provided "as is", without warranty of any kind,
express or implied, including but not limited to the warranties of
merchantability, fitness for a particular purpose, and noninfringement.
In no event shall the authors or copyright holders be liable for any claim,
damages or other liability, whether in an action of contract, tort or
otherwise, arising from, out of or in connection with the software or the
use or other dealings in the software.

-->

# Feature Hypotheses Simulation — Python Library

This folder contains the FHS Python package and the notebook learning path.

For the full project overview, see the [root README](../../README.md).

---

## What FHS Helps You Decide

FHS helps Product Owners, Portfolio Owners, Agile leaders, and Risk Managers answer practical questions:

- Which feature hypotheses create the highest expected business value?
- Which roadmap options show the strongest downside resilience?
- Which portfolio fits budget and delivery constraints?
- How much loss should we plan for in a bad quarter?

---

## Quick Start

```bash
pip install -e ".[notebooks]"
jupyter lab notebooks/
```

Start with [01-getting-started.ipynb](notebooks/01-getting-started.ipynb) — it takes about 10 minutes.

---

## Product Owner Workflow

Generate board-ready portfolio output in a few lines:

```python
from fhs.notebook import load_scenario

scenario = load_scenario("blockchain")

# Access features, strategy, and budget
features = scenario.features
budget = scenario.budget
```

**[Open the Portfolio Advisor notebook ->](notebooks/advanced/01-portfolio-advisor.ipynb)**

---

## Notebooks

Full learning path: [notebooks/README.ipynb](notebooks/README.ipynb).

**Core track — Beginner**

| # | Notebook | Audience |
|:-:|---|---|
| 01 | [Getting Started](notebooks/01-getting-started.ipynb) | Everyone |
| 02 | [Blockchain Case Study](notebooks/02-blockchain-case-study.ipynb) | Everyone |
| 03 | [Capital Budgeting](notebooks/03-blockchain-case-study-capital-budgeting.ipynb) | Product Owner / Portfolio Owner / Finance |
| 04 | [Portfolio Advisor](notebooks/04-blockchain-case-study-advisor.ipynb) | Product Owner / Portfolio Owner / Risk Manager |
| 05 | [Risk Dashboard](notebooks/05-blockchain-case-study-risk.ipynb) | Portfolio Owner / Risk Manager |
| 06 | [Delivery Risk](notebooks/06-blockchain-case-study-delivery-risk.ipynb) | PO / Engineering Lead |
| 07 | [Executive Decision](notebooks/07-blockchain-case-study-decision.ipynb) | Product Owner / Portfolio Owner / Risk Manager / Steering |

**Tutorial track — Concept deep dive**

| # | Notebook | Audience |
|:-:|---|---|
| T01 | [Distribution Guide](notebooks/tutorial/01-distribution-guide.ipynb) | Product Owner / Risk Manager |

**Advanced track — Portfolio analysis**

| # | Notebook | Audience |
|:-:|---|---|
| A01 | [Portfolio Advisor](notebooks/advanced/01-portfolio-advisor.ipynb) | Portfolio Owner / Risk Manager / Product Owner |
| A02 | [Portfolio Risk Dashboard](notebooks/advanced/02-portfolio-risk-dashboard.ipynb) | Portfolio Owner / Risk Manager / Product Owner |

---

## Delivery Risk (Notebook 06)

Notebook 06 is designed for beginners and executive discussions.

What it does:

- Simulates possible sprint overruns for each feature.
- Uses a fixed sprint length of **2 weeks** in the delivery-risk model.
- Adds cancellation logic after severe overruns.
- Reports break-even probability, expected loss, and Loss at Risk (95%).

This keeps delivery assumptions simple, transparent, and easy to explain.

## Executive Decision (Notebook 07)

Notebook 07 is the board-ready synthesis of the blockchain case study.

What it does:

- Combines business value, financial return, portfolio optimization, risk profile, and delivery cost risk.
- Links back to notebooks 02-06 for each deep dive.
- Produces a traffic-light recommendation and next actions for GO, Conditional GO, or REVIEW.

---

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev,notebooks]"

# Run tests
python3 -m pytest tests/ -v

# Code quality
python3 -m ruff format src/ tests/ && python3 -m ruff check src/ tests/
```

---

## License

MIT License — Copyright (c) 2026 Stefan Zils
