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

# Feature Hypotheses Simulation (FHS)

> **DRAFT:** FHS is an AI-generated financial Python project with arc42 documentation. Treat the code, notebooks, and reports as a prototype for review, learning, and further validation before production use.

**Roadmap and backlog decisions, strengthened by financial risk methods.**

FHS is a Python library for Product Owners, Portfolio Owners, and Agile leaders who want to compare feature hypotheses before they commit budget and capacity. It runs 10,000 Monte Carlo scenarios per feature and turns the result into decision-ready signals: business value, business value floor, downside tail, and diversification. Risk Managers stay an important second audience because every metric is traceable, governance-friendly, and strong enough for bank-style review.

---

## Documentation

| Where to start | What you get |
| --- | --- |
| [Beginners Guide](BEGINNERS_GUIDE.md) | End-to-end walkthrough for new readers — install, first notebook, and what the numbers mean |
| [Product Owner Case Study](PRODUCT-OWNER-CASE-STUDY.md) | Investment-case walkthrough of notebooks 01–07 and the advanced track — value driver tree, four risk signals, executive verdict |
| [Notebook Learning Path](apps/fhs/notebooks/README.ipynb) | All seven blockchain case-study notebooks plus the concept tutorial |
| [Notebook 02 — Case Study Setup](apps/fhs/notebooks/02-blockchain-case-study.ipynb) | Three feature hypotheses, business value drivers, simulation parameters |
| [Notebook 07 — Executive Decision](apps/fhs/notebooks/07-blockchain-case-study-decision.ipynb) | Board-grade synthesis: business value, financial return, portfolio fit, risk, delivery cost |
| [Glossary](apps/fhs/notebooks/GLOSSARY.ipynb) | Definitions for VaR, CVaR, business value floor, break-even probability, and the rest |
| [Architecture (arc42)](apps/fhs-arc42-doc/doc/arc42-docs.adoc) | Layered architecture, key components, design decisions |
| [Library Reference](apps/fhs/README.md) | Module structure, public API, sub-facades for advanced portfolio analysis |
| [Setup & Secrets](SECRETS_SETUP.md) | What the `CHANGE_ME_*` placeholders mean and how to set the real values |

---

## Why FHS?

Story points measure effort. They say nothing about **risk** or **return**. FHS answers the questions a Product Owner, Portfolio Owner, Agile leader, or Risk Manager asks before signing off on a budget:

| Question | FHS Answer |
|---|---|
| What is this feature worth? | Expected business value across 10,000 simulated scenarios |
| What is the worst reasonable outcome? | Business Value Floor 95 — the value floor exceeded in 95 out of 100 cases |
| Which features are most reliable? | Rank by risk ratio (volatility / expected value) |
| Which features fit our budget? | Budget-constrained optimizer (EUR 100k, 150k, etc.) |
| Are we betting everything on one feature? | HHI concentration index (diversification check) |
| What survives a market downturn? | Stress tests: -50% value shock, top-feature failure, best-case scenarios |

---

## Install

FHS is supported on **macOS** and **Linux**. Choose **one** of the two paths.

> **Windows / WSL2:** should work via WSL2 (treat WSL2 as Linux), but **this path is not tested**. Use at your own risk and report issues.

### Option A — Local Python install (fastest)

Requires Python 3.14+ and `git`.

```bash
git clone https://github.com/Eifel42/feature-hypotheses-simulation-public.git
cd feature-hypotheses-simulation/apps/fhs
pip install -e ".[notebooks]"
jupyter lab notebooks/
```

Open [01-getting-started.ipynb](apps/fhs/notebooks/01-getting-started.ipynb) and run all cells. About 10 minutes.

**Get Python 3.14+:**

