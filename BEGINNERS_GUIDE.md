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

# Beginners Guide to FHS

**Quantify feature risk before you commit the budget.**

This guide is your first end-to-end pass through FHS. It has three parts:

1. **Install** — get the tool running on your laptop in under 10 minutes.
2. **How-to** — apply FHS to a real Product Owner workflow, from feature idea to roadmap decision.
3. **Notebook learning path** — practice each step in a hands-on notebook.

Audience: Product Owners, Portfolio Owners, and Agile leaders new to FHS. Risk Managers are the second audience — the same notebooks also work as risk evidence for governance reviews.

> Looking for a **board-grade walkthrough**? Open [07 — Blockchain Case Study: Executive Decision](apps/fhs/notebooks/07-blockchain-case-study-decision.ipynb). It combines the outputs from notebooks 02-06 into five investment dimensions and closes with a board-ready recommendation.

---

## Part 1 — Install

FHS is supported on **macOS** and **Linux**. Pick **one** of the two paths.

> **Windows / WSL2:** should work via WSL2 (treat WSL2 as Linux), but **this path is not tested**. Use at your own risk and report issues.

### Option A — Local Python install

Requires Python 3.14+ and `git`.

```bash
git clone https://github.com/Eifel42/feature-hypotheses-simulation-public.git
cd feature-hypotheses-simulation/apps/fhs
pip install -e ".[notebooks]"
jupyter lab notebooks/
```

JupyterLab opens in your browser. Open [01-getting-started.ipynb](apps/fhs/notebooks/01-getting-started.ipynb) and run all cells.

**Get Python 3.14+ on your system:**

