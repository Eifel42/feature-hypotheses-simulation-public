# Product Owner Case Study - No-Install Overview

This is the short reading version of the blockchain roadmap case study. It is designed for readers who want the Product Owner numbers and key graphics without installing or running Jupyter.

## Decision Question

**Which use of the EUR 155,000 budget creates the best risk-adjusted roadmap decision?**

The case study compares three feature hypotheses:

| Feature | Decision | Why |
|---|---|---|
| H1 Simplified UI | Do not fund now | Expected business value is too low for the planned investment. |
| H2 Traceability | Fund next | Strongest expected business value and strongest value floor. |
| H3 Expiration Alerts | Test first | Good value for low capital, but development cost pressure is high. |

The recommended current portfolio is **two of three features: H2 Traceability + H3 Expiration Alerts**. Do not fund all three now; H1 Simplified UI stays on hold until its business value case improves. The decision still needs development controls, because development failure can remove too much value.

### How Business Value Is Measured Here

Business value is **not one number** — it depends on what the feature aims to improve and on the type of information system it lives in. This case study uses the **customer-facing conversion model**:

> business value = users × conversion rate × value per conversion

This fits **customer-facing systems** (customer portals, e-commerce, marketing apps) where conversion is the central metric.

For **internal systems** (employee tools, internal portals, decision-support dashboards) the model is the same shape, but the *units* change — for example time saved per task × labour cost, or events × failure-rate reduction × cost per failure. The Monte Carlo simulation is parameter-agnostic; only the input units shift. The deep comparison and concrete internal models are in the [Notebook 02 reading guide](notebooks/02-business-value.md#measuring-business-value-customer-facing-vs-internal-systems).

The headline message: **the value of a feature can be measured in several legitimate ways**. The case study picks one model and stays with it; a different system type would use different inputs and produce comparable outputs.

## Reading Guides

The numbers and diagrams below are the Product Owner output. The per-notebook reading guides under [notebooks/](notebooks/) complement them with framing, Scrum-language interpretation, and short reading rules. Each section links to its matching guide.

## Decision Path

Six steps lead to the recommendation. Each row jumps to the matching section below and to the deep-dive reading guide. Every section also carries its own step breadcrumb so you do not need to scroll back here.

| Step | Key question | Section | Reading guide |
|:-:|---|---|---|
| 1 | What value can each feature provide? | [Notebook 02](#notebook-02---business-value) | [02 — Business value](notebooks/02-business-value.md) |
| 2 | Does the investment pay back over time? | [Notebook 03](#notebook-03---financial-return) | [03 — Financial return](notebooks/03-financial-return.md) |
| 3 | Which feature bundle fits the budget best? | [Notebook 04](#notebook-04---portfolio-and-budget) | [04 — Portfolio and budget](notebooks/04-portfolio-and-budget.md) |
| 4 | Which risk layer removes the most value? | [Notebook 05](#notebook-05---risk-resilience) | [05 — Risk resilience](notebooks/05-risk-resilience.md) |
| 5 | Will development stay inside the budget? | [Notebook 06](#notebook-06---development-cost-risk) | [06 — Development cost risk](notebooks/06-development-cost-risk.md) |
| 6 | What is the final roadmap recommendation? | [Notebook 07](#notebook-07---executive-decision) | [07 — Executive decision](notebooks/07-executive-decision.md) |

---

## Notebook 02 - Business Value

> **Step 1 of 6.** Key question: *What value can each feature provide?*
> → Next: [Step 2 — Financial return](#notebook-03---financial-return)

Source notebook: [02-blockchain-case-study.ipynb](../../apps/fhs/notebooks/02-blockchain-case-study.ipynb)
Reading guide: [02-business-value.md](notebooks/02-business-value.md)

Three feature hypotheses (H1 Simplified UI, H2 Traceability, H3 Expiration Alerts) compared on expected business value, business value floor at 95%, and downside tail outcomes.

![Business value distributions](images/02-blockchain-case-study-fig1.png)

Business value distributions for H1, H2, H3 — spread of possible outcomes per feature instead of a single point estimate.

![Portfolio risk profile](images/02-blockchain-case-study-fig2.png)

Combined portfolio distribution with per-feature contributions — how the full roadmap behaves as one option.

---

## Notebook 03 - Financial Return

> **Step 2 of 6.** Key question: *Does the investment pay back over time?*
> ← Previous: [Step 1 — Business value](#notebook-02---business-value) · → Next: [Step 3 — Portfolio and budget](#notebook-04---portfolio-and-budget)

Source notebook: [03-blockchain-case-study-capital-budgeting.ipynb](../../apps/fhs/notebooks/03-blockchain-case-study-capital-budgeting.ipynb)
Reading guide: [03-financial-return.md](notebooks/03-financial-return.md)

Two funding views compared: full investment upfront vs. installments. Outputs per option: Year 1 result, NPV, IRR, profitability.

![NPV comparison at hurdle rate](images/03-capital-budgeting-fig1.png)

NPV gap between upfront and installment financing at the hurdle rate.

![Cash-flow view](images/03-capital-budgeting-fig2.png)

Cash-flow profile of the two financing options.

![Portfolio return comparison](images/03-capital-budgeting-fig3.png)

Portfolio-level return under each financing structure — installment financing improves the result but does not lift H1 above the funding threshold.

---

## Notebook 04 - Portfolio And Budget

> **Step 3 of 6.** Key question: *Which feature bundle fits the budget best?*
> ← Previous: [Step 2 — Financial return](#notebook-03---financial-return) · → Next: [Step 4 — Risk resilience](#notebook-05---risk-resilience)

Source notebook: [04-blockchain-case-study-advisor.ipynb](../../apps/fhs/notebooks/04-blockchain-case-study-advisor.ipynb)
Reading guide: [04-portfolio-and-budget.md](notebooks/04-portfolio-and-budget.md)

Portfolio choice across budget levels and planning horizons — best bundle of work, not best individual feature.

![Budget-level portfolio selection](images/04-advisor-fig1.png)

Selected feature bundle at three budget levels. H2 + H3 is the strongest bundle when the full budget is available; H3 alone is the natural low-budget choice; keeping reserve is sometimes the better roadmap decision.

---

## Notebook 05 - Risk Resilience

> **Step 4 of 6.** Key question: *Which risk layer removes the most value?*
> ← Previous: [Step 3 — Portfolio and budget](#notebook-04---portfolio-and-budget) · → Next: [Step 5 — Development cost risk](#notebook-06---development-cost-risk)

Source notebook: [05-blockchain-case-study-risk.ipynb](../../apps/fhs/notebooks/05-blockchain-case-study-risk.ipynb)
Reading guide: [05-risk-resilience.md](notebooks/05-risk-resilience.md)

Selected portfolio tested against development risk, market risk, component risk, and global shocks.

![Risk resilience matrix](images/05-blockchain-case-study-risk-fig1.png)

Development × market matrix — where the portfolio keeps a profit buffer and where it falls below break-even.

![Risk profile detail](images/05-blockchain-case-study-risk-fig2.png)

Downside structure of the portfolio in detail.

![Risk waterfall and portfolio impact](images/05-blockchain-case-study-risk-fig3.png)

Value loss as risk layers are applied one after another — development risk dominates; market, component, and global risks are smaller.

---

## Notebook 06 - Development Cost Risk

> **Step 5 of 6.** Key question: *Will development stay inside the budget?*
> ← Previous: [Step 4 — Risk resilience](#notebook-05---risk-resilience) · → Next: [Step 6 — Executive decision](#notebook-07---executive-decision)

Source notebook: [06-blockchain-case-study-development-risk.ipynb](../../apps/fhs/notebooks/06-blockchain-case-study-development-risk.ipynb)
Reading guide: [06-development-cost-risk.md](notebooks/06-development-cost-risk.md)

Development uncertainty converted into cost risk. Three numbers per feature:

- **Expected development cost** — average cost across all simulated scenarios.
- **Loss at Risk (LaR 95%)** — cost level exceeded in only 5 out of 100 scenarios.
- **CVaR 95%** — average cost inside the worst 5% of scenarios.

### Development Setup

Simulation reads sprint parameters from the development-risk configuration block in [blockchain.yaml](../../apps/fhs/notebooks/config/blockchain.yaml) — no values are hard-coded:

| Parameter | YAML key | Value | Meaning |
|---|---|---|---|
| Sprint length | `sprint_length_weeks` | 2 weeks | Six sprints fit in one quarter. |
| Quarterly capacity | `quarterly_capacity_sprints` | 6 sprints | Development capacity available per quarter. |
| Sprint uncertainty | `delay_model.sprint_uncertainty` | 30 (approx. +/-30%) | Around 68% of sprints finish within +/-30% of the planned duration. |
| Sprint ceiling | `delay_model.sprint_ceiling` | 2.5 | No scenario assumes worse than 2.5 times the planned duration. |
| Cancellation threshold | `cancellation.max_sprints_over_plan` / `cancellation_probability` | 2 / 0.6 | At more than two sprints over plan, there is a 60% chance the feature is cancelled. Already-spent sprints are sunk cost. |

These values are configurable estimates. A team with recorded velocity data should override `sprint_uncertainty` in `blockchain.yaml` with values from its own history.

### Feature Plan And Development Tail

Derived from [blockchain.yaml](../../apps/fhs/notebooks/config/blockchain.yaml):

| Feature | Planned weeks | Planned sprints | Planned dev cost | Cost per sprint |
|---|---:|---:|---:|---:|
| H1 Simplified UI | 5 | 3 | 75,000 EUR | 30,000 EUR |
| H2 Traceability | 5 | 3 | 55,000 EUR | 22,000 EUR |
| H3 Expiration Alerts | 3 | 2 | 10,509 EUR | 7,006 EUR |

The feature-level tail numbers below are simulation outputs, not plan inputs:

| Feature | P50 actual sprints | P75 actual sprints | P95 actual sprints | Expected development cost | LaR / CaR 95% | CVaR 95% | Feature budget pressure |
|---|---:|---:|---:|---:|---:|---:|---:|
| H1 Simplified UI | 3 | 4 | 5 | 104,286 EUR | 150,000 EUR | 153,302 EUR | +104.4% |
| H2 Traceability | 3 | 4 | 5 | 76,500 EUR | 110,000 EUR | 112,437 EUR | +104.4% |
| H3 Expiration Alerts | 2 | 3 | 4 | 17,608 EUR | 28,024 EUR | 28,272 EUR | +169.0% |

For the selected H2 + H3 portfolio, Notebook 06 uses the CVaR of the **per-scenario summed cost**, not the sum of the two individual CVaRs:

| Selected portfolio | Planned cost | Expected development cost | Portfolio LaR / CaR 95% | Portfolio CVaR 95% | Portfolio budget pressure |
|---|---:|---:|---:|---:|---:|
| H2 Traceability + H3 Expiration Alerts | 65,509 EUR | 94,108 EUR | 131,018 EUR | 136,047 EUR | +107.7% |

With `sprint_ceiling: 2.5`, the ceiling sits well above each feature's cancellation trigger, so the worst 5% of scenarios have real room above the trigger. CaR 95% and CVaR 95% therefore separate — CVaR is the *average* of the worst tail and lands above CaR (the boundary). The funding-gate metric remains **CVaR 95%**, because it answers what the average cost is in the worst 5% of scenarios.

Notebook 06 also shows a cost comparison chart with the same proportions as the table: planned cost, expected cost, CaR 95%, and CVaR 95%. This avoids reading the picture as a simple planned-vs-average comparison and makes the development tail visible.

![Development cost comparison](images/06-development-risk-fig2.png)

Planned cost, expected development cost, CaR 95%, and CVaR 95% per feature. The expected cost bar shows the planning reserve need; the CaR and CVaR bars show how far the development tail reaches.

Two observations before the simulation runs:

- **Portfolio plan is over capacity.** Three features sum to 3 + 3 + 2 = **8 planned sprints**; quarterly capacity is **6 sprints**. Forcing all three into one quarter pushes realised risk above the simulated numbers.
- **H3 has the highest relative pressure.** Cheap in absolute EUR, but the simulation shows +169 % budget pressure — the worst tail is far above its planned cost, because one extra sprint nearly doubles the bill. Its cancellation rule does fire (trigger 4 sprints, reachable under the 2.5× ceiling), but rarely — H3's P95 sits at exactly 4 sprints.

![Sprint overrun distribution](images/06-development-risk-fig1.png)

Actual sprint demand vs. planned sprint count per feature. The further the distribution leans right of the plan, the higher the cost tail. H3's distribution is the most asymmetric in relative terms — short median, long right tail.

---

## Notebook 07 - Executive Decision

> **Step 6 of 6 — final step.** Key question: *What is the final roadmap recommendation?*
> ← Previous: [Step 5 — Development cost risk](#notebook-06---development-cost-risk) · This step closes the decision chain.

Source notebook: [07-blockchain-case-study-decision.ipynb](../../apps/fhs/notebooks/07-blockchain-case-study-decision.ipynb)
Reading guide: [07-executive-decision.md](notebooks/07-executive-decision.md)

### Recommendation

Recommended combination: **2 of 3 features — H2 Traceability + H3 Expiration Alerts**. H1 Simplified UI is not part of the funded bundle.

- **Fund H2 Traceability** — value anchor.
- **Test H3 Expiration Alerts** — behind a tight development gate.
- **Defer H1 Simplified UI** — until the business value case improves.
- **Keep EUR 89,491 as reserve** — do not spend the full budget.

Headline verdict: **CONDITIONAL GO** — proceed with H2 + H3 with active development-risk control.

### Decision Dimensions

| Decision dimension | Essential question | Main message | Source |
|---|---|---|---|
| Business Value | Which hypothesis creates the strongest value? | H2 is the value anchor; H3 is useful; H1 is too weak for its cost. | Notebook 02 |
| Financial Return | Does the investment still work after funding logic? | Installment funding improves the case, but H1 still misses the threshold. | Notebook 03 |
| Portfolio And Budget | Which bundle should be funded? | H2 + H3 is the best use of budget; keeping reserve is better than spending everything. | Notebook 04 |
| Risk Resilience | What can break the case? | Development risk dominates the downside story. | Notebook 05 |
| Development Cost Risk | Can the team stay within budget if sprints overrun? | H2 needs release-window control; H3 needs an early scope gate because its relative budget pressure is highest (+169 %) — one extra sprint nearly doubles its planned cost. | Notebook 06 |

### Decision Signal Rule

Each dimension emits one traffic-light signal — **GO**, **CONDITIONAL GO**, or **REVIEW**. The overall verdict follows one rule:

| Overall verdict | Rule |
|---|---|
| **GO** | All five dimensions are GO. |
| **REVIEW** | Two or more dimensions are REVIEW. |
| **CONDITIONAL GO** | Every other combination. |


### Robustness Check

| Scenario | Development factor | Market shock probability | What it tests |
|---|---:|---:|---|
| Optimistic | 0.5x | 10% | How much value better development confidence would unlock. |
| Base case | 1.0x | 20% | The current planning assumption and headline verdict. |
| Stressed | 1.5x | 30% | Whether the portfolio still works when development gets harder. |

### Action Playbook

| Verdict | Product Owner action |
|---|---|
| **GO** | Confirm the funding structure, set development milestones, and rerun the analysis quarterly. |
| **CONDITIONAL GO** | Fund only the data-backed bundle, work the conditional dimensions first, and keep reserve until the next gate. |
| **REVIEW** | Do not proceed before mitigation; fix the highest-impact red dimension and rerun the scenario configuration. |

For this case study, the practical action is **CONDITIONAL GO**: fund H2, test H3 behind an early scope gate, defer H1, keep EUR 89,491 as reserve, and make development confidence the next management focus.

---

## Decision Canvas

![Product Owner decision canvas](images/product-owner-decision-canvas.svg)

The canvas connects customer value, investment return, budget fit, risk resilience, and development confidence. It is useful for workshop discussions with Product Owners, Scrum teams, finance partners, and risk stakeholders.

The editable draw.io source lives in the repository at [product-owner-decision-canvas.drawio](product-owner-decision-canvas.drawio). To edit, download the file and open it in draw.io desktop or upload it to app.diagrams.net via *File → Open from → Device*. The SVG above has the diagram XML embedded, so opening the SVG itself in draw.io produces the same round-trip.

## Product Owner Takeaway

This case study is a decision basis, not a replacement for the Product Owner's decision. It strengthens every backlog choice with clearer analysis, anchored on four questions:

- Value first: which feature creates the strongest business value?
- Floor second: how much value remains in weaker scenarios?
- Budget third: which bundle gives the best use of capital?
- Development last, but not least: can the team build while staying inside the agreed risk appetite?

That decision basis supports the recommended roadmap: **fund H2, test H3 behind an early scope gate, defer H1, and keep EUR 89,491 as reserve until the next decision gate is passed.**