- **macOS** (via [Homebrew](https://brew.sh)):
  ```bash
  brew install python@3.14
  python3.14 -m pip install -e ".[notebooks]"
  ```
  On Apple Silicon (M1/M2/M3): if scientific libraries fail to build, run `pip install numpy scipy --upgrade` first, then retry.
- **Linux — Ubuntu/Debian** (via [deadsnakes PPA](https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa)):
  ```bash
  sudo add-apt-repository ppa:deadsnakes/ppa
  sudo apt update && sudo apt install python3.14 python3.14-venv python3.14-dev
  python3.14 -m pip install -e ".[notebooks]"
  ```
- **Linux — Fedora/RHEL:** `sudo dnf install python3.14 python3.14-devel`
- **Linux — Arch:** `sudo pacman -S python` (Arch ships current Python).
- **Use a virtualenv** on either OS to keep the install isolated:
  ```bash
  python3.14 -m venv .venv && source .venv/bin/activate
  pip install -e ".[notebooks]"
  ```

### Option B — Docker (no local Python)

Requires Docker + Docker Compose.

```bash
git clone https://github.com/Eifel42/feature-hypotheses-simulation-public.git
cd feature-hypotheses-simulation
export JUPYTER_TOKEN="$(openssl rand -hex 16)"
make up
# Open http://localhost:8888 and paste $JUPYTER_TOKEN
```

- **macOS:** install Docker Desktop and enable VirtioFS for fast file sync.
- **Linux:** install `docker-ce` and `docker-compose-plugin` from your distro or [docker.com](https://docs.docker.com/engine/install/). Add your user to the `docker` group to avoid `sudo`.
- **Sandboxed alternative:** a [Lima](https://lima-vm.io/) VM with Docker installed inside it works on both macOS and Linux. Docker runs inside the VM only — no host Docker socket forwarding.

### Verify and run quality gates

```bash
cd apps/fhs
python3 -m pytest tests/ -v   # all tests should pass

# from the repo root
make quality-report            # generate Sonar reports without upload
make quality                   # optional: uploads to an external SonarQube server
```

`make quality` requires `SONAR_HOST_URL` and `SONAR_TOKEN` in your shell environment. Use `make quality-report` for a local-only check.

---

## How To — From Feature Idea to Roadmap Decision

The practical Product Owner workflow in five steps. Each step maps to a notebook in the learning path.

**1. Frame the feature as a hypothesis.** A feature is a testable assumption, not a task: *"If we build X, users do Y and that creates Z business value."* You need three numbers: expected users, conversion rate, and how uncertain you are.

**2. Edit the scenario YAML.** All inputs live in [apps/fhs/notebooks/config/blockchain.yaml](apps/fhs/notebooks/config/blockchain.yaml). Every notebook loads the same file via `load_scenario("blockchain")`, so a single edit propagates everywhere.

```python
from fhs.notebook import load_scenario

scenario = load_scenario("blockchain")
for f in scenario.features:
    print(f"{f.name} — {f.development_cost:,.0f} EUR")
```

**3. Run the simulation and read three numbers.** Per feature:

- **Expected business value** — your planning number (mean of 10,000 scenarios).
- **Business Value Floor 95** — the floor reached in 95 out of 100 scenarios. Your downside guarantee.
- **CVaR 95** — average outcome in the worst 5% of scenarios. The tail.

**4. Decide as a portfolio.** Single features get ranked. The portfolio view tells you whether your roadmap is diversified (HHI < 0.25) or concentrated on one bet. Stress tests show what happens when the market drops or a top feature fails.

**5. Defend the recommendation.** Every metric is in EUR with a plain-language sentence next to it. The notebook output goes straight into a sprint review or board deck.

Full walkthrough with notebook references: [Beginners Guide](BEGINNERS_GUIDE.md).

---

## Notebooks — Learning Path

Open [apps/fhs/notebooks/README.ipynb](apps/fhs/notebooks/README.ipynb) for the full guide.

### Core track — Beginner (Product Owners, Portfolio Owners, Agile leaders)

| # | Notebook | What you learn | Time |
|:-:|---|---|:-:|
| 01 | [Getting Started](apps/fhs/notebooks/01-getting-started.ipynb) | Simulate one feature with 10,000 scenarios. Learn Business Value Floor 95, expected business value, and CVaR. | 10 min |
| 02 | [Blockchain Case Study](apps/fhs/notebooks/02-blockchain-case-study.ipynb) | Three competing blockchain feature hypotheses with strategic categories. Full EUR business case. | 15 min |
| 03 | [Capital Budgeting](apps/fhs/notebooks/03-blockchain-case-study-capital-budgeting.ipynb) | NPV, IRR, upfront vs. installment financing, profitability index. | 15 min |
| 04 | [Portfolio Advisor](apps/fhs/notebooks/04-blockchain-case-study-advisor.ipynb) | NPV-based optimization, budget sensitivity, horizon comparison. | 15 min |
| 05 | [Risk Dashboard](apps/fhs/notebooks/05-blockchain-case-study-risk.ipynb) | Risk layer simulation, sensitivity analysis, heatmaps. | 15 min |
| 06 | [Delivery Risk](apps/fhs/notebooks/06-blockchain-case-study-delivery-risk.ipynb) | Sprint overruns, cost-at-risk, break-even probability. | 15 min |
| 07 | [Executive Decision](apps/fhs/notebooks/07-blockchain-case-study-decision.ipynb) | Combined decision matrix across notebooks 02-06 and final board recommendation. | 10 min |

### Tutorial track — Concept deep dive (Product Owners first, Risk Managers second)

| # | Notebook | What you learn | Time |
|:-:|---|---|:-:|
| T01 | [Distribution Guide](apps/fhs/notebooks/tutorial/01-distribution-guide.ipynb) | Normal vs. Lognormal vs. Beta — choose the right model for your uncertainty. Includes clipping warnings and skewness comparison. | 20 min |

### Advanced track — Portfolio analysis (Portfolio Owners, Agile leaders, Risk Managers)

| # | Notebook | What you learn | Time |
|:-:|---|---|:-:|
| A01 | [Portfolio Advisor](apps/fhs/notebooks/advanced/01-portfolio-advisor.ipynb) | Feature ranking by risk-adjusted value, solver comparison, concentration risk (HHI), stress tests. | 20 min |
| A02 | [Portfolio Risk Dashboard](apps/fhs/notebooks/advanced/02-portfolio-risk-dashboard.ipynb) | Risk layers (market, delivery, crisis), likelihood-of-non-delivery impact, budget risk path at different investment levels. | 20 min |

---

## Architecture in One Page — arc42 Canvases

Two one-page canvases give you the architecture without reading the full handbook.

| Canvas | Question it answers | When to read |
|---|---|---|
| **[Architecture Inception Canvas](apps/fhs-arc42-doc/doc/architecture-inception-canvas.adoc)** | *Why does FHS exist? Who is it for? What is in/out of scope?* | Before a stakeholder kick-off |
| **[Architecture Communication Canvas](apps/fhs-arc42-doc/doc/architecture-communication-canvas.adoc)** | *How is FHS built? Which components, technologies, and decisions matter?* | Before a code review or contribution |

Full arc42 documentation (12 chapters + C4 diagrams): [apps/fhs-arc42-doc/](apps/fhs-arc42-doc/). From the repository root, build it with `make docs`. From [apps/fhs-arc42-doc/](apps/fhs-arc42-doc/), build it with `make docs-build`.

---

## Configuration

FHS keeps simulation logic and business parameters separated:

1. **YAML-based** — all scenarios live in [apps/fhs/notebooks/config/](apps/fhs/notebooks/config/).
2. **Schema-validated** — a JSON Schema rejects bad inputs before they reach the engine.
3. **Centralized** — change the YAML once and every notebook adopts the update.

For the full configuration reference, open [apps/fhs/notebooks/config/scenario-config-reference.ipynb](apps/fhs/notebooks/config/scenario-config-reference.ipynb).

---

## Quick Troubleshooting

| Symptom | What to try |
|---|---|
| `jupyter: command not found` | Re-run `pip install -e ".[notebooks]"` inside [apps/fhs/](apps/fhs/) |
| Port `8888` is already in use | Start Jupyter with `jupyter lab notebooks/ --port 8890` |
| Docker asks for a token | Use the value printed by `make up`, or set `JUPYTER_TOKEN` before starting |
| Sonar quality upload fails | Use `make quality-report` locally, or set `SONAR_HOST_URL` and `SONAR_TOKEN` for `make quality` |

---

## Key Concepts

> Full definitions: [apps/fhs/notebooks/GLOSSARY.ipynb](apps/fhs/notebooks/GLOSSARY.ipynb)

| Term | Plain English | Example |
|---|---|---|
| **Monte Carlo Simulation** | Run 10,000 possible futures and measure the spread of outcomes | Each scenario randomly samples users and conversion rates based on your uncertainty estimates |
| **Expected Business Value** | The average outcome across all 10,000 scenarios | The mean of all simulated values is your planning number |
| **Business Value Floor (BVF 95%)** | The value floor exceeded in 95 out of 100 scenarios — a VaR-style downside boundary | "We keep at least EUR 80,000 of business value in 95% of cases" |
| **Expected Shortfall (CVaR 95%)** | Average of the worst 5% of outcomes — the tail risk beyond the floor | "If things go badly, we earn EUR 65,000 on average" |
| **Risk Ratio** | Standard deviation / Expected business value — measures predictability | 15% = predictable, 40% = high uncertainty (consider prototyping first) |
| **Strategic Category** | Why you build a feature (not all are for direct profit) | Value Driver, Regulatory Compliance, Market Differentiation |
| **HHI (Concentration Index)** | Measures portfolio diversification (sum of squared value shares) | Below 0.25 = well-diversified, above 0.40 = too concentrated on one feature |
| **Budget Optimization** | Find the best feature set within a EUR budget constraint | "Given EUR 100,000, which features maximize expected business value?" |
| **Efficient Frontier** | Portfolios with the best expected return for a given risk level | Trade-off curve: higher return requires accepting higher risk |

---

## More Documentation

- [BEGINNERS_GUIDE.md](BEGINNERS_GUIDE.md) — end-to-end walkthrough for new readers
- [PRODUCT-OWNER-CASE-STUDY.md](PRODUCT-OWNER-CASE-STUDY.md) — investment-case walkthrough of notebooks 01–07 and the advanced track, with embedded charts and an executive cheat sheet
- [Blockchain Case Study — Executive Decision](apps/fhs/notebooks/07-blockchain-case-study-decision.ipynb) — board-grade walkthrough: value driver tree, five investment dimensions, layered risk evidence, executive decision
- [apps/fhs/README.md](apps/fhs/README.md) — library structure and development commands
- [apps/fhs-arc42-doc/README.md](apps/fhs-arc42-doc/README.md) — arc42 build instructions
- [SECRETS_SETUP.md](SECRETS_SETUP.md) — credentials and machine-specific configuration

---

## Disclaimer

This software is a prototype for educational and research purposes. Simulation results are not financial advice. Users are responsible for validating results before making business decisions.

## License

MIT License — Copyright (c) 2026 Stefan Zils — [github.com/Eifel42](https://github.com/Eifel42)

See [LICENSE](LICENSE) and [NOTICE](NOTICE) for details. When forking or using this project, retain the copyright notice and provide attribution to **Feature Hypotheses Simulation (FHS)** by Stefan Zils.