- **macOS** (via [Homebrew](https://brew.sh)):
  ```bash
  brew install python@3.14
  python3.14 -m pip install -e ".[notebooks]"
  ```
  On Apple Silicon (M1/M2/M3): if scientific libraries fail to build, run `pip install numpy scipy --upgrade` first, then retry `pip install -e ".[notebooks]"`
- **Linux — Ubuntu/Debian** (via [deadsnakes PPA](https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa)):
  ```bash
  sudo add-apt-repository ppa:deadsnakes/ppa
  sudo apt update && sudo apt install python3.14 python3.14-venv python3.14-dev
  python3.14 -m pip install -e ".[notebooks]"
  ```
- **Linux — Fedora/RHEL:** `sudo dnf install python3.14 python3.14-devel`
- **Linux — Arch:** `sudo pacman -S python` (Arch ships current Python).

**Recommended on both OSes — use a virtualenv** to keep the install isolated:

```bash
python3.14 -m venv .venv && source .venv/bin/activate
pip install -e ".[notebooks]"
```

For an isolated VM workspace on either OS, you can use a [Lima](https://lima-vm.io/) VM with Docker installed inside it.

### Option B — Docker (no local Python)

Requires Docker + Docker Compose.

```bash
git clone https://github.com/Eifel42/feature-hypotheses-simulation-public.git
cd feature-hypotheses-simulation
export JUPYTER_TOKEN="$(openssl rand -hex 16)"
make up
# Open http://localhost:8888 and paste $JUPYTER_TOKEN
```

- **macOS:** install Docker Desktop and enable VirtioFS in Settings → General for fast file sync.
- **Linux:** install `docker-ce` and `docker-compose-plugin` from your distro or [docker.com](https://docs.docker.com/engine/install/). Add your user to the `docker` group (`sudo usermod -aG docker $USER`, then re-login) to avoid `sudo`.

### Verify the install

```bash
cd apps/fhs
python3 -m pytest tests/ -v
```

All tests should pass. If something fails, ensure you are on Python 3.14+ (see [apps/fhs/pyproject.toml](apps/fhs/pyproject.toml)).

### Quick troubleshooting

| Symptom | What to try |
|---|---|
| `jupyter: command not found` | Re-run `pip install -e ".[notebooks]"` inside [apps/fhs/](apps/fhs/) |
| Jupyter does not open automatically | Open `http://localhost:8888` manually |
| Port `8888` is already in use | Start Jupyter with `jupyter lab notebooks/ --port 8890` |
| Docker asks for a token | Use the token printed by `make up`, or set `JUPYTER_TOKEN` before starting |

---

## Part 2 — How-To: From Feature Idea to Roadmap Decision

The Product Owner workflow has five steps. Each step maps to a notebook so you can practice it.

### Step 1 — Frame the feature as a hypothesis

A feature is a **testable assumption**, not a task:

> *"If we build a transparent supply-chain tracker, around 20,000 buyers will use it, 4% will pay a premium, and each conversion is worth EUR 25 in extra margin — give or take 30%."*

You need three numbers:

| Number | Plain English | Example |
|---|---|---|
| **Expected users** | Best guess for the user count | 20,000 |
| **Conversion rate** | Share of users who do the valuable thing | 4% |
| **Uncertainty** | How wide your estimate could be off | ±30% |

Practice: [01 Getting Started](apps/fhs/notebooks/01-getting-started.ipynb).

### Step 2 — Put the feature into the scenario YAML

All inputs live in one file: [apps/fhs/notebooks/config/blockchain.yaml](apps/fhs/notebooks/config/blockchain.yaml). Every notebook reads from this file via `load_scenario("blockchain")`. Edit the YAML once and every notebook adopts the change.

```python
from fhs.notebook import load_scenario

scenario = load_scenario("blockchain")
for f in scenario.features:
    print(f"{f.name} — {f.development_cost:,.0f} EUR")
```

For an interactive editor inside the notebook, open Notebook 02 with `editable=True`.

### Step 3 — Run the simulation and read three numbers

The simulator runs **10,000 scenarios per feature**. Three numbers per feature carry the decision:

- **Expected business value** — average of all 10,000 outcomes. Your planning number.
- **Business Value Floor 95 (BVF 95%)** — the floor exceeded in 95 out of 100 scenarios. Your downside guarantee.
- **CVaR 95 (Expected Shortfall)** — average outcome in the worst 5% of scenarios. The tail you must live with if things go badly.

Practice: [02 Blockchain Case Study](apps/fhs/notebooks/02-blockchain-case-study.ipynb).

### Step 4 — Decide as a portfolio, not feature-by-feature

A single feature is rarely the whole story. The portfolio view answers:

- **Is the roadmap diversified or concentrated?** → HHI index (below 0.25 = healthy, above 0.40 = too concentrated)
- **Which feature carries most of the risk?** → Shapley risk attribution
- **What survives a market shock?** → stress tests at −30% / −50% / top-feature-failure

Practice: [A01 Portfolio Advisor](apps/fhs/notebooks/advanced/01-portfolio-advisor.ipynb).

### Step 5 — Defend the recommendation

Every output is in **EUR** with a plain-language sentence next to it. Drop the notebook output into your sprint review, business case, or board deck. The metrics also map to standard governance language so a Risk Manager can sign off.

Practice: [05 Risk Dashboard](apps/fhs/notebooks/05-blockchain-case-study-risk.ipynb).

---

## Architecture in One Page — arc42 Canvases

Two one-page canvases give you the broader context without reading the full architecture handbook.

| Canvas | Question it answers | When to read |
|---|---|---|
| **[Architecture Inception Canvas](apps/fhs-arc42-doc/doc/architecture-inception-canvas.adoc)** | *Why does FHS exist? Who is it for? What is in/out of scope?* | Before a stakeholder kick-off |
| **[Architecture Communication Canvas](apps/fhs-arc42-doc/doc/architecture-communication-canvas.adoc)** | *How is FHS built? Which components, technologies, decisions?* | Before a code review or contribution |

Full arc42 documentation (12 chapters + C4 diagrams): [apps/fhs-arc42-doc/](apps/fhs-arc42-doc/). From the repository root, build it with `make docs`. From [apps/fhs-arc42-doc/](apps/fhs-arc42-doc/), build it with `make docs-build`.

---

## Part 3 — Notebook Learning Path

| Track | Audience | Start here |
|---|---|---|
| **Core (01-07)** | Product Owners, Portfolio Owners, and Agile leaders new to FHS | [01 Getting Started](apps/fhs/notebooks/01-getting-started.ipynb) |
| **Tutorial (T01)** | Product Owners first, Risk Managers second | [T01 Distribution Guide](apps/fhs/notebooks/tutorial/01-distribution-guide.ipynb) |
| **Advanced (A01-A02)** | Portfolio Owners, Agile leaders, and Risk Managers | [A01 Portfolio Advisor](apps/fhs/notebooks/advanced/01-portfolio-advisor.ipynb) |

Complete the Core track first. Tutorial and Advanced build on it.

> **Investment-case version:** [07 — Blockchain Case Study: Executive Decision](apps/fhs/notebooks/07-blockchain-case-study-decision.ipynb) walks notebooks 02-06 as a single capital-allocation narrative — what each one decides, why it matters to the steering committee, and how the evidence is constructed.

> **Shared data basis:** all blockchain notebooks (02-07, A01-A02) load the same YAML scenario (`apps/fhs/notebooks/config/blockchain.yaml`) via `load_scenario("blockchain")`. Change the scenario once, and every notebook adopts the update.

---

## Core track

### 01 — Getting Started

**What it does:** Guides you through your first feature decision review — from defining a feature hypothesis to reading the risk evidence.

**Audience:** Product Owners and team members who want to learn FHS.

**You will learn:**
- How to describe a feature with three numbers: expected users, conversion rate, and uncertainty
- How Monte Carlo simulation generates 10,000 "what-if" scenarios
- How to read Business Value Floor 95 and expected business value

**Prerequisites:** None — start here.

**Key terms:**

| Term | Plain English |
|---|---|
| **Feature** | A backlog item described with three numbers: expected users, conversion rate, and uncertainty |
| **Monte Carlo Simulation** | The computer runs 10,000 scenarios with slightly different assumptions to draw a complete picture of possible outcomes |
| **Business Value Floor (BVF 95%)** | Your downside floor: in 95 out of 100 cases actual business value will be better than this number (VaR-style metric) |
| **Uncertainty** | How far off your estimate could be — higher uncertainty means a wider range of outcomes |
| **Conversion Rate** | The percentage of users who perform the desired action (purchase, signup, task completion) |

---

### 02 — Case Study: Blockchain in Agriculture

**What it does:** A complete end-to-end case study — three competing feature hypotheses for an agricultural operation, each with a strategic category (Value Driver, Regulatory Compliance, Market Differentiation), from decision framing to prioritized roadmap.

**Audience:** Anyone who wants to see how FHS is applied step by step to a real business decision.

**You will learn:**
- How to translate business goals into feature definitions with EUR values
- How to compare multiple hypotheses side by side
- How strategic categories explain why some features have negative ROI (regulation, market positioning)
- How to rank features by expected business value and downside risk
- How to build a prioritized backlog with data instead of gut feeling

**Prerequisites:** Notebook 01 (Getting Started).

**Key terms:**

| Term | Plain English |
|---|---|
| **Hypothesis** | A testable assumption about value creation: "If we build X, users do Y and generate Z in business value" |
| **Business Value per Conversion** | How much value each successful user action generates |
| **Strategic Category** | Why you build a feature (not all are for direct profit) — e.g., Value Driver, Regulatory Compliance, Market Differentiation |
| **Development Cost** | The estimated cost (EUR) for building and deployment — enables ROI calculation |
| **Risk-Return Ratio** | How much you can gain relative to accepted risk — features with high value and low downside risk are preferred |
| **Portfolio** | All features considered together as one investment — total risk is usually less than the sum of individual risks |
| **Backlog Prioritization** | The decision of which features to build first, based on quantified values and risks instead of opinions |

---

### 03 — Capital Budgeting

**What it does:** Applies capital budgeting methods (NPV, IRR, profitability index) to the blockchain features. Compares upfront vs. installment financing.

**Audience:** Product Owners, Portfolio Owners, and finance partners who need to justify feature investments.

**You will learn:**
- How to calculate NPV and IRR for feature investments
- When upfront vs. installment financing makes sense
- How to rank features by profitability index

**Prerequisites:** Notebook 02 (Blockchain Case Study).

---

### 04 — Portfolio Advisor

**What it does:** NPV-based optimization across multiple features. Shows budget sensitivity and horizon comparison.

**Audience:** Product Owners, Portfolio Owners, and Risk Managers who plan multi-feature investments.

**You will learn:**
- How to optimize feature selection under budget constraints
- How budget sensitivity affects which features make the cut
- How the planning horizon changes investment decisions

**Prerequisites:** Notebook 03 (Capital Budgeting).

---

### 05 — Risk Dashboard

**What it does:** Risk layer simulation covering market risk, delivery risk, component risk, and global shocks. Includes sensitivity analysis and heatmaps.

**Audience:** Portfolio Owners, Risk Managers, and Engineering Leads who need a clear portfolio risk view.

**You will learn:**
- How different risk layers interact (market, delivery, crisis)
- How to read sensitivity analysis and risk heatmaps
- Which features drive the most portfolio risk

**Prerequisites:** Notebook 02 (Blockchain Case Study).

---

### 06 — Delivery Risk

**What it does:** Simulates sprint overruns, cost-at-risk, and cancellation scenarios. Reports break-even probability, expected loss, and Loss at Risk.

**Audience:** Product Owners and Engineering Leads who manage delivery timelines.

**You will learn:**
- How likely each feature is to break even
- What the expected loss is in failure scenarios
- How much sunk cost you face if a feature is cancelled mid-delivery

**Prerequisites:** Notebook 02 (Blockchain Case Study).

---

### 07 — Executive Decision

**What it does:** Combines the key outputs from notebooks 02-06 into one board-ready view: business value, financial return, portfolio optimization, risk profile, delivery cost risk, and final recommendation.

**Audience:** Product Owners, Portfolio Owners, Risk Managers, and steering committees that need one decision page instead of five separate deep dives.

**You will learn:**
- How to read the five investment dimensions together
- How traffic-light recommendations are derived from quantitative evidence
- What to do next for GO, Conditional GO, or REVIEW outcomes

**Prerequisites:** Notebooks 02-06.

---

## Tutorial track

### T01 — Distribution Guide

**What it does:** Shows how Normal, Lognormal, and Beta distributions model different types of uncertainty — and what happens to your decision signal if you choose the wrong one.

**Audience:** Product Owners and Risk Managers who want to improve the accuracy of their estimates.

**You will learn:**
- When to use each distribution and why
- How the wrong distribution can over- or under-state risk by 10–30%
- A simple decision tree to pick the right distribution every time

**Prerequisites:** Notebook 01 (Getting Started).

**Key terms:**

| Term | Plain English |
|---|---|
| **Normal Distribution** | The classic bell curve — symmetric, simple, but can generate impossible values like negative conversion rates |
| **Lognormal Distribution** | Right-skewed — most outcomes are modest, but a few are very high. Realistic for business value data |
| **Beta Distribution** | Naturally bounded between 0 and 1 — mathematically correct for conversion rates and percentages |
| **Clipping Bias** | When a simulation clips negative values to zero, it slightly inflates the average — acceptable at low uncertainty, misleading at high uncertainty |

---

## Advanced track

### A01 — Portfolio Advisor (10 Features)

**What it does:** An automated decision-support tool that ranks features by risk-adjusted value, compares three solver strategies (ILP, Exact, Greedy), and checks portfolio concentration risk (HHI).

**Audience:** Product Owners and Risk Managers who manage multiple features and need data-driven answers quickly.

**You will learn:**
- How to rank all features by value and risk
- How to find the best combination of features within a fixed budget
- How to detect when one feature carries too much of the portfolio risk
- How solver strategies differ in speed and accuracy

**Prerequisites:** Notebook 01 (Getting Started).

**Key terms:**

| Term | Plain English |
|---|---|
| **Budget Constraint** | A fixed development budget — the advisor finds the best-value combination of features that fits within it |
| **Risk Concentration** | When one feature represents more than 50% of expected portfolio value — if it fails, the whole portfolio suffers |
| **Opportunity Cost** | The business value you forgo by choosing not to build a feature |
| **Stress Test** | A "what if" scenario: "What if the market drops 30%?" The advisor shows the portfolio impact |

---

### A02 — Portfolio Risk Dashboard

**What it does:** Risk layer simulation (market, delivery, crisis), likelihood-of-non-delivery impact analysis, stress scenarios, and budget risk path at different investment levels.

**Audience:** Portfolio Owners, Agile leaders, and Risk Managers who need a structured risk view for stakeholder reviews.

**You will learn:**
- How risk layers interact and compound
- How likelihood of non-delivery changes the risk picture
- How to present a budget risk path at 25%, 50%, and 100% investment levels

**Prerequisites:** A01 (Portfolio Advisor).

---

## Suggested learning paths

### "I am a Product Owner — quick results"
1. 01 Getting Started
2. 02 Blockchain Case Study
3. 07 Executive Decision

### "I need to present a business case"
1. 01 Getting Started
2. 02 Blockchain Case Study
3. 03 Capital Budgeting
4. 07 Executive Decision

### "I manage a feature portfolio and need risk numbers"
1. 01 Getting Started
2. 02 Blockchain Case Study
3. 05 Risk Dashboard
4. 07 Executive Decision
5. A01 Portfolio Advisor
6. A02 Portfolio Risk Dashboard

### "I want to understand the full methodology"
1. 01 Getting Started
2. 02 Blockchain Case Study
3. T01 Distribution Guide
4. 03-07 Remaining Core notebooks
5. A01 Portfolio Advisor
6. A02 Portfolio Risk Dashboard

---

## Glossary

| Term | Plain English |
|---|---|
| [**VaR 95%**](https://en.wikipedia.org/wiki/Value_at_risk) | The downside floor — 95 out of 100 scenarios land above this |
| [**CVaR 95%**](https://en.wikipedia.org/wiki/Expected_shortfall) | Average outcome in the worst 5% of scenarios |
| [**Monte Carlo**](https://en.wikipedia.org/wiki/Monte_Carlo_methods_in_finance) | Running 10,000 random simulations to map all possible outcomes |
| **Conversion Rate** | Percentage of users who take the desired action |
| **Uncertainty** | How far your estimate could be off — higher = wider range of outcomes |
| [**Portfolio**](https://en.wikipedia.org/wiki/Portfolio_(finance)) | All features viewed together as one investment |
| [**Diversification**](https://en.wikipedia.org/wiki/Diversification_(finance)) | Risk reduction from combining uncorrelated features |
| [**Efficient Frontier**](https://en.wikipedia.org/wiki/Efficient_frontier) | Portfolios with the best expected return for a given risk level |
| [**Sharpe Ratio**](https://en.wikipedia.org/wiki/Sharpe_ratio) | Return per unit of risk — higher is better |
| **Stress Test** | Simulating extreme scenarios to test portfolio resilience |
| [**Beta Distribution**](https://en.wikipedia.org/wiki/Beta_distribution) | Probability shape bounded between 0 and 1 — correct for conversion rates |
| [**Lognormal Distribution**](https://en.wikipedia.org/wiki/Log-normal_distribution) | Right-skewed distribution — realistic for business value data |
| [**Opportunity Cost**](https://en.wikipedia.org/wiki/Opportunity_cost) | Business value lost by choosing not to build a feature |
| **Risk Concentration** | When one feature dominates portfolio risk |
| **Strategic Category** | Why a feature is built: Value Driver (generates direct business value), Regulatory Compliance (required by law), or Market Differentiation (competitive advantage) |
| **Development Cost** | Estimated EUR cost to build a feature — used for ROI and budget calculations |
| **Likelihood of Non-Delivery** | Probability that a feature does not reach the planned outcome because delivery fails or slips too far |
| **Net Value** | Expected business value minus development cost — negative means the feature costs more than it earns |
| **Break-Even** | When cumulative business value exceeds cumulative development cost |
| [**NPV**](https://en.wikipedia.org/wiki/Net_present_value) | Sum of discounted future cash flows minus the initial investment |
| [**IRR**](https://en.wikipedia.org/wiki/Internal_rate_of_return) | The discount rate at which NPV becomes zero — used to compare investment options |

---

## Further Reading

### Financial Risk Methods

| Source | Topic | Link |
|---|---|---|
| MIT OpenCourseWare | Value at Risk — lecture notes (18.S096) | [ocw.mit.edu](https://ocw.mit.edu/courses/18-s096-topics-in-mathematics-with-applications-in-finance-fall-2013/resources/lecture-7-value-at-risk-var-models/) |
| MIT OpenCourseWare | Monte Carlo Simulation — lecture (6.0002) | [ocw.mit.edu](https://ocw.mit.edu/courses/6-0002-introduction-to-computational-thinking-and-data-science-fall-2016/resources/lecture-6-monte-carlo-simulation/) |
| MIT OpenCourseWare | Analytics of Finance (15.450) | [ocw.mit.edu](https://ocw.mit.edu/courses/15-450-analytics-of-finance-fall-2010/) |
| Wikipedia | Value at Risk | [en.wikipedia.org](https://en.wikipedia.org/wiki/Value_at_risk) |
| Wikipedia | Expected Shortfall (CVaR) | [en.wikipedia.org](https://en.wikipedia.org/wiki/Expected_shortfall) |
| Wikipedia | Monte Carlo Methods in Finance | [en.wikipedia.org](https://en.wikipedia.org/wiki/Monte_Carlo_methods_in_finance) |
| Wikipedia | Modern Portfolio Theory | [en.wikipedia.org](https://en.wikipedia.org/wiki/Modern_portfolio_theory) |
| Wikipedia | Efficient Frontier | [en.wikipedia.org](https://en.wikipedia.org/wiki/Efficient_frontier) |
| Wikipedia | Sharpe Ratio | [en.wikipedia.org](https://en.wikipedia.org/wiki/Sharpe_ratio) |
| Wikipedia | Diversification (finance) | [en.wikipedia.org](https://en.wikipedia.org/wiki/Diversification_(finance)) |

### Probability Distributions

| Source | Topic | Link |
|---|---|---|
| Wikipedia | Normal Distribution | [en.wikipedia.org](https://en.wikipedia.org/wiki/Normal_distribution) |
| Wikipedia | Log-Normal Distribution | [en.wikipedia.org](https://en.wikipedia.org/wiki/Log-normal_distribution) |
| Wikipedia | Beta Distribution | [en.wikipedia.org](https://en.wikipedia.org/wiki/Beta_distribution) |
| Wikipedia | Skewness | [en.wikipedia.org](https://en.wikipedia.org/wiki/Skewness) |
